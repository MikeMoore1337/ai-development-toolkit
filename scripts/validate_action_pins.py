#!/usr/bin/env python3
"""Offline integrity gate for approved GitHub Actions references.

Commit SHA pins are source identity, not code audit or cryptographic signing.
Update the allowlist only after verifying exact official repository tag objects.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PINS = {
    "actions/checkout": {
        "3d3c42e5aac5ba805825da76410c181273ba90b1",  # v7 at 2026-10-24
        "11d5960a326750d5838078e36cf38b85af677262",  # v4
    },
    "actions/setup-python": {
        "6d4fd22b20465ccc0f7354476588e8df7c9ca0e0",  # v7
        "a26af69be951a213d495a4c3e4e4022e16d87065",  # v5
    },
    "actions/upload-artifact": {
        "ea165f8d65b6e75b540449e92b4886f43607fa02",  # v4
    },
}
USE = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
SHA = re.compile(r"[a-f0-9]{40}\Z")


def validate_text(text: str, name: str) -> tuple[list[str], int]:
    """No network, no execution; check every external uses reference."""
    errors: list[str] = []
    count = 0
    for match in USE.finditer(text):
        reference = match.group(1)
        if reference.startswith("./"):
            continue  # Local actions are committed with the parent checkout.
        count += 1
        action, separator, revision = reference.partition("@")
        if not separator or not SHA.fullmatch(revision):
            errors.append(f"{name}: UNPINNED_ACTION: {reference}")
        elif action not in PINS or revision not in PINS[action]:
            errors.append(f"{name}: UNREVIEWED_ACTION_SHA: {reference}")
    return errors, count


def validate_directory(folder: Path) -> tuple[list[str], int]:
    if not folder.is_dir():
        return ["WORKFLOWS_MISSING"], 0
    paths = sorted([*folder.glob("*.yml"), *folder.glob("*.yaml")])
    if not paths:
        return ["WORKFLOWS_EMPTY"], 0
    errors: list[str] = []
    count = 0
    for path in paths:
        issues, checked = validate_text(path.read_text(encoding="utf-8"), path.name)
        errors.extend(issues)
        count += checked
    if count == 0:
        errors.append("NO_EXTERNAL_ACTION_REFERENCES")
    return errors, count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    errors, total = validate_directory(args.root / ".github" / "workflows")
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print(f"PASS: {total} external action references match reviewed exact SHAs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
