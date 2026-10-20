#!/usr/bin/env python3
"""Read-only structural validator for Issue #55 system specifications.

Not a semantic proof, source authentication, BPMN conformance or AI-client test.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "extensions/analysis/skills/business-system-analysis"
                       "/references/SYSTEM_SPEC_CONTRACT.json").read_text(encoding="utf-8"))
LABELS = set(CONTRACT["source_labels"])
CONFIRMATION = set(CONTRACT["confirmation_statuses"])
RULE_STATES = set(CONTRACT["business_rule_statuses"])
INTEGRATION = set(CONTRACT["integration_statuses"])
DECISIONS = set(CONTRACT["decision_statuses"])
TEST_STATES = set(CONTRACT["test_statuses"])


def _ids(records: list, section: str, errors: list[str], required: list[str]) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    for index, item in enumerate(records):
        if not isinstance(item, dict):
            errors.append(f"{section}[{index}]: expected object")
            continue
        absent = set(required) - set(item)
        if absent:
            errors.append(f"{section}[{index}]: missing {sorted(absent)}")
            continue
        ident = item["id"]
        if not isinstance(ident, str) or not ident.strip():
            errors.append(f"{section}[{index}]: invalid ID")
        elif ident in by_id:
            errors.append(f"{section}: duplicate ID {ident!r} (conflicting semantics possible)")
        else:
            by_id[ident] = item
    return by_id


def _refs(item: dict, field: str, allowed: set[str],
          context: str, errors: list[str]) -> None:
    values = item.get(field)
    if (not isinstance(values, list) or any(not isinstance(v, str) or v not in allowed
                                            for v in values)
            or len(values) != len(set(values))):
        errors.append(f"{context}: invalid {field} reference")


def _source(item: dict, context: str, errors: list[str]) -> None:
    if item.get("source") not in LABELS:
        errors.append(f"{context}: missing or invalid source")


def validate(document: object) -> list[str]:
    """Return deterministic structural errors without mutating any input."""
    errors: list[str] = []
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        return ["Expected schema_version=1 specification object"]
    if (document.get("document_type") != CONTRACT["document_type"]
            or document.get("artifact_status") != CONTRACT["artifact_status"]):
        errors.append("Invalid document_type or artifact_status")
    missing = set(CONTRACT["required_sections"]) - set(document)
    if missing:
        errors.append(f"Missing sections: {sorted(missing)}")
    for key in ("goal",):
        if not isinstance(document.get(key), str) or not document[key].strip():
            errors.append(f"{key}: missing")
    for key in CONTRACT["required_sections"]:
        if key in {"goal", "handoff"}:
            continue
        if key not in document or not isinstance(document[key], list):
            errors.append(f"{key}: expected list")
    if errors:
        return errors

    r = _ids(document["source_requirements"], "source_requirements", errors,
             CONTRACT["requirement_fields"])
    ac = _ids(document["acceptance_criteria"], "acceptance_criteria", errors,
              CONTRACT["acceptance_fields"])
    br = _ids(document["business_rules"], "business_rules", errors,
              CONTRACT["rule_fields"])
    uc = _ids(document["use_cases"], "use_cases", errors,
              CONTRACT["use_case_fields"])
    sr = _ids(document["system_requirements"], "system_requirements", errors,
              CONTRACT["system_requirement_fields"])
    nfr = _ids(document["nonfunctional_requirements"], "nonfunctional_requirements",
               errors, CONTRACT["nfr_fields"])
    integration = _ids(document["integrations"], "integrations", errors,
                       CONTRACT["integration_fields"])
    decision = _ids(document["decisions"], "decisions", errors, CONTRACT["decision_fields"])
    process = _ids(document["processes"], "processes", errors,
                   ["id", "start", "steps", "decisions", "errors", "cancellation", "end", "actors"])
    domain = _ids(document["domain_entities"], "domain_entities", errors,
                  ["id", "purpose", "relationships", "lifecycle", "invariants", "owner"])

    seen_behaviors: dict[str, str] = {}
    for ident, item in r.items():
        _source(item, ident, errors)
        if not isinstance(item["behavior"], str) or not item["behavior"].strip():
            errors.append(f"{ident}: empty requirement behavior")
        else:
            key = " ".join(item["behavior"].lower().split())
            if key in seen_behaviors and seen_behaviors[key] != ident:
                errors.append(f"{ident}: duplicate requirement behavior with {seen_behaviors[key]}")
            seen_behaviors[key] = ident
        _refs(item, "acceptance_ids", set(ac), ident, errors)
        if not item["acceptance_ids"]:
            errors.append(f"{ident}: missing acceptance criterion (log unresolved gap)")
    for ident, item in ac.items():
        _refs(item, "requirement_ids", set(r), ident, errors)
        if not item["requirement_ids"]:
            errors.append(f"{ident}: acceptance without source requirement")
        for parent in item["requirement_ids"]:
            if parent in r and ident not in r[parent].get("acceptance_ids", []):
                errors.append(f"{ident}: missing reciprocal link in {parent}")
    for ident, item in r.items():
        for target in item.get("acceptance_ids", []):
            if target in ac and ident not in ac[target].get("requirement_ids", []):
                errors.append(f"{ident}: acceptance {target} not reciprocally linked")

    contradictory: dict[str, set[str]] = {}
    for ident, item in br.items():
        _source(item, ident, errors)
        if item["status"] not in RULE_STATES:
            errors.append(f"{ident}: invalid rule status")
        if item["status"] == "CONFIRMED" and item["source"] in {"ASSUMPTION", "UNKNOWN"}:
            errors.append(f"{ident}: unverified business rule marked CONFIRMED")
        _refs(item, "requirement_ids", set(r), ident, errors)
        _refs(item, "acceptance_ids", set(ac), ident, errors)
        if item.get("subject") and item.get("polarity") and item["status"] == "CONFIRMED":
            contradictory.setdefault(str(item["subject"]), set()).add(str(item["polarity"]))
    for subject, polarities in contradictory.items():
        if {"ALLOW", "DENY"} <= polarities or {"REQUIRE", "DENY"} <= polarities:
            errors.append(f"UNRESOLVED_CONFLICT: contradictory confirmed rules for {subject}")

    for ident, item in uc.items():
        for field in ("main_path", "alternative_or_error_path"):
            if (not isinstance(item.get(field), list) or not item[field]
                    or not all(isinstance(x, str) and x.strip() for x in item[field])):
                errors.append(f"{ident}: missing checkable {field}")
        for field in ("observable_result", "verification"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"{ident}: missing {field}")
        _refs(item, "requirement_ids", set(r), ident, errors)
        _refs(item, "acceptance_ids", set(ac), ident, errors)
        _refs(item, "rule_ids", set(br), ident, errors)

    for ident, item in sr.items():
        parent = item["parent_requirement_id"]
        if parent not in r:
            errors.append(f"{ident}: unknown parent R-ID {parent}")
        _source(item, ident, errors)
        if item["status"] not in CONFIRMATION:
            errors.append(f"{ident}: invalid confirmation status")
        if item["status"] == "CONFIRMED" and item["source"] in {"ASSUMPTION", "UNKNOWN"}:
            errors.append(f"{ident}: unsupported CONFIRMED source")
        if item["scope"] not in {"IN", "OUT", "PROPOSED"}:
            errors.append(f"{ident}: invalid scope")
        if item["scope"] != "IN" and item["status"] == "CONFIRMED":
            errors.append(f"{ident}: PROPOSED_OUT_OF_SCOPE cannot be confirmed")
        _refs(item, "rule_ids", set(br), ident, errors)
        _refs(item, "use_case_ids", set(uc), ident, errors)
        _refs(item, "acceptance_ids", set(ac), ident, errors)
        if parent in r:
            _refs(item, "acceptance_ids", set(r[parent].get("acceptance_ids", [])),
                  ident + " parent", errors)

    for ident, item in nfr.items():
        _source(item, ident, errors)
        if item["status"] not in CONFIRMATION:
            errors.append(f"{ident}: invalid NFR status")
        if item["status"] == "CONFIRMED" and item["source"] in {"ASSUMPTION", "UNKNOWN"}:
            errors.append(f"{ident}: invented confirmed NFR")
        if item["status"] != "UNKNOWN" and any(
                not isinstance(item.get(k), str) or not item[k].strip()
                or item[k] == "UNKNOWN" for k in ("constraint", "verification")):
            errors.append(f"{ident}: untestable NFR; use UNKNOWN or define verification")

    for ident, item in integration.items():
        if item["status"] not in INTEGRATION:
            errors.append(f"{ident}: invalid integration status")
        if item["status"] == "KNOWN" and item["contract"] in {"UNKNOWN", "CONTRACT_PENDING", ""}:
            errors.append(f"{ident}: unverified interface must be CONTRACT_PENDING")
        if item["status"] == "CONTRACT_PENDING" and item["contract"] != "CONTRACT_PENDING":
            errors.append(f"{ident}: missing CONTRACT_PENDING marker")

    for ident, item in decision.items():
        _refs(item, "affected_requirements", set(r), ident, errors)
        if item["status"] not in DECISIONS:
            errors.append(f"{ident}: invalid decision status")
        if item["status"] == "APPROVED" and not str(item.get("approval_ref", "")).strip():
            errors.append(f"{ident}: proposed decision cannot be APPROVED without evidence")
    for ident, item in process.items():
        if (not str(item.get("start", "")).strip() or not str(item.get("end", "")).strip()
                or not isinstance(item.get("steps"), list) or not item["steps"]):
            errors.append(f"{ident}: incomplete process start/steps/end")
        if item.get("notation") == "BPMN_2_0_VERIFIED":
            errors.append(f"{ident}: text process falsely labelled verified BPMN 2.0")
    for ident, item in domain.items():
        if not isinstance(item["invariants"], list):
            errors.append(f"{ident}: invalid domain invariants")

    seen: set[tuple[str, str, str]] = set()
    covered: set[tuple[str, str]] = set()
    for row in document["traceability"]:
        if not isinstance(row, dict):
            errors.append("traceability: row must be object")
            continue
        if set(CONTRACT["trace_fields"]) - set(row):
            errors.append("traceability: missing fields")
            continue
        parent, system, acceptance = (row["requirement_id"],
                                       row["system_requirement_id"], row["acceptance_id"])
        key = (parent, system, acceptance)
        if key in seen:
            errors.append(f"traceability: duplicate {key}")
        seen.add(key)
        if parent not in r or system not in sr or acceptance not in ac:
            errors.append(f"traceability: unknown R/SR/AC reference {key}")
            continue
        if (sr[system]["parent_requirement_id"] != parent
                or acceptance not in sr[system]["acceptance_ids"]
                or acceptance not in r[parent]["acceptance_ids"]):
            errors.append(f"traceability: broken R->SR->AC relation {key}")
        else:
            covered.add((parent, acceptance))
        for field, allowed in (("business_rule_ids", set(br)), ("use_case_ids", set(uc)),
                               ("integration_ids", set(integration))):
            _refs(row, field, allowed, "traceability", errors)
        status = row["test_status"]
        if status not in TEST_STATES:
            errors.append("traceability: invalid test status")
        if status in {"IMPLEMENTED", "NOT_RUN", "PASS", "FAIL"} and not str(
                row["test_case_id"]).strip():
            errors.append("traceability: test claimed without test case ID")
        if status in {"PASS", "FAIL"} and not str(row["execution_evidence"]).strip():
            errors.append("traceability: unexecuted test marked PASS/FAIL")
    for ident, item in r.items():
        for acceptance in item.get("acceptance_ids", []):
            if (ident, acceptance) not in covered:
                errors.append(f"{ident}: missing traceability for {acceptance}")
    handoff = document["handoff"]
    if not isinstance(handoff, dict) or any(
            k not in handoff or not isinstance(handoff[k], list)
            for k in CONTRACT["handoff_targets"]):
        errors.append("handoff: missing UX/UI, Backend, Frontend or QA target")
    if not isinstance(document["open_questions"], list):
        errors.append("open_questions must be list")
    if not isinstance(document["conflicts"], list):
        errors.append("conflicts must be list")
    for item in document["stakeholders"]:
        if not isinstance(item, dict) or item.get("source") not in LABELS:
            errors.append("stakeholders: missing source label")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", type=Path, help="Explicitly authorized JSON file OUTSIDE Toolkit")
    args = parser.parse_args()
    try:
        issues = validate(json.loads(args.spec.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"INVALID: {type(exc).__name__}: {exc}")
        return 1
    for issue in issues:
        print("INVALID: " + issue)
    print("STRUCTURAL_PASS (NOT semantic verification / model activation)" if not issues
          else f"STRUCTURAL_FAIL: {len(issues)} issue(s)")
    return int(bool(issues))


if __name__ == "__main__":
    raise SystemExit(main())
