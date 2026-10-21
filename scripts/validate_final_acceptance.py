#!/usr/bin/env python3
"""Issue #70: read-only final acceptance oracle. No agents, network, API or writes."""
from __future__ import annotations

import copy
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.validate_end_to_end_workflow import audit as workflow_audit  # noqa: E402
from scripts.validate_end_to_end_workflow import load as workflow_load  # noqa: E402

DATA = ROOT / "fixtures" / "final-acceptance"
STAGES = ("S1", "S2", "S3", "S4", "S5", "S6")
PHASES = ("discovery", "prd", "planning", "analysis", "ux", "architecture",
          "implementation", "qa", "security", "release", "operations", "support")
STATUSES = {"PASS", "FAIL", "NOT_TESTED", "BLOCKED", "NOT_APPLICABLE", "INCONCLUSIVE"}
EVIDENCE_LEVELS = {"SOURCE_ONLY", "CONTRACT_VALIDATED", "SYNTHETIC_TESTED",
                   "EXECUTED", "INDEPENDENT_REVIEWED", "OWNER_REPORTED",
                   "NOT_TESTED", "BLOCKED"}
REQUIREMENT = re.compile(r"^[NX]-R[1-9]\d*$")
CRITERION = re.compile(r"^[NX]-AC[1-9]\d*$")


def load(name: str = "contract.json") -> dict:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def mutate(source: dict, path: list[str | int], value: object, *, delete=False) -> dict:
    result = copy.deepcopy(source)
    cursor = result
    for part in path[:-1]:
        cursor = cursor[part]
    if delete:
        if isinstance(cursor, list):
            cursor.pop(path[-1])
        else:
            del cursor[path[-1]]
    else:
        cursor[path[-1]] = value
    return result


def _source_ok(relative: object, root: Path) -> bool:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        return False
    part = Path(relative)
    if part.is_absolute() or ".." in part.parts or "." in part.parts:
        return False
    target = root / part
    if not target.is_file() or not target.resolve().is_relative_to(root.resolve()):
        return False
    return not any(p.is_symlink() for p in (target, *target.parents) if p != root.parent)


