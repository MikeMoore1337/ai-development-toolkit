#!/usr/bin/env python3
"""Issue #69: bounded offline tool/permission/evidence contract validator.

Contracts are illustrative, not a runtime authorization engine. No network,
credentials, external installation, user data, or source-project writes.
"""
from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "tool-integrations"
CLASSES = {"READ", "PREPARE", "WRITE", "EXECUTE", "PUBLISH", "DEPLOY", "ADMIN", "FINANCIAL"}
CATEGORIES = {"NATIVE_CLIENT_TOOL", "CONNECTED_TOOL", "PROJECT_LOCAL_TOOL",
              "CLI_TOOL", "EXTERNAL_SERVICE", "REFERENCE_ONLY"}
DATA_CLASSES = {"PUBLIC", "PROJECT_INTERNAL", "CONFIDENTIAL",
                "PERSONAL_DATA", "SECRET", "UNKNOWN"}
DECISIONS = {"NO_INSTALL_NEEDED", "ADOPT_REFERENCE", "REUSE_EXISTING",
             "PILOT_PROPOSED", "APPROVED_FOR_INSTALL", "REJECTED", "BLOCKED"}
REVERSIBILITY = {"REVERSIBLE", "PARTIALLY_REVERSIBLE", "IRREVERSIBLE", "UNKNOWN"}
EXECUTION = {"NOT_ATTEMPTED", "PREPARED", "AUTHORIZED", "EXECUTED",
             "EXECUTION_FAILED", "RESULT_VERIFIED", "RESULT_UNVERIFIED", "BLOCKED"}
REQUIRED = {
    "client": {"id", "capability", "connection"},
    "tool": {"id", "name", "provider", "category", "version", "source", "trust",
             "supported_actions", "required_scopes", "network_destinations",
             "authentication", "data_access", "side_effects", "reversibility",
             "approval_requirements", "alternatives", "evidence_level", "limitations"},
    "task": {"resource", "repository", "organization", "environment", "operation",
             "operation_class", "scope", "data_classification", "target_type",
             "owner_approved_design"},
    "permission": {"id", "tool_id", "client_id", "resource", "repository",
                   "organization", "environment", "operation", "operation_class",
                   "required_scope", "available_scopes", "source", "status",
                   "approval_reference", "expires", "data_classification",
                   "egress_allowed", "side_effects", "reversibility", "cost_policy"},
    "egress": {"source", "destination", "actual_destination", "expected_destinations",
               "data_classification", "allowed_classes", "payload_minimized",
               "contains_secret", "output_is_instruction", "redirect"},
    "cost": {"status", "pricing_source", "pricing_review_date",
             "free_tier_conditions", "estimated_requests", "used_requests",
             "quota", "policy", "planned_cost", "actual_cost"},
    "integration": {"decision", "native_sufficient", "gap_demonstrated",
                    "install_attempted", "approval_for_install", "source_revision",
                    "benefit", "benefit_measured", "requires_real_credentials",
                    "removal_plan", "residual_data_ack"},
    "preview": {"state", "tool_supports_dry_run", "claims_dry_run", "has_side_effect"},
    "execution": {"status", "reported_executed", "tool_response_reference",
                  "observed_result", "verified", "live_access", "claims_live_check",
                  "claimed_approved_design", "unsafe_retry", "publication_performed"},
    "storage": {"toolkit_written", "destination"},
}


def read(name: str) -> dict:
    """Load only fixed, repository-owned synthetic fixtures."""
    if name not in {"github.json", "figma.json", "server.json", "broken.json"}:
        raise ValueError("Unknown fixture name")
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def mutated(original: dict, path: list[str], value: object) -> dict:
    result = copy.deepcopy(original)
    node = result
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value
    return result


