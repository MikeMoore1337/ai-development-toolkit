#!/usr/bin/env python3
"""Report stale RU/EN translated documentation without blocking unrelated changes.

Only explicit, safe, repository-local source/translation pairs are accepted.
This checks revision age, not translation meaning, skill activation, or rights.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISIONS = Path("docs/ru/SOURCE_REVISIONS.json")
CHECKSUM = re.compile(r"^[0-9a-f]{64}$")
SOURCE_PATH = re.compile(r"^docs/[A-Z_]+\.md$")


def check(root: Path = ROOT) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    root = root.resolve()
    try:
        info = json.loads((root / REVISIONS).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"L10N007: cannot read source revision metadata ({type(exc).__name__})"], []

    if (not isinstance(info, dict) or info.get("schema_version") != 1
            or not isinstance(info.get("pairs"), list) or not info["pairs"]):
        return ["L10N007: invalid source revision metadata"], []

    seen: set[str] = set()
    destinations: set[str] = set()
    for entry in info["pairs"]:
        if not isinstance(entry, dict):
            errors.append("L10N007: invalid revision entry")
            continue
        source = entry.get("source")
        translated = entry.get("translation")
        expected = entry.get("source_sha256")
        if (not isinstance(source, str) or not SOURCE_PATH.fullmatch(source)
                or translated not in (source.replace("docs/", "docs/ru/", 1),
                                      source.replace("docs/", "docs/en/", 1))
                or not isinstance(expected, str) or not CHECKSUM.fullmatch(expected)
                or source in seen or translated in destinations):
            errors.append("L10N007: unsafe, duplicate or malformed revision entry")
            continue
        seen.add(source)
        destinations.add(translated)
        original = root / source
        localized = root / translated
        if original.is_symlink() or localized.is_symlink() or not original.is_file() or not localized.is_file():
            errors.append(f"L10N007: missing or linked translation pair {source}")
            continue
        data = original.read_bytes().replace(b"\r\n", b"\n")
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            warnings.append(f"L10N008: review translation {translated} because {source} changed")
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--strict", action="store_true",
                        help="Fail on stale sources (manual pre-publication check only)")
    args = parser.parse_args()
    errors, warnings = check(args.root)
    for item in errors:
        print("ERROR: " + item)
    for item in warnings:
        print("WARNING: " + item)
    if not errors and not warnings:
        print("RU/EN translation sources: current revisions (not semantic verification)")
    return 1 if errors or (args.strict and warnings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