def audit(document: dict, root: Path = ROOT) -> list[str]:
    """Discriminate invalid *claims* and trace models; not subjective usability."""
    errors: set[str] = set()

    def need(ok: bool, code: str) -> None:
        if not ok:
            errors.add(code)

    if not isinstance(document, dict) or document.get("schema_version") != 1 or not document.get("synthetic"):
        return ["INVALID_CONTRACT"]
    need(document.get("issue_reference") == "ISSUE-70" and
         document.get("roadmap_id") == "ISSUE-42", "WRONG_ROADMAP")
    need(document.get("stages") == list(STAGES), "STAGE_COVERAGE")
    checks = document.get("checks", [])
    check_ids = [c.get("id") for c in checks]
    need(len(check_ids) == len(set(check_ids)), "DUPLICATE_CRITERION")
    need(set(c.get("stage") for c in checks) == set(STAGES) and
         all(sum(c.get("stage") == stage for c in checks) >= 4 for stage in STAGES),
         "STAGE_COVERAGE")
    for c in checks:
        method = c.get("method")
        need(c.get("status") in STATUSES, "UNKNOWN_STATUS")
        if method == "SOURCE_PRESENCE":
            need(_source_ok(c.get("source"), root), "MISSING_SOURCE")
        elif method not in ("LIVE_MODEL", "INDEPENDENT_HUMAN"):
            errors.add("UNKNOWN_METHOD")
        if method == "LIVE_MODEL":
            need(c.get("status") == "BLOCKED" and bool(c.get("blocker")),
                 "OWNER_GATE_BYPASS")
        if method == "INDEPENDENT_HUMAN" and c.get("status") == "PASS":
            errors.add("FAKE_NOVICE_SESSION")
        if c.get("status") == "PASS":
            # The manifest may declare observations, but must never pre-record execution.
            errors.add("PASS_UNPROVEN")

    journeys = document.get("journeys", [])
    need(len(journeys) == 2 and {j.get("id") for j in journeys} == {"NOVICE", "EXPERT"},
         "MISSING_JOURNEY")
    for j in journeys:
        ident = j.get("id")
        revision = j.get("source_revision")
        need(j.get("synthetic") is True and bool(j.get("original_goal")) and
             isinstance(revision, str) and revision.startswith("SYNTHETIC-"),
             "SOURCE_IDENTITY")
        need(j.get("controller") in ("feature-delivery", "make-feature") and
             j.get("active_controllers") == [j.get("controller")], "DUP_CONTROLLER")
        reqs = j.get("requirements", [])
        acs = j.get("acceptance", [])
        r_ids = [r.get("id") for r in reqs]
        ac_ids = [a.get("id") for a in acs]
        need(bool(r_ids) and len(set(r_ids)) == len(r_ids) and
             set(r_ids) == set(j.get("original_r_ids", [])) and
             all(isinstance(r, str) and REQUIREMENT.fullmatch(r) for r in r_ids),
             "REQUIREMENT_LOST")
        need(bool(ac_ids) and len(set(ac_ids)) == len(ac_ids) and
             set(ac_ids) == set(j.get("original_ac_ids", [])) and
             all(isinstance(a, str) and CRITERION.fullmatch(a) for a in ac_ids),
             "AC_LOST")
        need(all(a.get("r_id") in r_ids for a in acs), "AC_PARENT_LOST")
        evidence = {e.get("id"): e for e in j.get("evidence", [])}
        need(len(evidence) == len(j.get("evidence", [])), "DUPLICATE_EVIDENCE")
        for e in evidence.values():
            need(e.get("level") in EVIDENCE_LEVELS, "UNKNOWN_EVIDENCE")
            need(e.get("source_revision") == revision, "WRONG_EVIDENCE_REVISION")
            need(_source_ok(e.get("artifact"), root), "MISSING_EVIDENCE")
            if e.get("level") in ("EXECUTED", "SYNTHETIC_TESTED", "INDEPENDENT_REVIEWED"):
                need(e.get("executed") is True and e.get("receipt") and e.get("observation"),
                     "EXECUTION_UNPROVEN")
            if e.get("level") == "INDEPENDENT_REVIEWED":
                need(e.get("independent") is True and
                     e.get("reviewer") not in (None, e.get("executor")),
                     "FAKE_REVIEW")

        trace = j.get("trace", [])
        need(len(trace) >= len(acs) and
             all(any(t.get("r_id") == a.get("r_id") and t.get("ac_id") == a.get("id")
                     for t in trace) for a in acs), "TRACEABILITY_LOST")
        need(all(t.get("r_id") in r_ids and t.get("ac_id") in ac_ids and
                 t.get("stage") in PHASES and t.get("deliverable") in PHASES
                 for t in trace), "TRACEABILITY_LOST")
        need(all(t.get("final_status") in STATUSES for t in trace), "UNKNOWN_STATUS")
        stage_rows = j.get("stages", [])
        need([s.get("id") for s in stage_rows] == list(PHASES), "MISSING_STAGE")
        for index, s in enumerate(stage_rows):
            need(s.get("source_revision") == revision, "WRONG_EVIDENCE_REVISION")
            need(set(s.get("r_ids", [])) == set(r_ids) and
                 set(s.get("ac_ids", [])) == set(ac_ids), "STAGE_TRACE_LOST")
            need(bool(s.get("deliverable")) and s.get("output") == s.get("id") and
                 s.get("input") == ("request" if index == 0 else PHASES[index - 1]),
                 "BROKEN_HANDOFF")
            if s.get("status") == "NOT_APPLICABLE":
                need(bool(s.get("skip_reason")), "UNJUSTIFIED_SKIP")
            elif s.get("status") not in ("PROPOSED", "COMPLETE"):
                errors.add("INVALID_STAGE_STATUS")
            if s.get("status") == "COMPLETE" and s.get("id") in ("implementation", "qa"):
                need(bool(j.get("receipts", {}).get(s.get("id"))), "FALSE_STAGE_COMPLETE")
        handoffs = j.get("handoffs", [])
        need(len(handoffs) == len(PHASES) - 1 and
             all(h.get("from") == PHASES[i] and h.get("to") == PHASES[i + 1]
                 for i, h in enumerate(handoffs)), "BROKEN_HANDOFF")
        for h in handoffs:
            need(h.get("source_revision") == revision, "WRONG_EVIDENCE_REVISION")
            need(set(h.get("r_ids", [])) == set(r_ids) and
                 set(h.get("ac_ids", [])) == set(ac_ids), "BROKEN_HANDOFF")
            need(h.get("source_artifact") == h.get("from") and
                 h.get("deliverable") == h.get("to"), "BROKEN_HANDOFF")
            if h.get("status") == "ACCEPTED":
                need(bool(h.get("receiver_ack")), "FALSE_HANDOFF_ACCEPTED")

        approved = set(j.get("scope", {}).get("approved", []))
        excluded = set(j.get("scope", {}).get("excluded", []))
        proposed = set(j.get("scope", {}).get("proposed_features", []))
        need(bool(approved) and proposed <= approved and not (proposed & excluded),
             "UNNECESSARY_EDITS")
        need(not j.get("scope", {}).get("unnecessary_edits"), "UNNECESSARY_EDITS")
        permissions = j.get("permissions", {})
        capabilities = j.get("capabilities", {})
        for action in j.get("actions", []):
            kind = action.get("kind")
            if kind == "TOOLKIT_WRITE" or permissions.get("toolkit_write"):
                errors.add("TOOLKIT_CONTAMINATION")
            if kind == "PAID_API":
                errors.add("OWNER_GATE_BYPASS")
            if kind == "WRITE" and not (permissions.get("write") and capabilities.get("file_write")):
                errors.add("UNAUTHORIZED_ACTION")
            if kind == "EXTERNAL" and not (permissions.get("external") and capabilities.get("external")):
                errors.add("UNAUTHORIZED_ACTION")
            if kind in ("PUBLISH", "DEPLOY") and not permissions.get(kind.lower()):
                errors.add("UNAUTHORIZED_ACTION")
            if kind not in ("READ", "WRITE", "EXTERNAL", "PUBLISH", "DEPLOY", "PAID_API", "TOOLKIT_WRITE"):
                errors.add("UNKNOWN_ACTION")
        tests = {t.get("id"): t for t in j.get("qa_tests", [])}
        need(bool(tests) and all(t.get("ac_id") in ac_ids for t in tests.values()) and
             all(t.get("test_ref") in tests for t in trace), "QA_TRACE_LOST")
        for t in tests.values():
            if t.get("status") == "PASS":
                ev = evidence.get(t.get("evidence_id"))
                need(t.get("executed") is True and ev is not None and
                     ev.get("executed") is True and ev.get("level") in
                     ("SYNTHETIC_TESTED", "EXECUTED", "INDEPENDENT_REVIEWED"),
                     "FALSE_TEST_PASS")
        for a in acs:
            need(a.get("status") in STATUSES, "UNKNOWN_STATUS")
            if a.get("status") == "PASS":
                ev = evidence.get(a.get("evidence_id"))
                need(ev is not None and ev.get("executed") is True and
                     ev.get("level") not in ("SOURCE_ONLY", "NOT_TESTED", "OWNER_REPORTED"),
                     "FALSE_AC_PASS")
        claims = j.get("claims", {})
        receipts = j.get("receipts", {})
        if claims.get("implemented"):
            need(permissions.get("write") and capabilities.get("file_write") and
                 bool(receipts.get("implementation")) and
                 bool(j.get("scope", {}).get("actual_changed_files")), "IMPLEMENTATION_UNPROVEN")
        if claims.get("qa_verified"):
            need(all(t.get("status") == "PASS" for t in tests.values()) and
                 bool(receipts.get("qa")), "FALSE_QA_VERIFIED")
        for state, prerequisite, receipt in (
            ("merged", None, "merge"), ("released", "merged", "release"),
            ("deployed", "released", "deployment"), ("user_verified", "deployed", "user")
        ):
            if claims.get(state):
                need(bool(receipts.get(receipt)) and
                     (prerequisite is None or claims.get(prerequisite)),
                     "FALSE_RELEASE_STATUS")
        if claims.get("skill_invoked"):
            need(capabilities.get("skill_discovered") and capabilities.get("skill_invoked")
                 and bool(receipts.get("invocation")), "FALSE_SKILL_ACTIVATION")
        if claims.get("model_effectiveness") is not None:
            errors.add("EFFECTIVENESS_UNPROVEN")
        independent = j.get("independent_usability", {})
        if independent.get("status") == "PASS" or claims.get("independent_reviewed"):
            need(bool(independent.get("session_id")) and
                 independent.get("reviewer_id") not in (None, independent.get("executor_id")) and
                 len(independent.get("timestamps", [])) >= 2 and
                 bool(receipts.get("independent_review")), "FAKE_NOVICE_SESSION")
        if independent.get("duration_seconds") is not None:
            need(len(independent.get("timestamps", [])) >= 2, "TIME_UNPROVEN")
        experiment = j.get("experiment", {})
        need(experiment.get("status") == "BLOCKED" and
             not experiment.get("owner_approval") and experiment.get("client_invocations") == 0,
             "OWNER_GATE_BYPASS")
        need(not experiment.get("baseline_skill_present"), "BASELINE_LEAKAGE")
        pairs = experiment.get("pairs", [])
        if pairs:
            need(all(p.get("baseline") and p.get("candidate") for p in pairs),
                 "MISSING_MATCHED_PAIR")
            need(len(set(experiment.get("model_versions", []))) <= 1,
                 "MIXED_MODELS")
            need(all(p.get("same_environment") for p in pairs),
                 "UNCONTROLLED_EXPERIMENT")
        measure = j.get("measurements", {})
        need(all(measure.get(m) is None for m in
                 ("usability_steps", "wall_time_seconds", "actual_cost_usd",
                  "model_quality_improvement")) or
             bool(independent.get("session_id")), "UNMEASURED_AS_MEASURED")
        if measure.get("model_quality_improvement") is not None:
            errors.add("EFFECTIVENESS_UNPROVEN")
        if experiment.get("actual_cost_usd") == 0 and not pairs:
            errors.add("FALSE_COST_ZERO")
        if (j.get("incidents", {}).get("regressions") and
                j.get("outcome") == "DONE"):
            errors.add("HIDDEN_REGRESSION")
        if j.get("outcome") == "DONE":
            need(claims.get("qa_verified") and claims.get("implemented") and
                 not j.get("incidents", {}).get("regressions"), "PREMATURE_DONE")

    owner = document.get("historical_owner_trials", {})
    need(owner.get("status") == "OWNER_REPORTED_PASS" and
         owner.get("independent_evidence") == "NOT_ATTACHED", "FAKE_INDEPENDENT_REVIEW")
    gate = document.get("skill_eval_gate", {})
    need(gate.get("status") == "BLOCKED" and gate.get("actual_live_runs") == 0
         and not gate.get("owner_approval") and
         gate.get("guard_file") == "scripts/agent_eval_runner.py", "OWNER_GATE_BYPASS")
    actions = document.get("owner_actions", {})
    need(not any(actions.values()), "UNAPPROVED_PUBLICATION")
    return sorted(errors)


