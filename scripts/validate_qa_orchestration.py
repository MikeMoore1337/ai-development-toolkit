#!/usr/bin/env python3
"""Validate *declared* QA orchestration evidence. No agent invocation or external I/O."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

STATES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "UNKNOWN"}
REAL_EVIDENCE = {"TEST_RUN", "CI_RUN", "BROWSER_RUN"}
EVIDENCE_KINDS = REAL_EVIDENCE | {"CODE_INSPECTION", "SYNTHETIC"}
WORKER_MODES = {"SEQUENTIAL", "ACTUAL_SUBAGENT", "GENERIC_SUBAGENT"}
HEX_SHA = re.compile(r"[0-9a-f]{40}\\Z")
ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\\Z")


def validate_report(report: Any) -> list[str]:
    """Fail closed on false-green claims; no external evidence is authenticated."""
    problems: list[str] = []
    if not isinstance(report, dict):
        return ["report must be an object"]
    required = {"schema_version", "repository", "revision", "mode",
                "execution", "streams", "evidence", "checks", "required_check_ids",
                "gate", "changed_code"}
    if set(report) != required:
        return ["invalid report fields"]
    if report["schema_version"] != 1 or report["mode"] != "AUDIT_ONLY":
        problems.append("unsupported version or audit mode")
    if report["changed_code"] is not False:
        problems.append("audit must not claim or perform code changes")
    if not isinstance(report["repository"], str) or not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", report["repository"]
    ):
        problems.append("invalid repository")
    revision = report["revision"]
    if not isinstance(revision, str) or (revision != "UNKNOWN" and not HEX_SHA.fullmatch(revision)):
        problems.append("invalid revision")
    execution = report["execution"]
    if not isinstance(execution, dict) or set(execution) != {"mode", "peak"}:
        return problems + ["invalid execution contract"]
    if execution["mode"] not in {"SEQUENTIAL", "SUBAGENTS"} or (
        type(execution["peak"]) is not int or not 1 <= execution["peak"] <= 3
    ):
        problems.append("invalid execution mode or parallel peak")
    streams = report["streams"]
    if not isinstance(streams, list) or not 1 <= len(streams) <= 3:
        return problems + ["stream count must be 1..3"]
    stream_ids: set[str] = set()
    actual_workers = 0
    for stream in streams:
        if not isinstance(stream, dict) or set(stream) != {"id", "focus", "execution", "trace", "skill"}:
            problems.append("invalid stream")
            continue
        sid = stream["id"]
        if not isinstance(sid, str) or not ID.fullmatch(sid) or sid in stream_ids:
            problems.append("duplicate or invalid stream id")
        else:
            stream_ids.add(sid)
        if not isinstance(stream["focus"], str) or not stream["focus"].strip():
            problems.append("missing stream focus")
        if not isinstance(stream["skill"], str) or not stream["skill"].strip():
            problems.append("missing skill source")
        worker_mode = stream["execution"]
        trace = stream["trace"]
        if worker_mode not in WORKER_MODES:
            problems.append("unsupported worker mode")
        elif worker_mode == "SEQUENTIAL":
            if trace is not None:
                problems.append("sequential worker cannot claim an invocation trace")
        else:
            actual_workers += 1
            if not isinstance(trace, str) or not trace.strip():
                problems.append("subagent missing actual trace")
        if execution["mode"] == "SEQUENTIAL" and worker_mode != "SEQUENTIAL":
            problems.append("sequential plan cannot claim subagents")
        if execution["mode"] == "SUBAGENTS" and worker_mode == "SEQUENTIAL":
            problems.append("subagent plan cannot invent mixed invocation")
    if execution["mode"] == "SEQUENTIAL" and execution["peak"] != 1:
        problems.append("sequential plan must have peak 1")
    if execution["mode"] == "SUBAGENTS" and actual_workers == 0:
        problems.append("subagent plan has no actual workers")
    if execution["mode"] == "SUBAGENTS" and execution["peak"] > actual_workers:
        problems.append("parallel peak exceeds recorded workers")
    evidence = report["evidence"]
    if not isinstance(evidence, list):
        return problems + ["evidence must be an array"]
    evidence_by_id: dict[str, dict] = {}
    for item in evidence:
        if not isinstance(item, dict) or set(item) != {"id", "kind", "reference", "revision"}:
            problems.append("invalid evidence entry")
            continue
        key = item["id"]
        if not isinstance(key, str) or not ID.fullmatch(key) or key in evidence_by_id:
            problems.append("duplicate or invalid evidence id")
            continue
        if item["kind"] not in EVIDENCE_KINDS:
            problems.append("unknown evidence kind")
        if not isinstance(item["reference"], str) or not item["reference"].strip():
            problems.append("missing evidence reference")
        if item["revision"] != revision or revision == "UNKNOWN":
            problems.append("evidence revision missing or mismatched")
        evidence_by_id[key] = item
    checks = report["checks"]
    if not isinstance(checks, list) or not checks:
        return problems + ["checks must be a nonempty array"]
    check_by_id: dict[str, dict] = {}
    all_pass = True
    for check in checks:
        if not isinstance(check, dict) or set(check) != {
            "id", "stream_id", "oracle", "status", "evidence_ids"
        }:
            problems.append("invalid check")
            continue
        cid = check["id"]
        if not isinstance(cid, str) or not ID.fullmatch(cid) or cid in check_by_id:
            problems.append("duplicate or invalid check id")
            continue
        check_by_id[cid] = check
        if check["stream_id"] not in stream_ids:
            problems.append("check refers to unknown stream")
        if not isinstance(check["oracle"], str) or not check["oracle"].strip():
            problems.append("missing test oracle")
        status = check["status"]
        if status not in STATES:
            problems.append("unknown check status")
        if status != "PASS":
            all_pass = False
        references = check["evidence_ids"]
        if not isinstance(references, list) or any(
            not isinstance(e, str) or e not in evidence_by_id for e in references
        ):
            problems.append("unknown evidence reference")
            continue
        if status in {"PASS", "FAIL"} and not any(
            evidence_by_id[e]["kind"] in REAL_EVIDENCE for e in references
        ):
            problems.append("PASS/FAIL requires execution evidence")
    required_checks = report["required_check_ids"]
    if not isinstance(required_checks, list) or any(
        not isinstance(x, str) for x in required_checks
    ) or len(set(required_checks)) != len(required_checks):
        problems.append("invalid required checks")
    elif not set(required_checks).issubset(check_by_id):
        problems.append("missing required check")
    gate = report["gate"]
    if gate not in {"READY_FOR_REVIEW", "BLOCKED", "INSUFFICIENT_EVIDENCE"}:
        problems.append("unsupported gate (never merge/deploy authority)")
    elif gate == "READY_FOR_REVIEW":
        if not required_checks or not all_pass or problems:
            problems.append("false ready-to-review claim")
    elif gate == "INSUFFICIENT_EVIDENCE" and any(
        c.get("status") in {"FAIL", "BLOCKED"} for c in checks if isinstance(c, dict)
    ):
        problems.append("known failure cannot be hidden as insufficient evidence")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        result = validate_report(json.loads(args.report.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"INVALID_REPORT: {type(exc).__name__}: {exc}")
        return 2
    for issue in result:
        print(f"FAIL: {issue}")
    if result:
        return 1
    print("PASS: declared QA evidence is internally consistent; no live execution verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
