#!/usr/bin/env python3
"""Offline checks for a declared feature-orchestration run. Not proof of live agents."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
WORKER_MODES = {"SEQUENTIAL", "ACTUAL_SUBAGENT", "GENERIC_SUBAGENT"}
CHECK_STATES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "UNKNOWN"}
HIGH_RISK = {"privacy", "security", "irreversible", "migration", "billing", "legal"}
GATED = {"visual", "privacy", "security", "irreversible", "billing", "legal", "release"}
ACTUAL_EVIDENCE = {"TEST_RUN", "CI_RUN", "INTEGRATION_RUN"}


def validate(data: Any) -> list[str]:
    """Reject malformed nested JSON safely instead of throwing a traceback."""
    try:
        return _validate(data)
    except (TypeError, KeyError, ValueError, AttributeError):
        return ["INVALID_INPUT_SHAPE"]


def _validate(data: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["EXPECTED_OBJECT"]
    required = {"schema_version", "task_id", "revision", "controller", "active_controllers",
                "depth", "risk_flags", "execution", "units", "acceptance",
                "evidence", "checks", "approvals", "outcome"}
    if set(data) != required:
        return ["SCHEMA_FIELDS"]
    if data["schema_version"] != 1 or not isinstance(data["task_id"], str) or not data["task_id"].strip():
        errors.append("SCHEMA_ID")
    revision = data["revision"]
    if not isinstance(revision, str) or not SHA.fullmatch(revision):
        errors.append("REVISION")
    controller = data["controller"]
    if controller not in {"feature-delivery", "make-feature"} or data["active_controllers"] != [controller]:
        errors.append("DUPLICATE_CONTROLLER")
    if data["depth"] not in {"quick", "normal", "deep"}:
        errors.append("DEPTH")
    risks = data["risk_flags"]
    if not isinstance(risks, list) or any(x not in (HIGH_RISK | GATED) for x in risks) or len(set(risks)) != len(risks):
        errors.append("RISK_FLAGS")
        risks = []
    if HIGH_RISK.intersection(risks) and data["depth"] != "deep":
        errors.append("RISK_DOWNGRADE")
    execution = data["execution"]
    if not isinstance(execution, dict) or set(execution) != {"mode", "peak"}:
        return errors + ["EXECUTION"]
    mode, peak = execution["mode"], execution["peak"]
    if mode not in {"SEQUENTIAL", "SUBAGENTS"} or type(peak) is not int or not (1 <= peak <= 3):
        errors.append("EXECUTION")
    if mode == "SEQUENTIAL" and peak != 1:
        errors.append("FAKE_PARALLELISM")
    units = data["units"]
    if not isinstance(units, list) or not (1 <= len(units) <= 12):
        return errors + ["UNITS_COUNT"]
    identities: dict[str, dict] = {}
    actual = 0
    writers = 0
    for item in units:
        if not isinstance(item, dict) or set(item) != {"id", "purpose", "role", "status",
                                                        "execution", "trace", "write_paths", "depends_on"}:
            errors.append("UNIT_FIELDS")
            continue
        uid = item["id"]
        if not isinstance(uid, str) or not ID.fullmatch(uid) or uid in identities:
            errors.append("UNIT_ID")
            continue
        identities[uid] = item
        if not isinstance(item["purpose"], str) or not item["purpose"].strip():
            errors.append("UNIT_PURPOSE")
        if not isinstance(item["role"], str) or not item["role"].strip():
            errors.append("UNIT_ROLE")
        if item["status"] not in {"PLANNED", "EXECUTED"}:
            errors.append("UNIT_STATUS")
        if item["execution"] not in WORKER_MODES:
            errors.append("UNIT_EXECUTION")
        if item["execution"] == "SEQUENTIAL":
            if item["trace"] is not None:
                errors.append("FAKE_SUBAGENT")
        else:
            if mode == "SEQUENTIAL" or item["status"] != "EXECUTED":
                errors.append("FAKE_SUBAGENT")
            if not isinstance(item["trace"], str) or not item["trace"].strip():
                errors.append("MISSING_TRACE")
            actual += 1
        paths = item["write_paths"]
        if not isinstance(paths, list) or len(set(paths)) != len(paths) or any(
            not isinstance(p, str) or not p or p.startswith("/") or
            "\\" in p or ".." in p.split("/") or "." in p.split("/") for p in paths
        ):
            errors.append("WRITE_SCOPE")
        elif paths:
            writers += 1
            if item["role"] != "implementer":
                errors.append("WRITE_OWNER")
            if item["execution"] != "SEQUENTIAL":
                errors.append("SUBAGENT_WRITE")
        if not isinstance(item["depends_on"], list) or len(set(item["depends_on"])) != len(item["depends_on"]):
            errors.append("DEPENDENCIES")
    if writers > 1:
        errors.append("CONCURRENT_WRITERS")
    if mode == "SUBAGENTS" and (actual < 1 or peak > actual):
        errors.append("FAKE_PARALLELISM")
    graph = {}
    for uid, unit in identities.items():
        dependencies = unit["depends_on"]
        if not isinstance(dependencies, list):
            continue
        graph[uid] = dependencies
        for dep in dependencies:
            if dep == uid or dep not in identities:
                errors.append("INVALID_DEPENDENCY")
            elif unit["status"] == "EXECUTED" and identities[dep]["status"] != "EXECUTED":
                errors.append("DEPENDENCY_NOT_COMPLETE")
    temporary: set[str] = set()
    visited: set[str] = set()

    def visit(node: str) -> None:
        if node in temporary:
            errors.append("DEPENDENCY_CYCLE")
            return
        if node in visited:
            return
        temporary.add(node)
        for dep in graph.get(node, []):
            if dep in graph:
                visit(dep)
        temporary.remove(node)
        visited.add(node)

    for uid in graph:
        visit(uid)
    approvals = data["approvals"]
    if not isinstance(approvals, list):
        return errors + ["APPROVALS"]
    gate_status: dict[str, str] = {}
    for approval in approvals:
        if not isinstance(approval, dict) or set(approval) != {"gate", "status", "reference"}:
            errors.append("APPROVAL_FIELDS")
            continue
        gate = approval["gate"]
        if gate not in GATED or gate in gate_status:
            errors.append("APPROVAL_ID")
            continue
        gate_status[gate] = approval["status"]
        if approval["status"] not in {"PENDING", "ACCEPTED", "REJECTED"}:
            errors.append("APPROVAL_STATUS")
        if approval["status"] == "ACCEPTED" and (
            not isinstance(approval["reference"], str) or not approval["reference"].strip()
        ):
            errors.append("UNVERIFIED_APPROVAL")
        if approval["status"] != "ACCEPTED" and approval["reference"] is not None:
            errors.append("APPROVAL_REFERENCE")
    for risk in risks:
        if risk in GATED and risk not in gate_status:
            errors.append("MISSING_GATE")
    acceptance = data["acceptance"]
    if not isinstance(acceptance, list) or not acceptance:
        return errors + ["ACCEPTANCE"]
    acs: dict[str, dict] = {}
    for ac in acceptance:
        if not isinstance(ac, dict) or set(ac) != {"id", "requirement", "check_ids"}:
            errors.append("ACCEPTANCE_FIELDS")
            continue
        aid = ac["id"]
        if not isinstance(aid, str) or not ID.fullmatch(aid) or aid in acs:
            errors.append("ACCEPTANCE_ID")
            continue
        acs[aid] = ac
        if not isinstance(ac["requirement"], str) or not ac["requirement"].strip():
            errors.append("ACCEPTANCE_REQUIREMENT")
        if not isinstance(ac["check_ids"], list) or not ac["check_ids"] or len(set(ac["check_ids"])) != len(ac["check_ids"]):
            errors.append("ACCEPTANCE_CHECKS")
    evidence = data["evidence"]
    if not isinstance(evidence, list):
        return errors + ["EVIDENCE"]
    recorded: dict[str, dict] = {}
    for row in evidence:
        if not isinstance(row, dict) or set(row) != {"id", "kind", "revision", "reference"}:
            errors.append("EVIDENCE_FIELDS")
            continue
        eid = row["id"]
        if not isinstance(eid, str) or not ID.fullmatch(eid) or eid in recorded:
            errors.append("EVIDENCE_ID")
            continue
        recorded[eid] = row
        if row["kind"] not in ACTUAL_EVIDENCE | {"CODE_INSPECTION", "SYNTHETIC"}:
            errors.append("EVIDENCE_KIND")
        if row["revision"] != revision:
            errors.append("STALE_EVIDENCE")
        if not isinstance(row["reference"], str) or not row["reference"].strip():
            errors.append("EVIDENCE_REFERENCE")
    checks = data["checks"]
    if not isinstance(checks, list) or not checks:
        return errors + ["CHECKS"]
    by_id: dict[str, dict] = {}
    for check in checks:
        if not isinstance(check, dict) or set(check) != {"id", "status", "evidence_ids"}:
            errors.append("CHECK_FIELDS")
            continue
        cid = check["id"]
        if not isinstance(cid, str) or not ID.fullmatch(cid) or cid in by_id:
            errors.append("CHECK_ID")
            continue
        by_id[cid] = check
        if check["status"] not in CHECK_STATES:
            errors.append("CHECK_STATUS")
        links = check["evidence_ids"]
        if not isinstance(links, list) or any(k not in recorded for k in links):
            errors.append("EVIDENCE_LOOKUP")
            continue
        if check["status"] in {"PASS", "FAIL"} and not any(
            recorded[k]["kind"] in ACTUAL_EVIDENCE for k in links
        ):
            errors.append("FALSE_EXECUTION")
    for ac in acs.values():
        for cid in ac["check_ids"]:
            if cid not in by_id:
                errors.append("MISSING_AC_CHECK")
    if data["outcome"] not in {"PLAN_ONLY", "BLOCKED", "READY_FOR_REVIEW"}:
        errors.append("OUTCOME")
    if data["outcome"] == "READY_FOR_REVIEW" and (
        errors or any(u["status"] != "EXECUTED" for u in identities.values())
        or any(c["status"] != "PASS" for c in by_id.values())
        or not acs or any(x != "ACCEPTED" for x in gate_status.values())
    ):
        errors.append("PREMATURE_READY")
    if data["outcome"] == "PLAN_ONLY" and any(
        c["status"] == "PASS" for c in by_id.values()
    ):
        errors.append("PLAN_CANNOT_PASS")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        issues = validate(json.loads(args.report.read_text(encoding="utf-8")))
    except (OSError, ValueError, UnicodeError) as exc:
        print(f"INVALID_INPUT: {exc}")
        return 2
    for issue in issues:
        print(f"FAIL: {issue}")
    if issues:
        return 1
    print("PASS: internal declarations consistent; actual tool runs and authority NOT authenticated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
