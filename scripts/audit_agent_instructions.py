#!/usr/bin/env python3
"""Read-only, bounded AGENTS.md/CLAUDE.md structural audit (no content export)."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".artifacts"}
FILENAMES = {"AGENTS.md", "CLAUDE.md"}
REFERENCE = re.compile(r"`([A-Za-z0-9_./-]+\.(?:md|py|json|toml|ts|tsx)):(\d+)`", re.I)
MAX_FILES = 256
MAX_BYTES = 262144


def audit(root: Path) -> dict:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("root must be a real directory, not a symlink")
    root = root.resolve()
    reports = []
    occurrences: dict[str, list[dict]] = {}
    paths = sorted(
        p for p in root.rglob("*")
        if p.name in FILENAMES
        and not (set(p.relative_to(root).parts[:-1]) & SKIP_DIRS)
    )
    if len(paths) > MAX_FILES:
        raise ValueError("too many instruction files; narrow the root")
    for path in paths:
        relative = path.relative_to(root).as_posix()
        if path.is_symlink() or not path.is_file():
            reports.append({"path": relative, "code": "UNSAFE_FILE"})
            continue
        if path.stat().st_size > MAX_BYTES:
            reports.append({"path": relative, "code": "TOO_LARGE"})
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            reports.append({"path": relative, "code": "UNREADABLE"})
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith(("- ", "* ")) and len(stripped) > 12:
                normalized = " ".join(stripped[2:].casefold().split())
                occurrences.setdefault(normalized, []).append({"path": relative, "line": line_number})
            for match in REFERENCE.finditer(line):
                target = (root / match.group(1)).resolve()
                target_line = int(match.group(2))
                if not target.is_relative_to(root) or not target.is_file():
                    reports.append({"path": relative, "line": line_number, "code": "STALE_OR_UNSAFE_REFERENCE"})
                    continue
                try:
                    count = len(target.read_text(encoding="utf-8").splitlines()) if target.stat().st_size <= MAX_BYTES else 0
                except (OSError, UnicodeError):
                    count = 0
                if target_line < 1 or target_line > count:
                    reports.append({"path": relative, "line": line_number, "code": "STALE_OR_UNSAFE_REFERENCE"})
    for locations in occurrences.values():
        if len({loc["path"] for loc in locations}) > 1:
            reports.extend({**loc, "code": "DUPLICATE_CROSS_FILE_RULE"} for loc in locations)
    reports.sort(key=lambda x: (x["path"], x.get("line", 0), x["code"]))
    return {"schema": 1, "files": len(paths), "findings": reports, "meaning": "Review hints only; no semantic conflict assertion or file changes"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = audit(args.root)
    except ValueError as exc:
        print(json.dumps({"schema": 1, "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