def audit(case: dict) -> list[str]:
    """Fail closed for any unsupported claim. This never grants actual access."""
    errors: set[str] = set()

    def need(condition: bool, code: str) -> None:
        if not condition:
            errors.add(code)

    if not isinstance(case, dict) or case.get("synthetic") is not True:
        return ["NOT_SYNTHETIC"]
    if set(case) != {"schema_version", "synthetic", "scenario", "controller",
                     "active_controllers", *REQUIRED} or case["schema_version"] != 1:
        return ["SCHEMA"]
    if any(not isinstance(case.get(k), dict) or set(case[k]) != fields
           for k, fields in REQUIRED.items()):
        return ["SCHEMA"]
    c, t, task, p = (case[k] for k in ("client", "tool", "task", "permission"))
    e, cost, i = (case[k] for k in ("egress", "cost", "integration"))
    v, run, storage = (case[k] for k in ("preview", "execution", "storage"))
    need(case["controller"] in {"feature-delivery", "make-feature"} and
         case["active_controllers"] == [case["controller"]], "DUPLICATE_CONTROLLER")
    need(case["scenario"] in {"github_review", "figma_audit", "server_docs"}, "UNKNOWN_SCENARIO")
    need(t["category"] in CATEGORIES, "TOOL_CATEGORY")
    need(bool(t["id"] and t["name"] and t["provider"] and t["source"] and
              t["trust"] and t["alternatives"] and t["limitations"]), "TOOL_INVENTORY")
    need(isinstance(t["supported_actions"], list) and
         task["operation"] in t["supported_actions"], "UNSUPPORTED_OPERATION")
    need(c["capability"] == "AVAILABLE", "CAPABILITY_NOT_CONFIRMED")
    need(c["connection"] == "CONNECTED", "TOOL_NOT_CONNECTED")
    need(task["operation_class"] in CLASSES, "OPERATION_CLASS")
    need(p["status"] == "GRANTED" and p["source"] == "SYNTHETIC_OWNER" and
         isinstance(p["approval_reference"], str) and
         bool(p["approval_reference"]), "AUTHORIZATION_MISSING")
    need(p["tool_id"] == t["id"] and p["client_id"] == c["id"], "GRANT_ID_MISMATCH")
    need(task["resource"] == p["resource"], "CROSS_RESOURCE")
    need(task["repository"] == p["repository"], "CROSS_REPOSITORY")
    need(task["organization"] == p["organization"], "CROSS_ORGANIZATION")
    need(task["environment"] == p["environment"], "WRONG_ENVIRONMENT")
    need(task["operation"] == p["operation"] and
         task["operation_class"] == p["operation_class"], "OPERATION_ESCALATION")
    need(task["scope"] == p["required_scope"] and
         task["scope"] in p["available_scopes"] and
         task["scope"] in t["required_scopes"], "MISSING_CREDENTIAL_SCOPE")
    try:
        need(date.fromisoformat(p["expires"]) >= date.today(), "EXPIRED_AUTHORIZATION")
    except (TypeError, ValueError):
        errors.add("EXPIRED_AUTHORIZATION")
    need(task["data_classification"] in DATA_CLASSES and
         task["data_classification"] != "UNKNOWN", "UNKNOWN_CLASSIFICATION")
    need(task["data_classification"] == p["data_classification"] ==
         e["data_classification"], "DATA_CLASS_MISMATCH")
    need(task["data_classification"] in e["allowed_classes"] and
         p["egress_allowed"] is True, "SENSITIVE_EGRESS")
    need(e["payload_minimized"] is True, "EXCESS_DATA_EGRESS")
    need(e["contains_secret"] is False, "SECRET_IN_LOG_OR_EGRESS")
    need(e["output_is_instruction"] is False, "TOOL_OUTPUT_INJECTION")
    need(e["actual_destination"] == e["destination"] and
         e["actual_destination"] in e["expected_destinations"] and
         e["actual_destination"] in t["network_destinations"], "UNEXPECTED_DESTINATION")
    need(e["redirect"] is False, "UNEXPECTED_REDIRECT")
    need(cost["policy"] == "ZERO_SPEND" and p["cost_policy"] == "ZERO_SPEND" and
         cost["planned_cost"] == 0 and cost["actual_cost"] == 0, "COST_BOUNDARY")
    need(cost["status"] == "VERIFIED_ZERO" and bool(cost["pricing_source"])
         and bool(cost["pricing_review_date"]), "COST_UNKNOWN")
    need(all(isinstance(cost[key], int) and not isinstance(cost[key], bool) and
             cost[key] >= 0 for key in ("estimated_requests", "used_requests", "quota")),
         "INVALID_QUOTA")
    if all(isinstance(cost[key], int) for key in ("estimated_requests", "used_requests", "quota")):
        need(cost["used_requests"] + cost["estimated_requests"] <= cost["quota"],
             "RATE_LIMIT_EXCEEDED")
    need(i["decision"] in DECISIONS, "DECISION_INVALID")
    need(i["install_attempted"] is False, "UNAUTHORIZED_INSTALL")
    need(not i["native_sufficient"] or i["decision"] in
         {"NO_INSTALL_NEEDED", "REUSE_EXISTING", "ADOPT_REFERENCE"}, "NATIVE_IGNORED")
    need(i["decision"] not in {"PILOT_PROPOSED", "APPROVED_FOR_INSTALL"}
         or i["gap_demonstrated"], "MISSING_INTEGRATION_GAP")
    need(i["decision"] != "APPROVED_FOR_INSTALL" or i["approval_for_install"],
         "INSTALL_APPROVAL_MISSING")
    need(i["benefit"] == "HYPOTHESIS" or i["benefit_measured"],
         "UNMEASURED_BENEFIT")
    need(i["requires_real_credentials"] is False, "REAL_CREDENTIALS_REQUESTED")
    need(bool(i["removal_plan"]) and i["residual_data_ack"] is True,
         "REMOVAL_DATA_POLICY")
    need(v["state"] in {"PLAN", "DRY_RUN", "APPROVAL_PENDING", "EXECUTE", "VERIFY"},
         "PREVIEW_STATE")
    need(not v["claims_dry_run"] or
         (v["state"] == "DRY_RUN" and v["tool_supports_dry_run"]), "FAKE_DRY_RUN")
    need(not (v["state"] in {"PLAN", "DRY_RUN", "APPROVAL_PENDING"} and
              v["has_side_effect"]), "PREVIEW_SIDE_EFFECT")
    need(p["reversibility"] in REVERSIBILITY and
         t["reversibility"] in REVERSIBILITY, "REVERSIBILITY_INVALID")
    need(not (p["reversibility"] == "REVERSIBLE" and
              t["reversibility"] in {"IRREVERSIBLE", "UNKNOWN"}),
         "UNSUPPORTED_ROLLBACK")
    need(run["status"] in EXECUTION, "EXECUTION_STATUS")
    need(run["status"] in {"NOT_ATTEMPTED", "PREPARED", "BLOCKED", "AUTHORIZED"},
         "SYNTHETIC_EXECUTION_CLAIM")
    need(run["reported_executed"] is False and run["publication_performed"] is False,
         "FABRICATED_EXTERNAL_ACTION")
    need(not run["verified"] and run["observed_result"] is None and
         run["tool_response_reference"] is None, "FALSE_VERIFICATION")
    need(not run["live_access"] and not run["claims_live_check"],
         "FAKE_LIVE_MONITORING")
    need(not run["claimed_approved_design"] or task["owner_approved_design"],
         "DESIGN_APPROVAL_CONFUSION")
    need(not run["unsafe_retry"], "UNSAFE_RETRY")
    need(not storage["toolkit_written"] and storage["destination"] == "CHAT",
         "TOOLKIT_CONTAMINATION")
    if case["scenario"] == "github_review":
        need(task["operation_class"] == "READ" and task["target_type"] == "GITHUB",
             "GITHUB_REVIEW_BOUNDARY")
    elif case["scenario"] == "figma_audit":
        need(task["operation_class"] == "READ" and task["target_type"] == "DESIGN"
             and t["category"] == "PROJECT_LOCAL_TOOL"
             and i["decision"] == "NO_INSTALL_NEEDED"
             and not task["owner_approved_design"], "FIGMA_OPTIONAL_BOUNDARY")
    elif case["scenario"] == "server_docs":
        need(task["target_type"] == "ENVIRONMENT" and task["operation"] == "read_docs"
             and t["category"] == "REFERENCE_ONLY" and
             not run["live_access"], "NO_SERVER_ACCESS")
    return sorted(errors)


def validate() -> tuple[int, int]:
    references = {name: read(name) for name in
                  ("github.json", "figma.json", "server.json")}
    for name, item in references.items():
        failures = audit(item)
        if failures:
            raise ValueError(f"{name}: {failures}")
    mutations = read("broken.json")["cases"]
    if len(mutations) < 36:
        raise ValueError("Insufficient negative oracles")
    seen: set[str] = set()
    for entry in mutations:
        if entry["id"] in seen:
            raise ValueError("Duplicate negative case")
        seen.add(entry["id"])
        base = references[entry["scenario"] + ".json"]
        errors = audit(mutated(base, entry["path"], entry["value"]))
        if entry["error"] not in errors:
            raise ValueError(f"{entry['id']}: expected {entry['error']}, got {errors}")
    return len(references), len(mutations)


def main() -> int:
    try:
        positive, negative = validate()
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: tool integration contracts: {exc}")
        return 1
    print(f"PASS: {positive} synthetic scenarios; {negative} independent negative mutations; no external calls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
