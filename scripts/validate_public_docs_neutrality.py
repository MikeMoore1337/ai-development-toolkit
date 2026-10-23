#!/usr/bin/env python3
"""Fail when public Markdown documentation names private/owner-specific projects.

Repository identity and third-party upstream package names are not restricted.
This check reads local Markdown only; it does not call APIs or alter files.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Keep this limited to identifiable project names, not generic product terms.
PROJECT_NAMES = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:"
    r"your[-_ ]fitness[-_ ]coach|"
    r"YFC|"
    r"hermes(?:[-_ ](?:agent|control[-_ ]center|brc))?|"
    r"second[-_ ]brain|second brain|"
    r"mikemoore\\.top"
    r")(?![A-Za-z0-9])"
)
SKIP_PARTS = frozenset({".git", ".venv", "venv", "node_modules", ".artifacts",
                        ".hermes-compat", "__pycache__", ".pytest_cache"})


def audit(root: Path = ROOT) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if set(relative.parts) & SKIP_PARTS or path.is_symlink():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = PROJECT_NAMES.search(line)
            if match:
                findings.append({"file": relative.as_posix(), "line": number,
                                 "token": match.group(0)})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = audit(args.root.resolve())
    print(json.dumps({"status": "FAIL" if result else "PASS",
                      "markdown_hits": len(result), "findings": result},
                     ensure_ascii=False, indent=2))
    return 1 if result else 0


if __name__ == "__main__":
    raise SystemExit(main())
