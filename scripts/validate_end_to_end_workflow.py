#!/usr/bin/env python3
"""Read-only, deterministic workflow contract oracle. Fictional data, no agents/API."""
from __future__ import annotations

import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "fixtures/end-to-end-workflow"
STAGES = ("discovery", "prd", "planning", "analysis", "ux", "architecture",
          "implementation", "qa", "security", "release", "operations", "support")
CONTROLLERS = {"feature-delivery", "make-feature"}
LEVELS = {"PROPOSED", "SOURCE_BACKED", "CONTRACT_VALIDATED",
          "SYNTHETIC_TESTED", "IMPLEMENTED", "TESTED", "INDEPENDENT_REVIEWED",
          "MERGED", "RELEASED", "DEPLOYED", "USER_VERIFIED", "NOT_TESTED", "BLOCKED"}
RELATIONS = {"BLOCKS", "RELATED", "REQUIRES_DECISION", "REQUIRES_APPROVAL", "OPTIONAL"}


def load(name: str) -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def mutate(source: dict, path: list[str | int], value: object) -> dict:
    result = copy.deepcopy(source)
    current = result
    for part in path[:-1]:
        current = current[part]
    current[path[-1]] = value
    return result


def audit(w: dict) -> list[str]:
    """Validate assertions, not existence of Markdown, actual client execution or intent."""
    errors: set[str] = set()

    def need(condition: bool, code: str) -> None:
        if not condition:
            errors.add(code)

    if not isinstance(w, dict) or not w.get("synthetic"):
        return ["NOT_SYNTHETIC"]
    chosen = w.get("controller")
    need(chosen in CONTROLLERS, "UNKNOWN_CONTROLLER")
    need(w.get("active_controllers") == [chosen], "DUP_CONTROLLER")
    need(w.get("mode") in ("quick", "normal", "deep"), "INVALID_MODE")
    need(bool(w.get("workflow_id")) and bool(w.get("source_request"))
         and bool(w.get("project_ref")), "WORKFLOW_IDENTITY")
    stages = w.get("stages", [])
    ids = [s.get("id") for s in stages]
    need(len(ids) == len(set(ids)) and all(x in STAGES for x in ids), "INVALID_STAGE")
    need(ids == sorted(ids, key=lambda x: STAGES.index(x) if x in STAGES else 99),
         "STAGE_ORDER")
    required = set(w.get("required_stages", []))
    need(required <= set(ids) and all(x in STAGES for x in required), "REQUIRED_STAGE")
    artifacts = w.get("artifacts", {})
    revision = w.get("source_revision")
    for s in stages:
        if s.get("status") == "NOT_APPLICABLE":
            need(bool(s.get("skip_reason")), "UNJUSTIFIED_SKIP")
        if s.get("status") not in ("PROPOSED", "COMPLETE", "BLOCKED", "NOT_APPLICABLE"):
            errors.add("ILLEGAL_STATUS")
        if s.get("input") not in artifacts or s.get("output") not in artifacts:
            errors.add("MISSING_ARTIFACT")
        if s.get("source_revision") != revision:
            errors.add("SOURCE_REVISION_MISMATCH")
    original_r = set(w.get("original_r_ids", []))
    original_ac = set(w.get("original_ac_ids", []))
    reqs = {r["id"] for r in w.get("requirements", [])}
    acs = {a["id"] for a in w.get("acceptance", [])}
    need(original_r <= reqs and bool(original_r), "REQUIREMENT_LOST")
    need(original_ac <= acs and bool(original_ac), "AC_LOST")
    need(all(a.get("r") in reqs for a in w.get("acceptance", [])), "AC_PARENT_LOST")
    trace = w.get("trace", [])
    need(all(any(t.get("r") == a.get("r") and t.get("ac") == a.get("id")
                 for t in trace) for a in w.get("acceptance", [])),
         "TRACEABILITY_LOST")
    evidence = {e.get("id"): e for e in w.get("evidence", [])}
    need(all(e.get("level") in LEVELS for e in evidence.values()), "ILLEGAL_STATUS")
    for t in trace:
        need(t.get("r") in reqs and t.get("ac") in acs, "TRACEABILITY_LOST")
        need(t.get("evidence") in evidence, "MISSING_EVIDENCE")
    for e in evidence.values():
        if e.get("level") in ("TESTED", "INDEPENDENT_REVIEWED", "USER_VERIFIED"):
            need(e.get("executed") is True and bool(e.get("observations")),
                 "QA_UNPROVEN")
        if e.get("level") == "INDEPENDENT_REVIEWED":
            need(e.get("separate_context") is True and e.get("invoked") is True,
                 "FICTIONAL_REVIEW")
        if e.get("level") in ("MERGED", "RELEASED", "DEPLOYED", "USER_VERIFIED"):
            need(e.get("receipt") is not None, "ILLEGAL_STATUS")
    for v in w.get("tests", []):
        if v.get("status") == "PASS":
            need(v.get("executed") is True and bool(v.get("observed"))
                 and v.get("evidence") in evidence, "TEST_NOT_EXECUTED")
        if v.get("status") == "PASS" and not w.get("capabilities", {}).get("execute"):
            errors.add("QA_UNPROVEN")
    if w.get("acceptance_claim") == "PASS":
        need(all(v.get("status") == "PASS" for v in w.get("tests", [])),
             "AC_MISMATCH")
    if w.get("outcome") == "DONE":
        need(w.get("acceptance_claim") == "PASS"
             and not w.get("blockers"), "PREMATURE_DONE")
    for h in w.get("handoffs", []):
        need(h.get("from") in STAGES and h.get("to") in STAGES
             and h.get("source_artifact") in artifacts
             and h.get("deliverable") in artifacts, "HANDOFF_ARTIFACT")
        need(h.get("source_revision") == revision, "SOURCE_REVISION_MISMATCH")
        need(set(h.get("r_ids", [])) <= original_r
             and set(h.get("ac_ids", [])) <= original_ac, "TRACEABILITY_LOST")
        if h.get("status") == "ACCEPTED":
            need(h.get("receiver_ack") not in (None, "NOT_AVAILABLE"),
                 "APPROVAL_UNCONFIRMED")
    edges = w.get("dependencies", [])
    graph: dict[str, set[str]] = {x: set() for x in STAGES}
    for edge in edges:
        u, v = edge.get("from"), edge.get("to")
        if u not in STAGES or v not in STAGES or edge.get("type") not in RELATIONS:
            errors.add("INVALID_DEPENDENCY")
            continue
        if edge["type"] == "BLOCKS":
            graph[u].add(v)
            if not edge.get("satisfied") and any(s.get("id") == v and
                    s.get("status") == "COMPLETE" for s in stages):
                errors.add("DEPENDENCY_REQUIRED")
    visited: set[str] = set()
    visiting: set[str] = set()

    def cycle(node: str) -> None:
        if node in visiting:
            errors.add("DEPENDENCY_CYCLE")
            return
        if node in visited:
            return
        visiting.add(node)
        for target in graph[node]:
            cycle(target)
        visiting.remove(node)
        visited.add(node)

    for node in STAGES:
        cycle(node)
    need(any(e.get("from") == "implementation" and e.get("to") == "qa"
             and e.get("type") == "BLOCKS" for e in edges), "DEPENDENCY_REQUIRED")
    scopes = w.get("scope", {})
    allowed = set(scopes.get("approved", []))
    implemented = set(scopes.get("implemented", []))
    excluded = set(scopes.get("excluded", []))
    need(implemented <= allowed and not implemented & excluded, "SCOPE_CREEP")
    permissions = w.get("permissions", {})
    actions = w.get("actions", {})
    caps = w.get("capabilities", {})
    need(not actions.get("change") or
         permissions.get("change") and caps.get("write"), "WRITE_NOT_AUTHORIZED")
    need(not actions.get("execute") or
         permissions.get("execute") and caps.get("execute"), "TOOL_UNAVAILABLE")
    need(not actions.get("external") or
         permissions.get("external") and caps.get("external"), "APPROVAL_UNCONFIRMED")
    need(not actions.get("paid_api") or permissions.get("paid_api"),
         "PAID_NOT_APPROVED")
    need(not actions.get("toolkit_write"), "TOOLKIT_WRITE")
    need(not actions.get("irreversible") or permissions.get("irreversible"),
         "APPROVAL_UNCONFIRMED")
    gates = w.get("gates", {})
    need(not gates.get("security_applicable") or gates.get("security_checked"),
         "SECURITY_SKIPPED")
    need(not gates.get("visual_required") or gates.get("visual_approved"),
         "VISUAL_APPROVAL_MISSING")
    release = w.get("release", {})
    need(not release.get("implemented") or actions.get("change") and
         bool(release.get("implementation_receipt")), "DESIGN_NOT_IMPLEMENTED")
    need(not release.get("merged") or bool(release.get("merge_receipt"))
         and bool(release.get("exact_sha")), "MERGE_UNPROVEN")
    need(not release.get("deployed") or release.get("merged") and
         bool(release.get("deploy_receipt")), "DEPLOY_UNPROVEN")
    need(not release.get("production") or release.get("deployed"),
         "LOCAL_NOT_PRODUCTION")
    need(not release.get("published") or permissions.get("publish")
         and bool(release.get("publish_receipt")), "PUBLISH_NOT_APPROVED")
    need(not release.get("user_verified") or release.get("deployed") and
         bool(release.get("user_receipt")), "USER_VERIFICATION_UNPROVEN")
    need(not release.get("support_version") or
         release.get("support_version") == release.get("version") and
         release.get("deployed"), "SUPPORT_VERSION_MISMATCH")
    need(not release.get("state") == "RELEASED" or release.get("published")
         and release.get("deployed"), "ILLEGAL_STATUS")
    for call in w.get("tool_calls", []):
        need(call.get("name") in caps.get("available_tools", [])
             and call.get("receipt") is not None, "TOOL_UNAVAILABLE")
    resume = w.get("resume", {})
    need(not resume.get("duplicate_state") and not resume.get("duplicate_issue"),
         "DUPLICATE_STATE")
    need(resume.get("delegations_used", 0) >= resume.get("delegations_before", 0),
         "BUDGET_RESET")
    need(not resume.get("irreversible_replayed"), "IRREVERSIBLE_REPEAT")
    need(set(resume.get("accepted_decisions", [])) <=
         set(w.get("decisions", [])), "LOST_DECISION")
    need(set(resume.get("previous_evidence", [])) <= set(evidence), "MISSING_EVIDENCE")
    need(set(resume.get("blockers", [])) <=
         {x["id"] for x in w.get("blockers", [])}, "LOST_BLOCKER")
    if resume.get("previous_head") != resume.get("current_head") or (
            resume.get("previous_source_revision") != revision):
        need(bool(resume.get("revalidation")), "STALE_EVIDENCE")
    return sorted(errors)


def validate() -> tuple[int, int]:
    reference = load("reference.json")
    failures = audit(reference)
    if failures:
        raise AssertionError(f"Reference rejected: {failures}")
    cases = load("broken_cases.json")["cases"]
    for case in cases:
        observed = audit(mutate(reference, case["path"], case["value"]))
        if case["expected_error"] not in observed:
            raise AssertionError(f"{case['id']}: expected {case['expected_error']}; got {observed}")
    print(f"PASS: reference=1; broken={len(cases)}; no external actions")
    return 1, len(cases)


if __name__ == "__main__":
    validate()
