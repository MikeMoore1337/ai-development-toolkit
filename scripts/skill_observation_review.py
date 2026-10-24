#!/usr/bin/env python3
"""Strict, offline review handoff for a *manually sanitized* Task Observer packet.

This is not an observer, a curator, a GitHub evidence verifier, or an installer.
No network, code execution, inference, or filesystem writes.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 32768
MAX_ITEMS = 20
ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z", re.ASCII)
SOURCE = re.compile(
    r"https://github\.com/[A-Za-z0-9-]{1,39}/[A-Za-z0-9_.-]{1,100}/"
    r"(?:issues/[1-9][0-9]*|pull/[1-9][0-9]*|actions/runs/[1-9][0-9]*|commit/[a-f0-9]{40})\Z",
    re.ASCII,
)
CATEGORIES = frozenset({
    "incorrect-routing", "missing-evidence", "redundant-step",
    "regression", "policy-conflict", "documentation-gap",
})
OBS_KEYS = frozenset({"observation_id", "skill_id", "category", "source_url"})


def review_packet(packet: object) -> dict:
    """Validate a limited handoff; never promote claimed evidence to verified."""
    if not isinstance(packet, dict) or set(packet) != {"schema_version", "observations"}:
        raise ValueError("INVALID_SCHEMA")
    if type(packet["schema_version"]) is not int or packet["schema_version"] != 1:
        raise ValueError("INVALID_VERSION")
    raw = packet["observations"]
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_ITEMS:
        raise ValueError("INVALID_COUNT")
    seen = set()
    rows = []
    for item in raw:
        if not isinstance(item, dict) or set(item) != OBS_KEYS:
            raise ValueError("INVALID_FIELDS")
        if any(not isinstance(item[key], str) for key in OBS_KEYS):
            raise ValueError("INVALID_TYPE")
        oid, skill = item["observation_id"], item["skill_id"]
        if not ID.fullmatch(oid) or not ID.fullmatch(skill):
            raise ValueError("INVALID_IDENTIFIER")
        if oid in seen:
            raise ValueError("DUPLICATE_ID")
        seen.add(oid)
        if item["category"] not in CATEGORIES:
            raise ValueError("INVALID_CATEGORY")
        if not SOURCE.fullmatch(item["source_url"]):
            raise ValueError("INVALID_SOURCE")
        rows.append({
            "observation_id": oid,
            "skill_id": skill,
            "category": item["category"],
            "source_url": item["source_url"],
            "evidence_verified": False,
            "disposition": "MANUAL_REVIEW_REQUIRED",
        })
    return {
        "schema_version": 1,
        "decision": "REVIEW_ONLY",
        "observer_executed": False,
        "curator_executed": False,
        "client_activation_verified": False,
        "items": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.input.is_symlink() or not args.input.is_file():
            raise ValueError("INVALID_FILE")
        with args.input.open("rb") as handle:
            data = handle.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise ValueError("TOO_LARGE")
        content = json.loads(data.decode("utf-8"))
        report = review_packet(content)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        # Reject without echoing untrusted data, paths, or raw prompt contents.
        code = str(exc) if isinstance(exc, ValueError) and str(exc) in {
            "INVALID_SCHEMA", "INVALID_VERSION", "INVALID_COUNT", "INVALID_FIELDS",
            "INVALID_TYPE", "INVALID_IDENTIFIER", "DUPLICATE_ID", "INVALID_CATEGORY",
            "INVALID_SOURCE", "INVALID_FILE", "TOO_LARGE",
        } else "INVALID_INPUT"
        print(json.dumps({"decision": "REJECT", "reason": code}, sort_keys=True))
        return 2
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