def workflow_fixture(journey: dict) -> dict:
    """Adapt the pre-existing #67 oracle fixture, not a second workflow controller."""
    w = copy.deepcopy(workflow_load("reference.json"))
    rev = journey["source_revision"]
    rids, acids = journey["original_r_ids"], journey["original_ac_ids"]
    w.update(workflow_id=f"SYNTHETIC-70-{journey['id']}",
             source_request=journey["original_goal"], project_ref=journey["project_ref"],
             source_revision=rev, original_r_ids=rids, original_ac_ids=acids,
             controller=journey["controller"], active_controllers=journey["active_controllers"])
    w["requirements"] = [{"id": x["id"], "text": x["description"]}
                         for x in journey["requirements"]]
    w["acceptance"] = [{"id": x["id"], "r": x["r_id"], "text": x["criterion"]}
                       for x in journey["acceptance"]]
    w["trace"] = [{"r": x["r_id"], "ac": x["ac_id"], "decision": "D1",
                   "implementation": "SYNTHETIC-only", "test": x["test_ref"], "evidence": "E1"}
                  for x in journey["trace"]]
    w["artifacts"]["request"] = "SYNTHETIC " + journey["original_goal"]
    for s in journey["stages"]:
        w["artifacts"][s["id"]] = "SYNTHETIC " + s["deliverable"]
    for item in w["stages"]:
        item["source_revision"] = rev
        item["requirement_refs"] = list(rids)
        if item["id"] == "ux" and journey["id"] == "EXPERT":
            item["status"] = "NOT_APPLICABLE"
            item["skip_reason"] = "API-only import; no user-facing UI"
    w["tests"] = [{"id": t["id"], "ac": t["ac_id"], "status": "NOT_RUN",
                    "executed": False, "observed": None, "evidence": "E1"}
                  for t in journey["qa_tests"]]
    for h in w["handoffs"]:
        h["source_revision"] = rev
        h["r_ids"], h["ac_ids"] = list(rids), list(acids)
    w["scope"].update(approved=journey["scope"]["approved"],
                      excluded=journey["scope"]["excluded"],
                      implemented=[], optional=[])
    w["resume"]["previous_source_revision"] = rev
    w["resume"]["previous_head"] = rev
    w["resume"]["current_head"] = rev
    for stage in w["stages"]:
        if stage["id"] in ("implementation", "qa", "release"):
            stage["status"] = "PROPOSED"
    return w


