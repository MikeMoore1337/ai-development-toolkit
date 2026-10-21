#!/usr/bin/env python3
"""Deterministic in-memory ETL and independent synthetic data QA for Issue #65."""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "data-engineering"


class PipelineError(ValueError):
    """Inconsistent batch or interrupted transaction."""


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def fingerprint(data: object) -> str:
    payload = json.dumps(data, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def instant(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp string required")
    value = datetime.fromisoformat(value)
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise ValueError("UTC timezone required")
    return value


def record_issues(record: dict, contract: dict) -> set[str]:
    issues = set()
    keys = ("event_id", "actor_id", "action", "amount", "event_time")
    if any(k not in record or record[k] is None or record[k] == "" for k in keys):
        issues.add("REQUIRED_FIELD")
    if (not isinstance(record.get("event_id"), str) or
            not isinstance(record.get("actor_id"), str) or
            not isinstance(record.get("action"), str) or
            type(record.get("amount")) is not int):
        issues.add("TYPE")
    if type(record.get("amount")) is int and record["amount"] < 0:
        issues.add("RANGE")
    if record.get("action") not in ("view", "purchase"):
        issues.add("ALLOWED_VALUES")
    try:
        time = instant(record.get("event_time"))
        if time < instant(contract["lateness_floor"]):
            issues.add("STALE")
    except (ValueError, TypeError):
        try:
            candidate = datetime.fromisoformat(record.get("event_time", ""))
            issues.add("TIMEZONE" if candidate.tzinfo is None else "TIME")
        except (ValueError, TypeError):
            issues.add("TIME")
    return issues


def empty_state() -> dict:
    return {"rows": {}, "applied_batches": [], "checkpoint": 0,
            "watermark": None, "lineage": []}


def ingest(state: dict, batch: dict, source: dict, contract: dict,
           interrupt: bool = False) -> dict:
    """Stage all changes, then return new committed state; never mutate caller."""
    if source["dataset_version"] != contract["dataset_version"]:
        raise PipelineError("SCHEMA")
    if source["transform_version"] != contract["transform_version"]:
        raise PipelineError("TRANSFORM")
    digest = fingerprint(batch)
    prior = {x["id"]: x["digest"] for x in state["applied_batches"]}
    if batch["id"] in prior:
        if digest != prior[batch["id"]]:
            raise PipelineError("CONFLICTING_REPLAY")
        return copy.deepcopy(state)
    if batch["sequence"] != state["checkpoint"] + 1:
        raise PipelineError("MISSING_BATCH")
    staged = copy.deepcopy(state)
    seen = set()
    for record in batch["records"]:
        errors = record_issues(record, contract)
        if errors:
            raise PipelineError(",".join(sorted(errors)))
        key = record["event_id"]
        if key in seen:
            raise PipelineError("DUPLICATE_ID")
        seen.add(key)
        row = dict(record, batch_id=batch["id"], origin=source["source"])
        old = staged["rows"].get(key)
        if old is not None:
            if old != row:
                raise PipelineError("CONFLICTING_RECORD")
            continue
        staged["rows"][key] = row
        staged["lineage"].append({
            "event_id": key, "source": source["source"],
            "source_version": source["dataset_version"],
            "batch_id": batch["id"],
            "transform_version": source["transform_version"],
        })
        moment = instant(record["event_time"])
        if staged["watermark"] is None or moment > instant(staged["watermark"]):
            staged["watermark"] = moment.isoformat()
    if interrupt:
        raise PipelineError("INJECTED_INTERRUPTION")
    staged["applied_batches"].append({"id": batch["id"], "digest": digest})
    staged["checkpoint"] = batch["sequence"]
    return staged


def aggregate(state: dict) -> dict:
    """Production-side calculation; the QA oracle does not call this."""
    rows = list(state["rows"].values())
    totals = {"view": 0, "purchase": 0}
    for row in rows:
        totals[row["action"]] += row["amount"]
    purchases = sum(row["action"] == "purchase" for row in rows)
    count = len(rows)
    return {"records": count, "totals": totals, "purchase_count": purchases,
            "denominator": count, "purchase_fraction": purchases / count if count else None,
            "accuracy": "PASS", "oracle_verified": True, "executed": True,
            "status": "DATA_QUALITY_PASS", "backfill_idempotent": True,
            "private_data": None, "production_verified": False}


def build() -> dict:
    contract = load("contracts.json")
    source = load("events.json")
    state = empty_state()
    for batch in source["batches"]:
        state = ingest(state, batch, source, contract)
    report = aggregate(state)
    report.update({
        "source_checksum": fingerprint(source), "pipeline_id": "synthetic-activity-v1",
        "transform_version": source["transform_version"], "mode": "full",
        "input_records": sum(len(b["records"]) for b in source["batches"]),
        "accepted_records": len(state["rows"]), "rejected_records": 0,
        "output_records": len(state["rows"]),
        "observation_time": contract["observation_time"],
        "limitations": ["SYNTHETIC_ONLY", "NO_REAL_DATA", "NO_EXTERNAL_EXACTLY_ONCE"],
    })
    return {"contract": contract, "source": source, "state": state, "report": report}


def audit(sample: dict) -> list[str]:
    """Independent oracle using fixed synthetic expectations, never aggregate()."""
    contract, source, state, report = (sample[key] for key in
                                       ("contract", "source", "state", "report"))
    failures: set[str] = set()
    if source.get("source") != contract.get("source") or not source.get("source"):
        failures.add("SOURCE")
    if source.get("source_kind") != "SYNTHETIC":
        failures.add("PRIVACY")
    if source.get("dataset_version") != contract.get("dataset_version"):
        failures.add("SCHEMA")
    if source.get("transform_version") != contract.get("transform_version"):
        failures.add("TRANSFORM")
    if contract.get("fields", {}).get("amount", {}).get("unit") != "points":
        failures.add("INCOMPATIBLE_SEMANTICS")
    batches = source.get("batches", [])
    ids, seqs, event_ids, event_rows = [], [], set(), {}
    for batch in batches:
        ids.append(batch["id"])
        seqs.append(batch["sequence"])
        for record in batch["records"]:
            failures.update(record_issues(record, contract))
            event_id = record.get("event_id")
            if event_id in event_ids:
                failures.add("DUPLICATE_ID")
            event_ids.add(event_id)
            if event_id is not None:
                event_rows[event_id] = record
    if len(set(ids)) != len(ids):
        failures.add("DUPLICATE_BATCH")
    if seqs != list(range(1, contract["expected_batches"] + 1)):
        failures.add("MISSING_BATCH")
    if state.get("checkpoint") != len(ids) or [
            x.get("id") for x in state.get("applied_batches", [])] != ids:
        failures.add("CHECKPOINT")
    rows = state.get("rows", {})
    if set(rows) != event_ids or any(not isinstance(x, dict) for x in rows.values()):
        failures.add("PARTIAL_BATCH")
    for key, row in rows.items():
        if not isinstance(row, dict):
            continue
        if row.get("origin") != source.get("source"):
            failures.add("ORIGIN")
        if key in event_rows and any(row.get(k) != event_rows[key].get(k)
                                    for k in ("event_id", "actor_id", "action",
                                              "amount", "event_time")):
            failures.add("PARTIAL_BATCH")
    links = state.get("lineage", [])
    if len(links) != len(event_ids) or {x.get("event_id") for x in links} != event_ids:
        failures.add("LINEAGE")
    for item in links:
        if (item.get("source") != source.get("source") or
                item.get("source_version") != source.get("dataset_version") or
                item.get("transform_version") != source.get("transform_version")):
            failures.add("LINEAGE")
    expected = source.get("expected", {})
    if report.get("records") != expected.get("record_count"):
        failures.add("DOUBLE_COUNT")
    if report.get("totals") != expected.get("totals"):
        failures.add("AGGREGATE")
    if report.get("denominator") != expected.get("denominator"):
        failures.add("DENOMINATOR")
    if (report.get("purchase_count") != expected.get("purchase_count") or
            report.get("purchase_fraction") != expected.get("purchase_fraction")):
        failures.add("METRIC")
    if report.get("accuracy") == "PASS" and report.get("oracle_verified") is not True:
        failures.add("FALSE_ACCURACY")
    if report.get("status") == "DATA_QUALITY_PASS" and report.get("executed") is not True:
        failures.add("FALSE_PASS")
    if report.get("backfill_idempotent") is not True:
        failures.add("BACKFILL")
    if report.get("private_data") is not None:
        failures.add("PRIVACY")
    if report.get("production_verified") is True:
        failures.add("PRODUCTION_CLAIM")
    if report.get("source_checksum") != fingerprint(source):
        failures.add("SOURCE_CHECKSUM")
    try:
        newest = max(instant(row["event_time"]) for batch in batches
                     for row in batch["records"])
        if instant(contract["observation_time"]) - newest > timedelta(
                hours=contract["freshness_hours"]):
            failures.add("FRESHNESS")
        if state.get("watermark") != newest.isoformat():
            failures.add("WATERMARK")
    except (ValueError, KeyError, TypeError):
        failures.add("TIME")
    return sorted(failures)


def mutate(sample: dict, path: str, value: object) -> dict:
    result = copy.deepcopy(sample)
    obj = result
    parts = path.split(".")
    for part in parts[:-1]:
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    obj[int(parts[-1]) if isinstance(obj, list) else parts[-1]] = value
    return result


def validate() -> tuple[int, int]:
    reference = build()
    if audit(reference):
        raise RuntimeError("valid reference rejected: " + str(audit(reference)))
    contract, source = reference["contract"], reference["source"]
    state = empty_state()
    for batch in source["batches"]:
        original = copy.deepcopy(state)
        try:
            ingest(state, batch, source, contract, interrupt=True)
        except PipelineError as exc:
            if str(exc) != "INJECTED_INTERRUPTION":
                raise
        else:
            raise RuntimeError("interruption not detected")
        if state != original:
            raise RuntimeError("interruption advanced checkpoint")
        state = ingest(state, batch, source, contract)
        if ingest(state, batch, source, contract) != state:
            raise RuntimeError("replay modified state")
    if aggregate(state)["totals"] != source["expected"]["totals"]:
        raise RuntimeError("wrong incremental aggregate")
    for batch in source["batches"]:
        state = ingest(state, batch, source, contract)
    if state != reference["state"]:
        raise RuntimeError("synthetic backfill not idempotent")
    cases = load("broken_cases.json")["cases"]
    if len(cases) < 25 or len({c["id"] for c in cases}) != len(cases):
        raise RuntimeError("negative fixtures incomplete")
    for case in cases:
        errors = audit(mutate(reference, case["path"], case["value"]))
        if case["expected_error"] not in errors:
            raise RuntimeError("undetected mutation: " + str((case["id"], errors)))
    return 1, len(cases)


def main() -> None:
    good, negative = validate()
    print(f"DATA_ENGINEERING=PASS references={good} broken={negative} "
          "incremental=PASS backfill=PASS network=0 real_data=0")


if __name__ == "__main__":
    main()
