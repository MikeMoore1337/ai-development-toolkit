#!/usr/bin/env python3
"""Issue #66: independent offline support evidence oracle; no external operations."""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "maintenance-support"
TYPES = {"USER_REPORTED", "SOURCE_BACKED", "OBSERVED", "SYNTHETIC_TESTED", "INFERRED", "UNKNOWN"}
MEASURED = {"SOURCE_BACKED", "OBSERVED", "SYNTHETIC_TESTED"}
CATEGORIES = {"DEFECT", "FEATURE_REQUEST", "HOW_TO", "CONFIGURATION",
              "ENVIRONMENT", "EXTERNAL_DEPENDENCY", "SERVICE_INCIDENT",
              "SECURITY_OR_PRIVACY", "DUPLICATE", "EXPECTED_BEHAVIOR", "UNKNOWN"}


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def mutate(case: dict, path: str, value: object) -> dict:
    result = copy.deepcopy(case)
    parts = path.split(".")
    obj = result
    for key in parts[:-1]:
        obj = obj[key]
    obj[parts[-1]] = value
    return result


def audit(case: dict) -> list[str]:
    """Check scoped evidence and state transitions independently of fixture creation."""
    bad: set[str] = set()
    def need(ok: bool, code: str) -> None:
        if not ok:
            bad.add(code)

    ev = case["evidence"]
    def has(value: object, types: set[str] = TYPES) -> bool:
        return isinstance(value, str) and value in ev and ev[value].get("source") in types

    r, du, rep, cause = (case[x] for x in ("report", "duplicate", "reproduction", "diagnosis"))
    hand, fix, dl = (case[x] for x in ("handoff", "fix", "delivery"))
    known, change, dep = (case[x] for x in ("known_issue", "changelog", "deprecation"))
    msg, end, acc, trace = (case[x] for x in ("message", "closure", "access", "trace"))

    need(bool(r.get("id") and r.get("source") and r.get("component")
              and r.get("symptom") and r.get("expected") and r.get("observed")
              and r.get("privacy") and r.get("next") and isinstance(r.get("missing"), list)),
         "INTAKE_MISSING")
    need(has(r.get("evidence")), "EVIDENCE_MISSING")
    need(r.get("category") in CATEGORIES and bool(r.get("basis")) and
         (r.get("kind") == "FAULT" or r.get("category") != "DEFECT"),
         "BAD_CLASSIFICATION")
    need(not r.get("version") or has(r.get("version_evidence"), MEASURED),
         "VERSION_UNVERIFIED")
    need(not r.get("conflict") or len(r.get("reports", [])) >= 2, "CONFLICT_LOST")
    need(du.get("state") in {"SIMILAR", "POSSIBLE", "CONFIRMED", "INDEPENDENT"},
         "DUPLICATE_INVALID")
    if du.get("state") == "CONFIRMED":
        need(du.get("same_cause") is True and has(du.get("evidence"), MEASURED),
             "FALSE_DUPLICATE")
    need(rep.get("report") == hand.get("report") == msg.get("report") ==
         trace.get("report") == r.get("id") and hand.get("issue") ==
         known.get("issue") == change.get("issue") == trace.get("issue"),
         "TRACE_LOST")
    need(rep.get("status") in {"REPRODUCED", "NOT_REPRODUCED", "NOT_ATTEMPTED",
         "INTERMITTENT", "ENVIRONMENT_BLOCKED", "INSUFFICIENT_DATA", "NOT_APPLICABLE"},
         "REPRODUCTION_STATUS")
    if rep.get("status") in {"REPRODUCED", "NOT_REPRODUCED", "INTERMITTENT"}:
        need(type(rep.get("attempts")) is int and rep["attempts"] > 0
             and bool(rep.get("steps")) and bool(rep.get("expected"))
             and bool(rep.get("actual")) and has(rep.get("evidence"), MEASURED),
             "FAKE_REPRODUCTION")
    if cause.get("confidence") == "CONFIRMED":
        need(bool(cause.get("cause")) and bool(cause.get("alternatives"))
             and has(cause.get("evidence"), MEASURED), "FAKE_RCA")
    need(bool(hand.get("acceptance")) and all(isinstance(s, str) and s.strip()
         for s in hand.get("acceptance", [])), "HANDOFF_NO_AC")
    need(fix.get("status") in {"NONE", "FIX_PROPOSED", "FIX_IMPLEMENTED",
         "TESTS_NOT_RUN", "VERIFIED_PASS", "VERIFIED_FAIL", "BLOCKED", "INCONCLUSIVE"},
         "FIX_STATUS")
    if fix.get("status") in {"FIX_IMPLEMENTED", "VERIFIED_PASS", "VERIFIED_FAIL"}:
        need(bool(fix.get("commit")) and bool(fix.get("pr"))
             and has(fix.get("code_evidence"), MEASURED), "FIX_NOT_IMPLEMENTED")
    if fix.get("status") == "VERIFIED_PASS":
        need(fix.get("test_status") == "PASS" and
             has(fix.get("test_evidence"), {"SYNTHETIC_TESTED", "OBSERVED"}),
             "QA_NOT_VERIFIED")
    need(fix.get("pr") == trace.get("pr") == change.get("pr") and
         fix.get("commit") == trace.get("commit"), "TRACE_LOST")
    if dl.get("merged"):
        need(bool(fix.get("commit")) and has(dl.get("merge_evidence"), MEASURED),
             "MERGE_UNVERIFIED")
    if dl.get("published"):
        need(dl.get("merged") and bool(dl.get("version")) and
             has(dl.get("release_evidence"), MEASURED), "RELEASE_UNVERIFIED")
    need(dl.get("version") == trace.get("version"), "VERSION_MAPPING")
    if dl.get("deployed"):
        need(dl.get("published") and bool(dl.get("channel")) and
             bool(dl.get("environment")) and has(dl.get("deploy_evidence"), MEASURED),
             "DEPLOY_UNVERIFIED")
        need(dl.get("deployed_version") == dl.get("version"), "DEPLOY_VERSION_MISMATCH")
    if dl.get("user_verified"):
        need(dl.get("deployed") and dl.get("user_version") == dl.get("deployed_version")
             and dl.get("user_environment") == dl.get("environment")
             and has(dl.get("user_evidence"), {"USER_REPORTED", "OBSERVED"}),
             "USER_NOT_VERIFIED")
    if dl.get("rollback"):
        need(not dl.get("deployed") and has(dl.get("rollback_evidence"), MEASURED),
             "ROLLBACK_INVALID")
    if known.get("status") == "CLOSED":
        need(dl.get("user_verified") and not dl.get("rollback"), "KNOWN_ISSUE_PREMATURE")
    if known.get("workaround"):
        need(known.get("workaround_checked") and
             has(known.get("workaround_evidence"), MEASURED), "WORKAROUND_UNTESTED")
    if change.get("state") == "PUBLISHED":
        need(dl.get("published") and change.get("version") == dl.get("version") and
             has(change.get("evidence"), MEASURED), "CHANGELOG_MISMATCH")
    if dep.get("state") in {"ANNOUNCED", "DEPRECATED", "MIGRATION_AVAILABLE",
                            "REMOVAL_APPROVED", "REMOVED", "VERIFIED"}:
        need(dep.get("approved") and has(dep.get("approval_evidence"), MEASURED)
             and (not dep.get("requires_notice") or
                  has(dep.get("notice_evidence"), MEASURED)), "DEPRECATION_UNAPPROVED")
    if msg.get("status") in {"SENT", "DELIVERY_CONFIRMED"}:
        need(msg.get("approved") and has(msg.get("send_evidence"), MEASURED),
             "UNAUTHORIZED_SEND")
    need(not msg.get("deadline") or msg.get("deadline_approved"), "UNAPPROVED_DEADLINE")
    if msg.get("data_safe_claim"):
        need(has(msg.get("data_evidence"), MEASURED), "DATA_SAFETY_UNVERIFIED")
    need(not re.search(r"(?i)(?:token|password|cookie)\s*[:=]\s*\S+|"
                       r"Bearer\s+\S+|[\w.+-]+@[\w.-]+\.[a-z]{2,}", msg.get("text", "")),
         "SENSITIVE_CONTENT")
    claims = {"RECEIVED": bool(r.get("id")),
              "REPRODUCED": rep.get("status") == "REPRODUCED",
              "NOT_REPRODUCED": rep.get("status") == "NOT_REPRODUCED",
              "FIX_TESTED": fix.get("status") == "VERIFIED_PASS",
              "PUBLISHED": bool(dl.get("published")),
              "CHANNEL_DEPLOYED": bool(dl.get("deployed")) and not dl.get("rollback"),
              "ROLLED_BACK": bool(dl.get("rollback")),
              "USER_VERIFIED": bool(dl.get("user_verified"))}
    need(claims.get(msg.get("claim"), False), "CUSTOMER_CLAIM_UNSUPPORTED")
    if end.get("status") == "CLOSED":
        resolved = end.get("reason") == "VERIFIED_FOR_USER" and dl.get("user_verified") and has(end.get("evidence"))
        duplicate = end.get("reason") == "CONFIRMED_DUPLICATE" and du.get("state") == "CONFIRMED"
        need(resolved or duplicate, "FALSE_CLOSURE")
    if acc.get("claimed_observation"):
        need(acc.get("production") and
             has(acc.get("observation_evidence"), {"OBSERVED", "SOURCE_BACKED"}),
             "ACCESS_UNVERIFIED")
    return sorted(bad)


def validate() -> tuple[int, int]:
    valid = ("reference", "pre_release", "unreproduced", "rollback", "user_verified")
    for name in valid:
        errors = audit(load(name + ".json"))
        if errors:
            raise AssertionError(f"{name}: {errors}")
    original = load("reference.json")
    cases = load("broken_cases.json")["cases"]
    for c in cases:
        errors = audit(mutate(original, c["path"], c["value"]))
        if c["expected_error"] not in errors:
            raise AssertionError(f"{c['id']}: {c['expected_error']} absent from {errors}")
    return len(valid), len(cases)


if __name__ == "__main__":
    good, bad = validate()
    print(f"PASS: {good} synthetic references, {bad} rejected broken records")