def source_revision() -> str:
    try:
        result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                capture_output=True, text=True, timeout=5, check=False)
        value = result.stdout.strip()
        return value if result.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", value) else "UNKNOWN"
    except (OSError, subprocess.TimeoutExpired):
        return "UNKNOWN"


def report(document: dict) -> dict:
    failures = audit(document)
    if failures:
        raise AssertionError(f"Reference contract rejected: {failures}")
    journeys = {}
    for journey in document["journeys"]:
        issues = workflow_audit(workflow_fixture(journey))
        if issues:
            raise AssertionError(f"{journey['id']} existing E2E oracle: {issues}")
        journeys[journey["id"]] = "PASS: SYNTHETIC_CONTRACT_ONLY"
    negative = load("broken_cases.json")["cases"]
    for case in negative:
        altered = copy.deepcopy(document)
        for patch in case.get("patches", [case]):
            altered = mutate(altered, patch["path"], patch.get("value"),
                             delete=patch.get("delete", False))
        actual = audit(altered)
        if case["expected_error"] not in actual:
            raise AssertionError(f"{case['id']}: expected {case['expected_error']}, got {actual}")
    coverage = {}
    for stage in STAGES:
        counts: Counter[str] = Counter()
        for c in document["checks"]:
            if c["stage"] != stage:
                continue
            # A PASS below means only checked presence of a specific source, never its effect.
            result = "PASS" if c["method"] == "SOURCE_PRESENCE" else c["status"]
            counts[result] += 1
        coverage[stage] = {"total": sum(counts.values()), **{
            key: counts[key] for key in ("PASS", "FAIL", "BLOCKED",
                                         "NOT_TESTED", "NOT_APPLICABLE", "INCONCLUSIVE")}}
    return {
        "issue": "70", "source_revision": source_revision(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "offline_synthetic_only",
        "workflow_oracles": journeys, "negative_mutations_detected": len(negative),
        "coverage_source_presence_only": coverage,
        "independent_novice_usability": "NOT_TESTED",
        "live_skill_evals": "BLOCKED", "real_skill_invocation": "NOT_TESTED",
        "real_model_effectiveness": "NOT_MEASURED",
        "owner_reported_zip_trials": "OWNER_REPORTED_PASS",
        "technical_independent_evidence": "NOT_ATTACHED",
        "release_readiness": "READY_FOR_REVIEW",
        "actual_live_runs": 0, "external_connections_used": 0,
        "actual_additional_cost": "NOT_MEASURED",
        "limitations": "Source presence is not behavioral validation; CI checks reported separately."
    }


def main() -> int:
    try:
        print(json.dumps(report(load()), ensure_ascii=False, indent=2))
    except (AssertionError, KeyError, ValueError, TypeError) as exc:
        print(f"FAIL: final acceptance oracle: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
