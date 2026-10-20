#!/usr/bin/env python3
"""Read-only structural validation for optional delivery-plan JSON.

Validates declared links and status evidence SHAPE, not whether external claims are true.
No GitHub access, no automatic status changes and no filesystem writes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TYPES = {"BLOCKS", "RELATED", "REQUIRES_DECISION", "REQUIRES_APPROVAL", "OPTIONAL"}
STATUSES = {"DRAFT", "PLANNED", "IN_PROGRESS", "BLOCKED", "READY_FOR_REVIEW",
            "VERIFIED", "MERGED", "RELEASED", "CANCELLED", "NOT_APPLICABLE"}
EVIDENCE = {"STARTED", "TEST_PASS", "REVIEW", "ARTIFACT", "GITHUB_MERGE",
            "DEPLOY", "RELEASE"}
ADVANCED = {"IN_PROGRESS", "READY_FOR_REVIEW", "VERIFIED", "MERGED", "RELEASED"}
SATISFIED = {"VERIFIED", "MERGED", "RELEASED"}
REQUIRED = {"id", "title", "goal", "requirement_ids", "acceptance_ids",
            "outcome", "scope", "dependencies", "priority", "verification",
            "owner", "status", "evidence", "blockers", "approvals", "risk_ids"}


def validate(plan: object) -> list[str]:
    """Return deterministic human-readable errors; do not mutate inputs."""
    errors: list[str] = []
    if not isinstance(plan, dict) or plan.get("schema_version") != 1:
        return ["Expected schema_version=1 plan object"]
    tasks = plan.get("tasks")
    if not isinstance(tasks, list):
        return ["tasks must be a list"]
    req = plan.get("requirements")
    ac = plan.get("acceptance_criteria")
    risks = plan.get("risks", [])
    changes = plan.get("changes", [])
    if not isinstance(req, list) or not all(isinstance(x, str) for x in req):
        errors.append("requirements must contain original R-IDs")
        req = []
    if not isinstance(ac, list) or not all(isinstance(x, str) for x in ac):
        errors.append("acceptance_criteria must contain original AC-IDs")
        ac = []
    for label, values in (("requirements", req), ("acceptance_criteria", ac)):
        if len(values) != len(set(values)):
            errors.append(f"{label} contains duplicate IDs")
    if not isinstance(risks, list) or not isinstance(changes, list):
        errors.append("risks and changes must be lists")
        risks, changes = [], []
    required_risk = {"id", "description", "cause", "impact", "probability", "severity",
                     "detection", "mitigation", "contingency", "owner", "state"}
    risk_ids: set[str] = set()
    for risk in risks:
        if not isinstance(risk, dict) or not required_risk <= risk.keys():
            errors.append("risk missing required fields")
            continue
        ident = risk["id"]
        if not isinstance(ident, str) or not ident or ident in risk_ids:
            errors.append("invalid or duplicate risk id")
        else:
            risk_ids.add(ident)
    required_change = {"id", "type", "affected_requirements", "affected_tasks",
                       "dependency_impact", "verification_impact", "risk_impact", "approval"}
    change_types = {"NEW_REQUIREMENT", "CLARIFICATION", "BUG_FIX", "REPRIORITIZE",
                    "CANCEL", "DEFER", "AC_CHANGE"}
    for change in changes:
        if not isinstance(change, dict) or not required_change <= change.keys():
            errors.append("change missing required fields")
        elif change["type"] not in change_types:
            errors.append("invalid scope change type")
    ids: set[str] = set()
    by_id: dict[str, dict] = {}
    for task in tasks:
        if not isinstance(task, dict) or not REQUIRED <= task.keys():
            errors.append("task missing required fields")
            continue
        ident = task["id"]
        if not isinstance(ident, str) or not ident or ident in ids:
            errors.append("invalid or duplicate task id")
            continue
        ids.add(ident)
        by_id[ident] = task
        for field, allowed in (("requirement_ids", req), ("acceptance_ids", ac),
                               ("risk_ids", risk_ids)):
            values = task[field]
            if not isinstance(values, list) or any(
                    not isinstance(x, str) or x not in allowed for x in values):
                errors.append(f"{ident}: invalid {field} reference")
        if not isinstance(task["dependencies"], list):
            errors.append(f"{ident}: dependencies must be a list")
        if not isinstance(task["blockers"], list):
            errors.append(f"{ident}: blockers must be a list")
        if not isinstance(task["evidence"], list):
            errors.append(f"{ident}: evidence must be a list")
            continue
        if task["status"] not in STATUSES:
            errors.append(f"{ident}: unknown status")
            continue
        kinds = set()
        for item in task["evidence"]:
            if (not isinstance(item, dict) or item.get("kind") not in EVIDENCE
                    or not isinstance(item.get("ref"), str) or not item["ref"].strip()):
                errors.append(f"{ident}: invalid evidence record")
            else:
                kinds.add(item["kind"])
        status = task["status"]
        if status == "BLOCKED" and not task["blockers"]:
            errors.append(f"{ident}: BLOCKED needs an identified blocker")
        if status in ADVANCED and not kinds:
            errors.append(f"{ident}: {status} cannot be claimed without evidence")
        if status == "IN_PROGRESS" and "STARTED" not in kinds:
            errors.append(f"{ident}: IN_PROGRESS needs STARTED evidence")
        if status in {"VERIFIED", "MERGED", "RELEASED"} and not kinds & {
                "TEST_PASS", "REVIEW", "ARTIFACT"}:
            errors.append(f"{ident}: verification evidence missing")
        if status in {"MERGED", "RELEASED"} and "GITHUB_MERGE" not in kinds:
            errors.append(f"{ident}: merge evidence missing")
        if status == "RELEASED" and not kinds & {"DEPLOY", "RELEASE"}:
            errors.append(f"{ident}: release evidence missing")
    graph: dict[str, set[str]] = {name: set() for name in by_id}
    for ident, task in by_id.items():
        if not isinstance(task["dependencies"], list):
            continue
        for dep in task["dependencies"]:
            if not isinstance(dep, dict) or dep.get("type") not in TYPES:
                errors.append(f"{ident}: invalid dependency type")
                continue
            typ = dep["type"]
            if typ == "BLOCKS":
                upstream = dep.get("task_id")
                if upstream not in by_id:
                    errors.append(f"{ident}: unknown blocking predecessor {upstream!r}")
                    continue
                graph[ident].add(upstream)
                if upstream == ident:
                    errors.append(f"{ident}: self dependency")
                if task["status"] in ADVANCED and by_id[upstream]["status"] not in SATISFIED:
                    errors.append(f"{ident}: unsatisfied BLOCKS predecessor {upstream}")
            elif typ in {"REQUIRES_DECISION", "REQUIRES_APPROVAL"}:
                if not isinstance(dep.get("reference"), str) or not dep["reference"].strip():
                    errors.append(f"{ident}: missing gate reference")
                if task["status"] in ADVANCED and dep.get("resolved") is not True:
                    errors.append(f"{ident}: unresolved {typ}")
            elif "task_id" in dep and dep["task_id"] not in by_id:
                errors.append(f"{ident}: unknown related task")
    colors: dict[str, int] = {}
    def visit(node: str, trail: tuple[str, ...]) -> None:
        if colors.get(node) == 2:
            return
        if colors.get(node) == 1:
            errors.append("dependency cycle: " + " -> ".join((*trail, node)))
            return
        colors[node] = 1
        for predecessor in sorted(graph[node]):
            visit(predecessor, (*trail, node))
        colors[node] = 2
    for node in sorted(graph):
        visit(node, ())
    for change in changes:
        if isinstance(change, dict) and required_change <= change.keys():
            if any(x not in req for x in change["affected_requirements"]):
                errors.append("scope change references unknown R-ID")
            if any(x not in ids for x in change["affected_tasks"]):
                errors.append("scope change references unknown task")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path, help="Authorized JSON plan path (read-only)")
    args = parser.parse_args()
    try:
        issues = validate(json.loads(args.plan.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        print(f"INVALID: {type(exc).__name__}: {exc}")
        return 1
    for item in issues:
        print(f"INVALID: {item}")
    print("STRUCTURAL_PASS (not independent evidence verification)" if not issues
          else f"STRUCTURAL_FAIL: {len(issues)} issue(s)")
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
