#!/usr/bin/env python3
"""Explicit, local Git-based selective rollback for tracked regular files.

No agent hooks, prompts, background observation, paid services, or file snapshots.
Git commits (not individual agent actions) are the supported checkpoints.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys

SHA_PATTERN = re.compile(r"[0-9a-fA-F]{40}\Z")


class Refusal(ValueError):
    """A safety precondition for a proposed restore was not satisfied."""


def git(root: Path, *args: str, allow_diff: bool = False) -> str:
    proc = subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=20,
    )
    if proc.returncode and not (allow_diff and proc.returncode == 1):
        raise Refusal(f"Git precondition failed for {args[0]} (exit {proc.returncode})")
    return proc.stdout.strip()


def git_root(raw: str) -> Path:
    root = Path(raw).resolve(strict=True)
    if not root.is_dir():
        raise Refusal("Repository path is not a directory")
    actual = Path(git(root, "rev-parse", "--show-toplevel")).resolve(strict=True)
    if actual != root:
        raise Refusal("--repo must identify the exact Git repository root")
    return root


def commit_sha(root: Path, value: str) -> str:
    if not SHA_PATTERN.fullmatch(value):
        raise Refusal("Commit must be a complete 40-character hexadecimal SHA")
    sha = value.lower()
    # Only existing commit objects are accepted, not other Git object types.
    if git(root, "rev-parse", "--verify", f"{sha}^{{commit}}") != sha:
        raise Refusal("Commit is unavailable or not an exact commit SHA")
    return sha


def validated_path(root: Path, supplied: str) -> str:
    # Avoid drive-letter paths, backslash separators, ADS, .git and path traversal.
    if (not supplied or supplied.startswith("/") or "\\" in supplied
            or ":" in supplied or "\x00" in supplied):
        raise Refusal("Only safe repository-relative POSIX paths are accepted")
    parts = supplied.split("/")
    if any(s in {"", ".", ".."} or s.lower() == ".git" for s in parts):
        raise Refusal("Unsafe, noncanonical or internal repository path")
    candidate = root
    for part in parts:
        candidate = candidate / part
        if candidate.is_symlink() or (hasattr(candidate, "is_junction") and candidate.is_junction()):
            raise Refusal("Symlinked files/directories cannot be restored")
    if not candidate.exists() or not candidate.is_file():
        raise Refusal("Only existing tracked regular files can be restored")
    if not candidate.resolve().is_relative_to(root):
        raise Refusal("Target escapes repository")
    return "/".join(parts)


def regular_blob(root: Path, sha: str, path: str) -> str:
    row = git(root, "ls-tree", sha, "--", path)
    # Exact match, regular-file mode only (no symlink, directory or submodule).
    cols = row.split("\t", 1)
    if len(cols) != 2 or cols[1] != path:
        raise Refusal(f"Not a tracked regular file in {sha[:12]}: {path}")
    meta = cols[0].split()
    if len(meta) != 3 or meta[0] not in {"100644", "100755"} or meta[1] != "blob":
        raise Refusal(f"Non-regular Git object refused: {path}")
    return meta[2]


def validate(root: Path, commit: str, paths: list[str], *, require_clean: bool) -> tuple[str, list[str]]:
    if not paths:
        raise Refusal("At least one --file is required")
    selected = [validated_path(root, p) for p in paths]
    if len(set(selected)) != len(selected):
        raise Refusal("Duplicate file selection")
    head = git(root, "rev-parse", "HEAD")
    for path in selected:
        regular_blob(root, head, path)
        regular_blob(root, commit, path)
        if require_clean:
            # git diff HEAD includes both index and working-tree changes.
            changed = subprocess.run(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--", path], timeout=20)
            if changed.returncode != 0:
                raise Refusal(f"Uncommitted/staged modification or diff failure: {path}")
    return head, selected


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="exact root of a local Git checkout")
    sub = parser.add_subparsers(dest="cmd", required=True)
    timeline = sub.add_parser("timeline", help="read-only Git commit history")
    timeline.add_argument("--count", type=int, default=10)
    for name in ("preview", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--commit", required=True, help="exact commit SHA to restore from")
        p.add_argument("--file", action="append", required=True, dest="files")
        if name == "apply":
            p.add_argument("--confirm", action="store_true", help="explicit opt-in write")
            p.add_argument("--expect-head", required=True, help="HEAD SHA observed in preview")
    args = parser.parse_args(argv)
    try:
        root = git_root(args.repo)
        if args.cmd == "timeline":
            if not 1 <= args.count <= 100:
                raise Refusal("--count must be from 1 to 100")
            print(git(root, "log", f"--max-count={args.count}", "--format=%H %ad %s", "--date=short"))
            return 0
        commit = commit_sha(root, args.commit)
        if args.cmd == "apply" and not args.confirm:
            raise Refusal("Apply requires explicit --confirm")
        if args.cmd == "apply" and len(args.files) != 1:
            raise Refusal("Apply restores exactly one file per confirmation to avoid partial multi-file writes")
        head, selected = validate(root, commit, args.files, require_clean=args.cmd == "apply")
        if args.cmd == "apply":
            expected = commit_sha(root, args.expect_head)
            if expected != head:
                raise Refusal("HEAD moved since preview; inspect changes again")
        print(f"HEAD={head}\nSOURCE={commit}\nFILES={len(selected)}")
        for path in selected:
            source_blob = regular_blob(root, commit, path)
            current_blob = regular_blob(root, head, path)
            print(f"FILE={path} CURRENT_BLOB={current_blob} SOURCE_BLOB={source_blob}")
            print(git(root, "diff", "--no-ext-diff", "--no-textconv", "HEAD", commit, "--", path))
        if args.cmd == "apply":
            # Existing tracked files are still clean, HEAD unchanged, all sources regular.
            # Restore affects working tree only; index and commit history remain untouched.
            for path in selected:
                git(root, "restore", f"--source={commit}", "--worktree", "--", path)
            print("RESTORE=APPLIED; INDEX=UNCHANGED; PREVIOUS_CONTENT_IN_GIT_HEAD=YES")
        else:
            print("RESTORE=NOT_RUN (read-only preview)")
        return 0
    except (Refusal, OSError, subprocess.TimeoutExpired) as exc:
        print(f"REWIND=REFUSED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
