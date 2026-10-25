#!/usr/bin/env python3
"""Run pinned upstream Replica parity on a source-backed, public comparison.

Does not install skills, copy upstream source, modify projects or use any AI API.
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse

UPSTREAM_SHA = "77c9436fb3d18c3d58169efb8caf4fe906b0dc51"
UPSTREAM_BLOBS = {
    "LICENSE": "ac31f09aba721de8d139c7bef3d5024421426472",
    "replica-recon/SKILL.md": "e877302e106c839b81835edaa2a409cd239c52e3",
    "replica-diff/SKILL.md": "1322d76e6f383171808491f691dbdc477f250343",
    "replica-test/SKILL.md": "7dbe9dafa4c75fe02b6fb9eca37cadd809a73a36",
    "replica-diff/parity.py": "bb4eabd6f59a6435b5d9ed3c9e4340ef58e3958d",
}
REQUIRED = {"feature", "area", "priority", "original", "clone", "notes", "evidence_url", "target_evidence"}


class Refusal(ValueError):
    """Fail closed on non-pinned source or unsupported evidence."""


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", timeout=15)
    if proc.returncode:
        raise Refusal(f"Unable to verify upstream Git source for {args[0]}")
    return proc.stdout.strip()


def verified_upstream(raw: str) -> Path:
    root = Path(raw).resolve(strict=True)
    if not root.is_dir() or Path(git(root, "rev-parse", "--show-toplevel")).resolve() != root:
        raise Refusal("--upstream must be the exact root of a dedicated clone")
    if git(root, "rev-parse", "HEAD") != UPSTREAM_SHA:
        raise Refusal("Unpinned Replica upstream SHA")
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise Refusal("Upstream checkout must be clean; unknown files may contain executable code")
    for path, blob in UPSTREAM_BLOBS.items():
        if not (root / path).is_file() or (root / path).is_symlink():
            raise Refusal(f"Missing or symlinked original upstream component: {path}")
        if git(root, "rev-parse", f"HEAD:{path}") != blob:
            raise Refusal(f"Unexpected upstream file revision: {path}")
    return root


def check_matrix(raw: str) -> Path:
    path = Path(raw)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise Refusal("Source-backed matrix must be a regular CSV <= 1MiB")
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or set(reader.fieldnames) != REQUIRED:
            raise Refusal("Matrix needs exact feature,area,priority,original,clone,notes,evidence_url,target_evidence headers")
        rows = list(reader)
    if not rows or len(rows) > 250:
        raise Refusal("Expected 1..250 source-backed features")
    for n, row in enumerate(rows, 2):
        if None in row or not row["feature"].strip() or row["priority"].lower() not in {"must", "should", "could"}:
            raise Refusal(f"Invalid feature/priority at row {n}")
        if row["original"].lower() not in {"yes", "no"} or row["clone"].lower() not in {"yes", "partial", "no", "skip"}:
            raise Refusal(f"Unverified status at row {n}; UNKNOWN must not be counted as NO")
        if row["original"].lower() == "yes":
            u = urlparse(row["evidence_url"].strip())
            if u.scheme != "https" or not u.netloc or u.username or u.password:
                raise Refusal(f"Missing public HTTPS evidence at row {n}")
        if row["clone"].lower() in {"yes", "partial"} and not row["target_evidence"].strip():
            raise Refusal(f"Claimed target implementation lacks evidence at row {n}")
        if row["clone"].lower() == "skip" and not row["notes"].strip():
            raise Refusal(f"Skip requires reason at row {n}")
    return path.resolve(strict=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--upstream", required=True, help="locally available, clean pinned original repo")
    p.add_argument("--matrix", help="reviewed, evidence-backed CSV (no user secrets)")
    a = p.parse_args(argv)
    try:
        upstream = verified_upstream(a.upstream)
        if not a.matrix:
            print(f"REPLICA_SOURCE=PASS; SHA={UPSTREAM_SHA}; EXECUTION=NOT_RUN")
            return 0
        matrix = check_matrix(a.matrix)
        proc = subprocess.run(
            [sys.executable, "-I", str(upstream / "replica-diff/parity.py"), str(matrix), "--markdown"],
            cwd=upstream, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=20,
        )
        if proc.returncode:
            raise Refusal(f"Original upstream parity.py failed with exit {proc.returncode}")
        print(f"REPLICA_SOURCE=PASS; SHA={UPSTREAM_SHA}; INPUT=REVIEWED; READ_ONLY=YES")
        print(proc.stdout)
        return 0
    except (Refusal, OSError, UnicodeError, csv.Error, subprocess.TimeoutExpired) as exc:
        print(f"REPLICA=REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
