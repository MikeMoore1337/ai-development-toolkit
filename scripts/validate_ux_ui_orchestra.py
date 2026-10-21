#!/usr/bin/env python3
"""Read-only structural checker for an optional UX/UI Design Orchestra receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MODES = {"audit-proposal", "audit-only", "implement-approved"}
WORKERS = {"ACTUAL_SUBAGENT", "GENERIC_SUBAGENT", "SEQUENTIAL"}
SOURCES = {"LOADED", "REFERENCE_ONLY", "UNAVAILABLE"}
EVIDENCE = {"RENDERED", "SOURCE_ONLY", "NOT_OBSERVED"}
GATES = {"AWAITING_VISUAL_APPROVAL", "VISUAL_PACKAGE_MISSING", "AUDIT_COMPLETE",
         "OWNER_ACCEPTED", "IMPLEMENTED_NOT_RELEASED"}


def validate(report: object) -> list[str]:
    """Fail closed on contradictory claims; does not independently verify screenshots."""
    if not isinstance(report, dict):
        return ["report must be object"]
    errors: list[str] = []
    for key in ("mode", "project", "baseline", "design_authority", "workers",
                "evidence", "findings", "proposal", "implementation", "gate"):
        if key not in report:
            errors.append(f"missing {key}")
    if errors:
        return errors
    mode = report["mode"]
    if mode not in MODES:
        errors.append("invalid mode")
    for name in ("project", "baseline", "design_authority"):
        if not isinstance(report[name], str) or not report[name].strip():
            errors.append(f"invalid {name}")
    workers = report["workers"]
    if not isinstance(workers, list) or not workers:
        errors.append("workers must be nonempty list")
        workers = []
    if len(workers) > 5:
        errors.append("too many workstreams")
    selected = set()
    for i, worker in enumerate(workers):
        if not isinstance(worker, dict):
            errors.append(f"worker {i}: invalid")
            continue
        name = worker.get("name")
        if not isinstance(name, str) or not name.strip() or name in selected:
            errors.append(f"worker {i}: missing or duplicate name")
        else:
            selected.add(name)
        if worker.get("execution") not in WORKERS:
            errors.append(f"worker {i}: invalid execution")
        if worker.get("source_status") not in SOURCES:
            errors.append(f"worker {i}: invalid source status")
        if worker.get("execution") in {"ACTUAL_SUBAGENT", "GENERIC_SUBAGENT"} and not worker.get("trace"):
            errors.append(f"worker {i}: subagent missing actual trace")
        if worker.get("execution") == "SEQUENTIAL" and worker.get("trace"):
            errors.append(f"worker {i}: sequential work cannot claim agent trace")
        if worker.get("source_status") == "UNAVAILABLE" and worker.get("execution") != "SEQUENTIAL":
            errors.append(f"worker {i}: unavailable skill cannot be claimed loaded by subagent")
    if report.get("max_concurrent_workers", 3) not in (1, 2, 3):
        errors.append("max_concurrent_workers must be 1..3")
    actual_concurrent = report.get("observed_peak_workers", 1)
    if type(actual_concurrent) is not int or not 1 <= actual_concurrent <= report.get("max_concurrent_workers", 3):
        errors.append("observed_peak_workers invalid")
    if actual_concurrent > 1 and not any(w.get("execution") != "SEQUENTIAL" for w in workers if isinstance(w, dict)):
        errors.append("parallel claim without subagents")
    ledger = report["evidence"]
    if not isinstance(ledger, list):
        errors.append("evidence must be list")
        ledger = []
    evidence_ids = set()
    for i, row in enumerate(ledger):
        if not isinstance(row, dict):
            errors.append(f"evidence {i}: invalid")
            continue
        identity = row.get("id")
        if not isinstance(identity, str) or not identity or identity in evidence_ids:
            errors.append(f"evidence {i}: missing or duplicate id")
        else:
            evidence_ids.add(identity)
        if row.get("status") not in EVIDENCE:
            errors.append(f"evidence {i}: invalid status")
        if row.get("status") == "RENDERED" and not all(isinstance(row.get(x), str) and row[x].strip() for x in ("artifact_ref", "route", "viewport", "provenance")):
            errors.append(f"evidence {i}: rendered claim lacks proof details")
        if row.get("status") == "NOT_OBSERVED" and row.get("artifact_ref"):
            errors.append(f"evidence {i}: not observed but artifact claimed")
    findings = report["findings"]
    if not isinstance(findings, list):
        errors.append("findings must be list")
        findings = []
    for i, row in enumerate(findings):
        if not isinstance(row, dict) or row.get("status") not in ("OBSERVED", "HYPOTHESIS"):
            errors.append(f"finding {i}: invalid")
            continue
        references = row.get("evidence_ids")
        if not isinstance(references, list) or any(x not in evidence_ids for x in references):
            errors.append(f"finding {i}: invalid evidence refs")
        if row["status"] == "OBSERVED" and not references:
            errors.append(f"finding {i}: observed without evidence")
        if not row.get("problem") or not row.get("recommendation"):
            errors.append(f"finding {i}: incomplete problem or fix")
    proposal = report["proposal"]
    if not isinstance(proposal, dict) or not isinstance(proposal.get("selected_direction"), str) or not proposal["selected_direction"].strip():
        errors.append("missing selected design direction")
    else:
        if proposal.get("visual_status") not in ("TEXT_SPEC", "RENDERED", "NOT_PREPARED"):
            errors.append("invalid proposal visual status")
        if proposal.get("visual_status") == "RENDERED" and not proposal.get("artifact_refs"):
            errors.append("proposal claims rendered visuals without artifacts")
    implementation = report["implementation"]
    if not isinstance(implementation, dict) or implementation.get("status") not in ("NOT_STARTED", "IMPLEMENTED"):
        errors.append("invalid implementation status")
    if report["gate"] not in GATES:
        errors.append("invalid gate")
    if mode != "implement-approved":
        if report.get("changed_ui") is not False:
            errors.append("audit must explicitly affirm no UI changes")
        if isinstance(implementation, dict) and implementation.get("status") != "NOT_STARTED":
            errors.append("audit must not claim implementation")
        if report["gate"] in {"OWNER_ACCEPTED", "IMPLEMENTED_NOT_RELEASED"}:
            errors.append("audit cannot claim owner acceptance or implementation")
    else:
        if not isinstance(report.get("owner_approval_evidence"), str) or not report["owner_approval_evidence"].strip():
            errors.append("implementation requires explicit owner approval evidence")
        if report["gate"] == "AWAITING_VISUAL_APPROVAL" and report.get("changed_ui"):
            errors.append("cannot implement before visual approval")
    if mode == "audit-proposal" and report["gate"] == "AWAITING_VISUAL_APPROVAL" and isinstance(proposal, dict) and proposal.get("visual_status") == "NOT_PREPARED":
        errors.append("approval requested without design proposal")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.report.read_text(encoding="utf-8"))
        errors = validate(payload)
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print("FAIL:", error)
    if not errors:
        print("PASS: structure consistent; evidence and agent execution NOT independently verified")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
