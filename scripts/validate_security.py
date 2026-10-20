#!/usr/bin/env python3
"""Issue #60: deterministic, entirely offline Security Engineering examples.

No sockets, external targets, credentials, services, scanners or file writes.
Failures are reported only as defect identifiers; never print synthetic secrets.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import PurePosixPath

RISK_STATUSES = frozenset({
    "HYPOTHETICAL", "POTENTIAL", "CONFIRMED", "MITIGATED",
    "NOT_VERIFIED", "NOT_APPLICABLE",
})
EVIDENCE = frozenset({
    "NOT_TESTED", "SOURCE_ONLY", "STATIC_VALIDATED",
    "SYNTHETIC_TESTED", "REAL_TESTED", "HUMAN_REVIEWED",
})
THREAT_FIELDS = (
    "threat_id", "source", "component", "asset", "actor", "trust_boundary",
    "entry_point", "scenario", "preconditions", "potential_impact",
    "existing_controls", "proposed_controls", "verification_method",
    "related_requirement", "risk_status", "evidence", "residual_risk",
    "required_decision",
)
CONTROL_FIELDS = (
    "control_id", "source", "threat_id", "protected_asset", "trust_boundary",
    "invariant", "expected_allow", "expected_deny", "forbidden_side_effects",
    "level", "scenario", "actual_evidence", "status", "limitations",
    "responsible_decision", "residual_risk",
)
RISK_FIELDS = (
    "risk_id", "threat_id", "description", "source", "asset", "preconditions",
    "impact", "likelihood", "detectability", "priority", "confirmed_controls",
    "missing_controls", "owner", "fix_plan", "fix_verification",
    "residual_risk", "required_permissions",
)
FAKE_SECRET = "DEMO_PLACEHOLDER_NOT_A_CREDENTIAL"
ASSET = "fictional tenant-owned notes"
BOUNDARY = "fictional client -> in-process notes service"


def validate_packet(packet: dict) -> None:
    """Reject malformed or inflated threat/control/verification assertions."""
    if not isinstance(packet, dict) or any(
        not isinstance(packet.get(name), list) or not packet[name]
        for name in ("threats", "risks", "controls")
    ):
        raise ValueError("missing risk, control or threat register")
    threats: set[str] = set()
    for entry in packet["threats"]:
        require(entry, THREAT_FIELDS)
        if entry["threat_id"] in threats:
            raise ValueError("duplicate threat")
        threats.add(entry["threat_id"])
        if entry["risk_status"] not in RISK_STATUSES:
            raise ValueError("unknown threat status")
        if entry["risk_status"] == "MITIGATED" and not entry["evidence"]:
            raise ValueError("unproved mitigation")
    risks: set[str] = set()
    for entry in packet["risks"]:
        require(entry, RISK_FIELDS)
        if entry["risk_id"] in risks or entry["threat_id"] not in threats:
            raise ValueError("invalid risk linkage")
        risks.add(entry["risk_id"])
    controls: set[str] = set()
    for entry in packet["controls"]:
        require(entry, CONTROL_FIELDS)
        if entry["control_id"] in controls or entry["threat_id"] not in threats:
            raise ValueError("invalid control linkage")
        controls.add(entry["control_id"])
        if entry["status"] not in {"PASS", "FAIL", "NOT_TESTED"}:
            raise ValueError("invalid execution status")
        if entry["status"] == "PASS" and not entry["actual_evidence"]:
            raise ValueError("PASS without actual evidence")
        if entry["status"] == "NOT_TESTED" and entry["actual_evidence"]:
            raise ValueError("unexecuted verification has evidence")
    if not all(any(r["threat_id"] == t for r in packet["risks"]) for t in threats):
        raise ValueError("unregistered threat risk")
    if not all(any(c["threat_id"] == t for c in packet["controls"]) for t in threats):
        raise ValueError("uncontrolled threat")


def require(item: object, fields: tuple[str, ...]) -> None:
    if not isinstance(item, dict):
        raise ValueError("entry must be object")
    for field in fields:
        value = item.get(field)
        if value is None or value == "" or value == []:
            raise ValueError("missing " + field)


def sample_packet() -> dict:
    threat = dict.fromkeys(THREAT_FIELDS, "UNKNOWN")
    threat.update(
        threat_id="TH-01", source="synthetic model", component="notes",
        asset=ASSET, actor="user-A", trust_boundary=BOUNDARY,
        entry_point="read(note-id)", scenario="cross-tenant read",
        preconditions="valid user-A session and foreign ID",
        potential_impact="disclosure", existing_controls="server-side ownership",
        proposed_controls="deny before accessing foreign note",
        verification_method="isolated in-process negative oracle",
        related_requirement="REQ-ACCESS-1", risk_status="HYPOTHETICAL",
        evidence="synthetic model only", residual_risk="real system NOT_TESTED",
        required_decision="owner to authorize real-system verification",
    )
    risk = dict.fromkeys(RISK_FIELDS, "UNKNOWN")
    risk.update(
        risk_id="R-01", threat_id="TH-01", description="cross-tenant exposure",
        source="synthetic model", asset=ASSET, preconditions="other tenant ID",
        impact="confidentiality", likelihood="UNKNOWN", detectability="UNKNOWN",
        priority="REVIEW", confirmed_controls="reference model only",
        missing_controls="real-system evidence", owner="UNKNOWN",
        fix_plan="enforce trusted ownership", fix_verification="both ALLOW/DENY",
        residual_risk="NOT_VERIFIED", required_permissions="local synthetic only",
    )
    control = dict.fromkeys(CONTROL_FIELDS, "UNKNOWN")
    control.update(
        control_id="C-01", source="synthetic model", threat_id="TH-01",
        protected_asset=ASSET, trust_boundary=BOUNDARY,
        invariant="user-A cannot read tenant-B note",
        expected_allow="user-A reads own tenant-A note",
        expected_deny="user-A cannot read tenant-B note",
        forbidden_side_effects="no state modification",
        level="in-process synthetic", scenario="owner vs foreign note",
        actual_evidence="offline oracle on reference model",
        status="PASS", limitations="not tested on production",
        responsible_decision="owner", residual_risk="NOT_VERIFIED",
    )
    return {"threats": [threat], "risks": [risk], "controls": [control]}


def _owned(actor: str, note: dict, *, session: bool) -> bool:
    return session and actor == note["user"] and (
        ("user-A", "tenant-A") if actor == "user-A"
        else ("user-B", "tenant-B")
    ) == (note["user"], note["tenant"])


def note_operation(actor: str, note: dict, action: str, *,
                   session: bool = True, client_owner: str | None = None,
                   defect: str | None = None) -> dict:
    """In-memory reference plus explicitly faulty variants; no persistence."""
    current = dict(note)
    authorized = _owned(actor, note, session=session)
    if defect == "cross-tenant" and action == "read":
        authorized = session
    if defect == "client-owner" and client_owner is not None:
        authorized = session and client_owner == note["user"]
    if action not in {"read", "update", "delete"}:
        authorized = False
    response = "ALLOW" if authorized else "DENY"
    if authorized and action == "update":
        current["body"] = "updated"
    if authorized and action == "delete":
        current["deleted"] = True
    if defect == "write-before-deny" and action == "update" and not authorized:
        current["body"] = "unauthorized-change"
    return {"response": response, "before": dict(note), "after": current,
            "data": note["body"] if authorized and action == "read" else None}


def redacted(message: str, *, defect: str | None = None) -> str:
    return message if defect == "log-secret" else message.replace(FAKE_SECRET, "[REDACTED]")


def tool_scope(path: str, *, defect: str | None = None) -> bool:
    """Reject untrusted paths outside a bounded fictional workspace."""
    p = PurePosixPath(path)
    if defect == "tool-escape":
        return path.startswith("/workspace/")
    return p.is_absolute() and ".." not in p.parts and len(p.parts) > 2 and p.parts[1] == "workspace" and p.parts[2] == "notes"


def irreversible(approved: bool, *, defect: str | None = None) -> bool:
    return approved or defect == "no-approval"


def ci_policy(config: dict, *, defect: str | None = None) -> bool:
    """Synthetic CI contract; no YAML parser or live workflow execution."""
    if defect == "ci-write":
        return True
    return not (config["fork_pr"] and (
        config["permissions"] != "contents:read" or config["secrets"]
        or config["unsafe_checkout"] or config["shell_interpolation"]
    ))


def component_verified(component: dict, *, defect: str | None = None) -> bool:
    if defect == "fake-provenance":
        return component["claimed_verified"]
    return bool(component["publisher_verified"] and component["origin_verified"]
                and component["license_checked"])


def matches_integrity(content: bytes, expected: str, *,
                      defect: str | None = None) -> bool:
    if defect == "skip-hash":
        return True
    return hashlib.sha256(content).hexdigest() == expected


def safe_report(text: str, *, defect: str | None = None) -> bool:
    if defect == "sensitive-output":
        return True
    return FAKE_SECRET not in text


CASES = (
    "cross-tenant", "client-owner", "write-before-deny", "log-secret",
    "tool-escape", "no-approval", "ci-write", "fake-provenance",
    "skip-hash", "sensitive-output",
)


def observation(case: str, broken: bool = False) -> object:
    if case not in CASES:
        raise ValueError("unknown synthetic case")
    defect = case if broken else None
    foreign = {"user": "user-B", "tenant": "tenant-B",
               "body": "fictional-b-note"}
    if case in {"cross-tenant", "client-owner", "write-before-deny"}:
        action = "update" if case == "write-before-deny" else "read"
        return note_operation("user-A", foreign, action,
                              client_owner="user-B", defect=defect)
    if case == "log-secret":
        return redacted("LOG: " + FAKE_SECRET, defect=defect)
    if case == "tool-escape":
        return tool_scope("/workspace/notes/../private", defect=defect)
    if case == "no-approval":
        return irreversible(False, defect=defect)
    if case == "ci-write":
        return ci_policy({"fork_pr": True, "permissions": "contents:write",
                          "secrets": False, "unsafe_checkout": False,
                          "shell_interpolation": False}, defect=defect)
    if case == "fake-provenance":
        return component_verified({
            "claimed_verified": True, "publisher_verified": False,
            "origin_verified": False, "license_checked": False,
        }, defect=defect)
    if case == "skip-hash":
        return matches_integrity(b"fixture-B",
                                 hashlib.sha256(b"fixture-A").hexdigest(),
                                 defect=defect)
    if case == "sensitive-output":
        return safe_report("report: " + FAKE_SECRET, defect=defect)
    raise AssertionError("unreachable")


def oracle(case: str, observed: object) -> bool:
    """Independent contract oracle, not delegated to implementation functions."""
    if case in {"cross-tenant", "client-owner", "write-before-deny"}:
        if not isinstance(observed, dict):
            return False
        return (observed.get("response") == "DENY"
                and observed.get("before") == observed.get("after")
                and observed.get("data") is None)
    if case == "log-secret":
        return isinstance(observed, str) and FAKE_SECRET not in observed
    return observed is False


def run_cases() -> dict:
    validate_packet(sample_packet())
    correct = {case: oracle(case, observation(case)) for case in CASES}
    mutants_rejected = {case: not oracle(case, observation(case, True)) for case in CASES}
    if not all(correct.values()) or not all(mutants_rejected.values()):
        raise AssertionError("reference failure or false-green security oracle")
    return {
        "scope": "SYNTHETIC_TESTED", "real_assessment": "NOT_MEASURED",
        "cases": len(CASES), "reference_pass": sum(correct.values()),
        "mutants_rejected": sum(mutants_rejected.values()),
        "external_scans": "NOT_RUN", "production_tests": "NOT_RUN",
    }


if __name__ == "__main__":
    print(json.dumps(run_cases(), sort_keys=True))
