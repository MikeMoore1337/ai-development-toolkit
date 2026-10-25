#!/usr/bin/env python3
"""Offline, advisory-only gate for a concrete consumer UI-component adoption proposal.

No network, package installation, files written or UI changes. Not a substitute for
the consumer project's design approval, browser tests or release rules.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT_KEYS = frozenset({
    "schema_version", "candidate", "source", "decision", "consumer_revision",
    "observed_problem", "reuse_evidence", "license", "source_revision",
    "new_dependencies", "performance", "accessibility", "reduced_motion",
    "visual_evidence", "owner_approval", "tests", "remote_services",
})
DECISIONS = frozenset({"REUSE_EXISTING", "PROPOSAL_ONLY", "IMPLEMENT_APPROVED"})
SOURCES = frozenset({"shadcn-ui/ui", "magicuidesign/magicui", "native_or_existing"})
SHA = re.compile(r"[a-f0-9]{40}\Z")


def validate(payload: object) -> list[str]:
    if not isinstance(payload, dict) or set(payload) != ROOT_KEYS:
        return ["INVALID_SCHEMA"]
    if payload.get("schema_version") != 1 or isinstance(payload.get("schema_version"), bool):
        return ["INVALID_VERSION"]

    errors: list[str] = []
    candidate = payload["candidate"]
    if not isinstance(candidate, str) or not candidate.strip() or len(candidate) > 128:
        errors.append("INVALID_CANDIDATE")
    if (not isinstance(payload["source"], str) or payload["source"] not in SOURCES
            or not isinstance(payload["decision"], str) or payload["decision"] not in DECISIONS):
        errors.append("INVALID_DECISION_OR_SOURCE")
    if not isinstance(payload["observed_problem"], str) or not payload["observed_problem"].strip():
        errors.append("MISSING_PROBLEM")
    if not isinstance(payload["reuse_evidence"], str) or not payload["reuse_evidence"].strip():
        errors.append("MISSING_REUSE_COMPARISON")
    if payload["remote_services"] not in ([], None):
        errors.append("NO_REMOTE_SERVICES_ALLOWED")

    dependencies = payload["new_dependencies"]
    if not isinstance(dependencies, list) or len(dependencies) > 10 or any(
        not isinstance(item, str) or not item.strip() or len(item) > 100 for item in dependencies
    ):
        errors.append("INVALID_DEPENDENCIES")
        dependencies = []

    revision = payload["consumer_revision"]
    if payload["decision"] == "IMPLEMENT_APPROVED":
        if not isinstance(revision, str) or not SHA.fullmatch(revision):
            errors.append("EXACT_CONSUMER_SHA_REQUIRED")

    if payload["source"] != "native_or_existing":
        if payload["license"] not in ("MIT_REVIEWED", "OTHER_REVIEWED"):
            errors.append("LICENSE_NOT_REVIEWED")
        source_revision = payload["source_revision"]
        if not isinstance(source_revision, str) or not SHA.fullmatch(source_revision):
            errors.append("UPSTREAM_PIN_REQUIRED")
    elif payload["license"] not in ("NATIVE", "LOCAL_REVIEWED"):
        errors.append("INVALID_LOCAL_LICENSE")

    perf = payload["performance"]
    if not isinstance(perf, dict) or set(perf) != {"status", "before_bytes", "after_bytes"}:
        errors.append("INVALID_PERFORMANCE")
    elif payload["decision"] == "IMPLEMENT_APPROVED" and dependencies:
        if (
            perf.get("status") != "MEASURED"
            or not isinstance(perf["before_bytes"], int)
            or isinstance(perf["before_bytes"], bool)
            or not isinstance(perf["after_bytes"], int)
            or isinstance(perf["after_bytes"], bool)
            or perf["before_bytes"] < 0
            or perf["after_bytes"] < 0
        ):
            errors.append("MEASURED_BUNDLE_COST_REQUIRED")

    if payload["decision"] == "IMPLEMENT_APPROVED":
        if payload["accessibility"] != "TESTED":
            errors.append("ACCESSIBILITY_NOT_TESTED")
        if payload["reduced_motion"] != "TESTED":
            errors.append("MOTION_NOT_TESTED")
        if not isinstance(payload["visual_evidence"], list) or not payload["visual_evidence"] or any(
            not isinstance(v, str) or not v.strip() for v in payload["visual_evidence"]
        ):
            errors.append("VISUAL_EVIDENCE_MISSING")
        approval = payload["owner_approval"]
        if not isinstance(approval, dict) or approval.get("status") != "OWNER_ACCEPTED" or not (
            isinstance(approval.get("evidence_ref"), str) and approval["evidence_ref"].strip()
        ):
            errors.append("OWNER_VISUAL_GATE_MISSING")
        if payload["tests"] != "PASS_EXACT_SHA":
            errors.append("ACTUAL_TEST_EVIDENCE_REQUIRED")
    else:
        # Proposal-only and reuse decisions must never masquerade as implemented/approved.
        if payload["tests"] == "PASS_EXACT_SHA":
            errors.append("PREMATURE_IMPLEMENTATION_CLAIM")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Local, manually prepared JSON evidence packet")
    args = parser.parse_args(argv)
    try:
        if args.input.is_symlink() or not args.input.is_file() or args.input.stat().st_size > 32_768:
            raise ValueError("invalid, symlinked or oversized input")
        packet = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"INVALID_INPUT: {exc}", file=sys.stderr)
        return 2
    problems = validate(packet)
    if problems:
        print(json.dumps({"status": "REJECTED", "issues": problems}, ensure_ascii=False))
        return 2
    print(json.dumps({"status": "STRUCTURAL_PASS_ONLY", "implementation_verified": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
