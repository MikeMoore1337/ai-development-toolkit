#!/usr/bin/env python3
"""Validate offline declared cross-project A/B orchestration evidence; no agent calls."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_CASES = {
    "YFC": "MikeMoore1337/your-fitness-coach",
    "Hermes": "MikeMoore1337/hermes",
    "SecondBrain": "MikeMoore1337/second-brain",
}
HEX40 = re.compile(r"[a-f0-9]{40}\Z")
ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
RUN_FIELDS = {"status", "revision", "acceptance_ids", "client", "model",
              "invocation_id", "worker_traces", "evidence", "elapsed_seconds",
              "tokens_used"}
POLICY_FIELDS = {"paid_api_allowed", "owner_runtime_approved",
                 "verified_zero_incremental_cost", "verified_isolation",
                 "approval_reference", "cost_reference", "isolation_reference"}


def validate(value: Any) -> list[str]:
    """Fail closed on malformed/unhashable input; assertions are not authenticated."""
    try:
        return sorted(set(_validate(value)))
    except (TypeError, ValueError, KeyError, AttributeError, OverflowError):
        return ["MALFORMED_INPUT"]


def _validate(doc: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(doc, dict) or set(doc) != {
        "schema_version", "purpose", "policy", "cases", "conclusion"
    }:
        return ["SCHEMA"]
    if doc["schema_version"] != 1 or doc["purpose"] != "REAL_CLIENT_AB_PILOT":
        errors.append("SCHEMA")
    policy = doc["policy"]
    if not isinstance(policy, dict) or set(policy) != POLICY_FIELDS:
        return errors + ["POLICY_FIELDS"]
    for field in ("paid_api_allowed", "owner_runtime_approved",
                  "verified_zero_incremental_cost", "verified_isolation"):
        if type(policy[field]) is not bool:
            errors.append("POLICY_FIELDS")
    if policy["paid_api_allowed"] is not False:
        errors.append("NO_PAID_API")
    approvals = (
        policy["owner_runtime_approved"],
        policy["verified_zero_incremental_cost"],
        policy["verified_isolation"],
    )
    for flag, ref in zip(approvals, (
        policy["approval_reference"], policy["cost_reference"],
        policy["isolation_reference"],
    )):
        if flag and (not isinstance(ref, str) or not ref.strip()):
            errors.append("UNSUPPORTED_GATE")
        if not flag and ref is not None:
            errors.append("UNSUPPORTED_GATE")
    cases = doc["cases"]
    if not isinstance(cases, list) or len(cases) != len(REPO_CASES):
        return errors + ["CASE_REGISTRY"]
    seen: set[str] = set()
    every_pair_observed = True
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "id", "repository", "revision", "scope", "acceptance_ids",
            "baseline", "orchestra"
        }:
            errors.append("CASE_FIELDS")
            every_pair_observed = False
            continue
        cid = case["id"]
        if not isinstance(cid, str) or cid not in REPO_CASES or cid in seen:
            errors.append("CASE_REGISTRY")
        else:
            seen.add(cid)
        if case["repository"] != REPO_CASES.get(cid):
            errors.append("REPO_MISMATCH")
        revision = case["revision"]
        if not isinstance(revision, str) or not HEX40.fullmatch(revision):
            errors.append("REVISION")
        if not isinstance(case["scope"], str) or not case["scope"].strip():
            errors.append("SCOPE")
        acs = case["acceptance_ids"]
        if not isinstance(acs, list) or not acs or any(
            not isinstance(a, str) or not ID.fullmatch(a) for a in acs
        ) or len(set(acs)) != len(acs):
            errors.append("ACCEPTANCE")
        pair_status = []
        for arm in ("baseline", "orchestra"):
            run = case[arm]
            if not isinstance(run, dict) or set(run) != RUN_FIELDS:
                errors.append("RUN_FIELDS")
                pair_status.append("INVALID")
                continue
            status = run["status"]
            pair_status.append(status)
            if status not in {"NOT_RUN", "OBSERVED"}:
                errors.append("RUN_STATUS")
            if run["revision"] != revision or run["acceptance_ids"] != acs:
                errors.append("UNEQUAL_INPUTS")
            if status == "NOT_RUN":
                if (run["client"] is not None or run["model"] is not None
                    or run["invocation_id"] is not None or run["worker_traces"]
                    or run["evidence"] or run["elapsed_seconds"] is not None
                    or run["tokens_used"] is not None):
                    errors.append("FAKE_OBSERVATION")
                continue
            if status != "OBSERVED":
                continue
            if not all(approvals) or policy["paid_api_allowed"]:
                errors.append("LIVE_GATE")
            if not isinstance(run["client"], str) or not run["client"].strip() or (
                not isinstance(run["model"], str) or not run["model"].strip()
            ):
                errors.append("CLIENT_MISSING")
            if not isinstance(run["invocation_id"], str) or not run["invocation_id"].strip():
                errors.append("INVOCATION_MISSING")
            trace = run["worker_traces"]
            target = 1 if arm == "baseline" else None
            if (not isinstance(trace, list) or any(
                not isinstance(t, str) or not t.strip() for t in trace
            ) or len(set(trace)) != len(trace)
                or (target is not None and len(trace) != 1)
                or (target is None and not 2 <= len(trace) <= 3)):
                errors.append("REAL_WORKERS_UNVERIFIED")
            proof = run["evidence"]
            if not isinstance(proof, list) or not proof or any(
                not isinstance(p, str) or not p.strip() for p in proof
            ):
                errors.append("EXECUTION_EVIDENCE")
            elapsed = run["elapsed_seconds"]
            if type(elapsed) not in (int, float) or not (0 < elapsed < 86400):
                errors.append("INVALID_TIME")
            tokens = run["tokens_used"]
            if tokens is not None and (type(tokens) is not int or tokens < 0):
                errors.append("INVALID_TOKENS")
        if pair_status != ["OBSERVED", "OBSERVED"]:
            every_pair_observed = False
        else:
            b, o = case["baseline"], case["orchestra"]
            if b["client"] != o["client"] or b["model"] != o["model"]:
                errors.append("MODEL_CONFOUND")
            if b["invocation_id"] == o["invocation_id"]:
                errors.append("SAME_INVOCATION")
    if seen != set(REPO_CASES):
        errors.append("CASE_REGISTRY")
    if doc["conclusion"] not in {"NOT_MEASURED", "PENDING_INDEPENDENT_REVIEW"}:
        errors.append("CONCLUSION")
    if not every_pair_observed and doc["conclusion"] != "NOT_MEASURED":
        errors.append("PREMATURE_COMPARISON")
    if every_pair_observed and doc["conclusion"] != "PENDING_INDEPENDENT_REVIEW":
        errors.append("REVIEW_REQUIRED")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(json.loads(args.path.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"INVALID_INPUT: {type(exc).__name__}: {exc}")
        return 2
    for error in errors:
        print(f"FAIL: {error}")
    if errors:
        return 1
    print("PASS: self-consistent declaration only; no real Codex/Claude evidence verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
