#!/usr/bin/env python3
"""Offline integrity and optional clean-source applicability check for #338.

Does not download, install, execute Codex, modify the upstream, or use AI.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import subprocess
import sys

UPSTREAM_SHA = "7e06519357777badd7a115d2014a7ef845904310"
PATCH_SHA256 = "26202d49f6a37fa3dabbe53a4f048398b1a0e129624e1c20d2da90166c2ba5e6"
ROOT = Path(__file__).resolve().parents[1]
PATCH = ROOT / "integrations/episodic-memory/patches/0001-mcp-read-scoping-and-zero-inference-verify.patch"
EXPECTED_FILES = {
    "src/mcp-server.ts",
    "src/verify.ts",
    "test/mcp-server.test.ts",
}
REQUIRED_PATTERNS = (
    "function indexedArchivePath(requested: string)",
    "shouldSkipConversation(resolved)",
    "SELECT 1 FROM exchanges WHERE archive_path",
    "EPISODIC_MEMORY_SKIP_SUMMARIES",
    "expect(excluded.isError).toBe(true)",
)


def check() -> None:
    if PATCH.is_symlink():
        raise ValueError("Symlinked patch is not permitted")
    raw = PATCH.read_bytes()
    if hashlib.sha256(raw).hexdigest() != PATCH_SHA256:
        raise ValueError("Unexpected patch SHA256")
    text = raw.decode("utf-8")
    diffs = re.findall(r"^diff --git a/(\S+) b/(\S+)$", text, re.MULTILINE)
    if len(diffs) != len(EXPECTED_FILES):
        raise ValueError("Unexpected patch file count")
    if {old for old, _ in diffs} != EXPECTED_FILES or any(old != new for old, new in diffs):
        raise ValueError("Patch modifies unexpected upstream paths")
    if any(pattern not in text for pattern in REQUIRED_PATTERNS):
        raise ValueError("Mandatory security or zero-inference change missing")


def git(args: list[str], directory: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(directory), *args],
        check=True, text=True, capture_output=True, timeout=30,
    )
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--upstream-dir", type=Path, help="optional untouched upstream clone at pinned SHA"
    )
    args = parser.parse_args()
    try:
        check()
        if args.upstream_dir is not None:
            upstream = args.upstream_dir.resolve(strict=True)
            if git(["rev-parse", "HEAD"], upstream) != UPSTREAM_SHA:
                raise ValueError("Upstream commit differs from pinned revision")
            git(["apply", "--check", str(PATCH)], upstream)
        print("EPISODIC_MEMORY_PATCH=PASS")
        print(f"UPSTREAM_APPLICABILITY={'PASS' if args.upstream_dir else 'NOT_RUN'}")
        print("EXECUTION=NONE; CODEX_CLI=NONE; MODEL_CALLS=NONE")
        return 0
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        print(f"EPISODIC_MEMORY_PATCH=FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
