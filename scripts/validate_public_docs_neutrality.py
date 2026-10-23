#!/usr/bin/env python3
"""Reject references to private owner projects in public Markdown.

Run from any directory; checks the entire repository without network or writes.
The upstream Hermes Agent *client* and the Toolkit repository name are allowed.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = frozenset({
    ".git", ".venv", "venv", "node_modules", ".artifacts",
    "__pycache__", ".pytest_cache", ".hermes-compat",
})
OWNER_PROJECT = re.compile(
    r"(?i)(?<![a-z0-9])(?:"
    r"yfc|your[-_ ]fitness[-_ ]coach|"
    r"hermes[-_ ](?:control[-_ ]center|brc|agent[-_ ]owner)|"
    r"MikeMoore1337/hermes|"
    r"ops[-_ ]watch|research[-_ ]scout|"
    r"second[-_ ]brain|night[-_ ]shift|"
    r"mikemoore\.top"
    r")(?![a-z0-9])"
)


def audit(root: Path = ROOT) -> list[dict[str, object]]:
    """Return findings for banned names, symlinks and unreadable Markdown."""
    findings: list[dict[str, object]] = []
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if not path.is_file() and not path.is_symlink():
            continue
        if SKIP_DIRS.intersection(relative.parts):
            continue
        if path.is_symlink():
            findings.append({"file": relative.as_posix(), "line": 0, "token": "SYMLINK"})
            continue
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            findings.append({"file": relative.as_posix(), "line": 0, "token": "UNREADABLE"})
            continue
        for number, line in enumerate(lines, 1):
            match = OWNER_PROJECT.search(line)
            if match:
                findings.append({
                    "file": relative.as_posix(),
                    "line": number,
                    "token": match.group(0),
                })
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        print(json.dumps({"status": "FAIL", "error": "Invalid root directory"}))
        return 2
    found = audit(root)
    print(json.dumps(
        {"status": "FAIL" if found else "PASS",
         "markdown_hits": len(found), "findings": found},
        indent=2, ensure_ascii=False,
    ))
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
