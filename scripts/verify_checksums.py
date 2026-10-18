#!/usr/bin/env python3
"""Verify the existing SHA256SUMS.txt file. No network access or writes by default.

Run with --write to regenerate digests of Git-tracked files before a release.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = re.compile(r"^([0-9a-f]{64})  (.+)$")


def verify(root: Path = ROOT) -> list[str]:
    checksum_file = root / "SHA256SUMS.txt"
    errors: list[str] = []
    if not checksum_file.is_file():
        return ["SHA256SUMS.txt is missing"]
    seen: set[str] = set()
    for number, line in enumerate(checksum_file.read_text(encoding="utf-8").splitlines(), 1):
        match = RECORD.fullmatch(line)
        if not match:
            errors.append(f"line {number}: malformed SHA256 record")
            continue
        expected, name = match.groups()
        if name in seen:
            errors.append(f"line {number}: duplicate path {name}")
            continue
        seen.add(name)
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or name == "SHA256SUMS.txt":
            errors.append(f"line {number}: unsafe path {name}")
            continue
        file = root / relative
        if file.is_symlink() or not file.is_file():
            errors.append(f"line {number}: missing or linked file {name}")
            continue
        if not file.resolve().is_relative_to(root.resolve()):
            errors.append(f"line {number}: escaping path {name}")
            continue
        actual = hashlib.sha256(file.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"line {number}: checksum mismatch {name}")
    if not seen:
        errors.append("No checksum records")
    return errors


def write(root: Path = ROOT) -> int:
    command = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, capture_output=True, check=False,
    )
    if command.returncode:
        print("FAIL: --write requires a Git worktree", file=sys.stderr)
        return 1
    paths = sorted(p.decode("utf-8") for p in command.stdout.split(b"\0") if p)
    digests = []
    for name in paths:
        if name == "SHA256SUMS.txt":
            continue
        file = root / name
        if file.is_symlink() or not file.is_file():
            print(f"FAIL: missing or linked tracked file: {name}", file=sys.stderr)
            return 1
        digests.append(f"{hashlib.sha256(file.read_bytes()).hexdigest()}  {name}")
    (root / "SHA256SUMS.txt").write_text("\n".join(digests) + "\n", encoding="utf-8")
    print(f"WROTE: {len(digests)} SHA256 records")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Explicitly regenerate from Git tracked files")
    args = parser.parse_args()
    if args.write:
        return write()
    errors = verify()
    for issue in errors:
        print(f"FAIL: {issue}")
    if errors:
        return 1
    print("PASS: SHA256SUMS.txt entries match repository bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
