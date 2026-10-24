#!/usr/bin/env python3
"""Validate scoped real-client evidence without invoking clients or exposing secrets.

This validator checks provenance and logical consistency, not the historical
truth of owner statements. Never turn an offline CI pass into a new L4/L5 result.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "compatibility/live_client_evidence.json"
SHA = re.compile(r"^[0-9a-f]{40}$")
ROLES = {
    "chatgpt-personal-plugin-session": (
        "ASSISTANT_OBSERVED_CURRENT_SESSION", "OBSERVED_THIS_SESSION",
        "READ_THIS_SESSION", "0.1.8"
    ),
    "codex-personal-mcp-owner-20261023": (
        "HISTORICAL_OWNER_REPORTED_FROM_ISSUE_190", "OWNER_REPORTED_PASS",
        "OWNER_REPORTED_GUIDANCE_RETURNED", "0.1.10"
    ),
    "codex-project-mcp": ("SOURCE_ONLY_NO_HOST_SESSION", "NOT_RUN", "NOT_RUN",
                          "SOURCE_SCRIPT_NO_PACKAGE_VERSION"),
    "claude-code-project-mcp": ("SOURCE_ONLY_NO_HOST_SESSION", "NOT_RUN", "NOT_RUN",
                                "SOURCE_SCRIPT_NO_PACKAGE_VERSION"),
}
FIELDS = frozenset((
    "id", "client", "mode", "client_version", "adapter_version",
    "toolkit_version", "source_sha", "observation_date", "evidence_origin",
    "l4", "l5_guidance", "l5_native_skill_activation", "l6_benefit",
    "target_execution", "project_files_changed", "cost", "evidence", "limitations"
))


class EvidenceError(ValueError):
    pass


def _check(condition: bool, reason: str) -> None:
    if not condition:
        raise EvidenceError(reason)


def validate(payload: object) -> dict:
    _check(isinstance(payload, dict), "Root must be object")
    _check(set(payload) == {
        "schema_version", "description", "review_date", "collection",
        "current_source_sha", "zero_spend_gate", "scenarios"
    }, "Unexpected registry fields")
    _check(payload["schema_version"] == 1, "Unsupported evidence schema")
    _check(payload["collection"] ==
           "OBSERVED_CURRENT_AND_HISTORICAL_WITH_EXPLICIT_PROVENANCE",
           "Evidence provenance contract mismatch")
    _check(payload["zero_spend_gate"] == "ACTIVE_ISSUE_11_NOT_PLANNED",
           "Zero-spend gate may not be removed")
    _check(isinstance(payload["description"], str) and payload["description"],
           "Description missing")
    _check(payload["review_date"] == "2026-10-24", "Review date drift")
    _check(isinstance(payload["current_source_sha"], str) and
           SHA.fullmatch(payload["current_source_sha"]) is not None,
           "Unpinned source SHA")
    items = payload["scenarios"]
    _check(isinstance(items, list) and len(items) == len(ROLES),
           "Expected four distinct scoped scenarios")
    seen: set[str] = set()
    for row in items:
        _check(isinstance(row, dict) and set(row) == FIELDS, "Bad scenario fields")
        ident = row["id"]
        _check(isinstance(ident, str) and ident in ROLES and ident not in seen,
               "Unknown or duplicate scenario")
        seen.add(ident)
        origin, l4, l5, version = ROLES[ident]
        _check((row["evidence_origin"], row["l4"], row["l5_guidance"],
                row["adapter_version"]) == (origin, l4, l5, version),
               "Unsupported L4/L5 promotion or adapter version")
        _check(row["l5_native_skill_activation"] == "NOT_OBSERVED",
               "No native skill activation evidence")
        _check(row["l6_benefit"] == "NOT_MEASURED",
               "No controlled task benefit evidence")
        _check(row["target_execution"] == "NOT_RUN" and
               row["project_files_changed"] is False,
               "No user project execution or modifications were authorized")
        _check(isinstance(row["source_sha"], str) and
               SHA.fullmatch(row["source_sha"]) is not None,
               "Scenario must pin exact source revision")
        _check(isinstance(row["evidence"], list) and row["evidence"] and
               all(isinstance(e, str) and 1 <= len(e) <= 600 for e in row["evidence"]),
               "Bounded evidence required")
        _check(isinstance(row["limitations"], str) and row["limitations"],
               "Missing scope limitations")
        for fld in ("client", "mode", "client_version", "toolkit_version",
                    "observation_date", "cost"):
            _check(isinstance(row[fld], str) and row[fld], "Missing " + fld)
        if origin == "HISTORICAL_OWNER_REPORTED_FROM_ISSUE_190":
            _check(any("issues/190#issuecomment-6363045693" in item
                       for item in row["evidence"]),
                   "Codex owner assertion needs precise issue evidence")
            _check(row["toolkit_version"] == "5.5.3",
                   "Old Codex observation is not Toolkit v5.5.5")
        elif origin == "SOURCE_ONLY_NO_HOST_SESSION":
            _check(row["source_sha"] == payload["current_source_sha"],
                   "Project MCP source SHA mismatch")
        else:
            _check(row["source_sha"] == payload["current_source_sha"],
                   "ChatGPT loaded source SHA mismatch")
            _check(row["toolkit_version"] == "5.5.5",
                   "Current ChatGPT manifest version mismatch")
    _check(seen == set(ROLES), "Incomplete evidence set")
    return {
        "classification": "scoped_client_evidence_not_universal_compatibility",
        "scenarios": len(items),
        "current_observed": 1,
        "historical_owner_reported": 1,
        "not_run": 2,
        "native_activation": "NOT_OBSERVED",
        "benefit": "NOT_MEASURED",
        "zero_spend": True,
        "source": payload["current_source_sha"],
        "read_only": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--file", type=Path, default=DEFAULT)
    args = parser.parse_args(argv)
    try:
        report = validate(json.loads(args.file.read_text(encoding="utf-8")))
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
