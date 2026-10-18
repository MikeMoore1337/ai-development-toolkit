#!/usr/bin/env python3
"""Verify every tracked file against SHA256SUMS.txt, including inventory completeness.

Normal mode uses the exact Git index inventory; --archive-root validates a clean
extracted release tree without Git metadata. Verification does not write files.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = re.compile(r"^([0-9a-f]{64})  (.+)$")
INVENTORY = "SHA256SUMS.txt"


def canonical_bytes(data: bytes) -> bytes:
    """Canonicalize Git-managed LF/CRLF text; never normalize binary-looking bytes."""
    if b"\x00" in data or any(b < 32 and b not in (9, 10, 12, 13) for b in data):
        return data
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return data
    return data.replace(b"\r\n", b"\n")


def _tracked(root: Path) -> set[str]:
    """Require the target to be the actual Git root, not a parent worktree."""
    try:
        top = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
            capture_output=True, check=False, text=True, encoding="utf-8",
        )
        if top.returncode or Path(top.stdout.strip()).resolve() != root.resolve():
            raise ValueError("A Git repository root is required (or use --archive-root)")
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "-z", "--full-name"],
            capture_output=True, check=False,
        )
    except OSError as exc:
        raise ValueError(f"Unable to inspect Git index: {exc}") from exc
    if result.returncode:
        raise ValueError("Unable to list Git-tracked files")
    return {os.fsdecode(name) for name in result.stdout.split(b"\0") if name}


def _archive_files(root: Path) -> set[str]:
    """All files in a clean extracted source archive must be accounted for."""
    if not root.is_dir():
        raise ValueError("Archive root does not exist")
    if (root / ".git").exists():
        raise ValueError("Archive mode must target an extracted archive, not a clone")
    return {path.relative_to(root).as_posix() for path in root.rglob("*")
            if path.is_file() or path.is_symlink()}


def _safe_path(root: Path, name: str) -> Path | None:
    relative = Path(name)
    if (not name or name == INVENTORY or relative.is_absolute()
            or "\\" in name or ".." in relative.parts or "." in relative.parts):
        return None
    file = root / relative
    if not file.resolve().is_relative_to(root.resolve()):
        return None
    for item in (file, *list(file.parents)):
        if item == root.parent:
            break
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            return None
    return file


def verify(root: Path = ROOT, *, tracked_paths: set[str] | None = None,
           archive: bool = False) -> list[str]:
    """Check digest correctness AND full expected file coverage."""
    root = root.resolve()
    record = root / INVENTORY
    if not record.is_file() or record.is_symlink():
        return [f"{INVENTORY} is missing or linked"]
    if archive and tracked_paths is not None:
        return ["Archive and explicit tracked paths cannot be mixed"]
    try:
        expected_files = (_archive_files(root) if archive else
                          (_tracked(root) if tracked_paths is None else set(tracked_paths)))
    except ValueError as exc:
        return [str(exc)]
    expected_files.discard(INVENTORY)
    errors: list[str] = []
    declared: set[str] = set()
    for number, line in enumerate(record.read_text(encoding="utf-8").splitlines(), 1):
        match = RECORD.fullmatch(line)
        if not match:
            errors.append(f"line {number}: malformed SHA256 record")
            continue
        expected, name = match.groups()
        if name in declared:
            errors.append(f"line {number}: duplicate path {name}")
            continue
        declared.add(name)
        file = _safe_path(root, name)
        if file is None:
            errors.append(f"line {number}: unsafe path {name}")
        elif name not in expected_files:
            errors.append(f"line {number}: untracked or unexpected path {name}")
        elif not file.is_file():
            errors.append(f"line {number}: missing file {name}")
        else:
            actual = hashlib.sha256(canonical_bytes(file.read_bytes())).hexdigest()
            if actual != expected:
                errors.append(f"line {number}: checksum mismatch {name}")
    for name in sorted(expected_files - declared):
        errors.append(f"missing checksum entry: {name}")
    if not expected_files:
        errors.append("No expected files in distribution")
    return errors


def write(root: Path = ROOT) -> int:
    """Explicitly regenerate an inventory for the current Git index."""
    try:
        paths = sorted(_tracked(root))
    except ValueError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    digests = []
    for name in paths:
        if name == INVENTORY:
            continue
        file = _safe_path(root, name)
        if file is None or not file.is_file():
            print(f"FAIL: unsafe or missing tracked file: {name}", file=sys.stderr)
            return 1
        digests.append(f"{hashlib.sha256(canonical_bytes(file.read_bytes())).hexdigest()}  {name}")
    (root / INVENTORY).write_text("\n".join(digests) + "\n", encoding="utf-8")
    print(f"WROTE: {len(digests)} complete SHA256 records")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="Regenerate using tracked files")
    mode.add_argument("--archive-root", type=Path, help="Check a clean extracted release archive")
    args = parser.parse_args()
    if args.write:
        return write()
    issues = verify(args.archive_root, archive=True) if args.archive_root else verify()
    for issue in issues:
        print(f"FAIL: {issue}")
    if issues:
        return 1
    print("PASS: all expected source files listed with matching SHA256 digests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
