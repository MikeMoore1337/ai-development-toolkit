#!/usr/bin/env python3
"""Explicit local Git checkpoint for resuming a task; never captures chat transcripts."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ISSUE = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/issues/[1-9][0-9]*\Z")
MAX_INPUT = 32_768


def _git(repo: Path, *args: str) -> str:
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True, timeout=10)
    return run.stdout.decode("utf-8", errors="replace").strip()


def state(repo: Path) -> dict:
    root = Path(_git(repo, "rev-parse", "--show-toplevel")).resolve()
    branch = _git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    commit = _git(root, "rev-parse", "HEAD")
    raw_status = _git(root, "status", "--porcelain=v1", "-uno")
    return {
        "repo_id": hashlib.sha256(os.fsencode(root)).hexdigest(),
        "branch": branch,
        "commit": commit,
        "status_sha256": hashlib.sha256(raw_status.encode()).hexdigest(),
        "dirty": bool(raw_status),
    }


def make_packet(repo: Path, issue_url: str) -> dict:
    if not ISSUE.fullmatch(issue_url):
        raise ValueError("only a public GitHub issue URL is accepted")
    return {"schema": 1, "source": "GIT_METADATA_ONLY", "issue_url": issue_url, **state(repo)}


def verify_packet(repo: Path, packet: object) -> dict:
    if not isinstance(packet, dict) or packet.get("schema") != 1 or packet.get("source") != "GIT_METADATA_ONLY":
        return {"decision": "BLOCKED", "reason": "INVALID_PACKET"}
    if not ISSUE.fullmatch(str(packet.get("issue_url", ""))):
        return {"decision": "BLOCKED", "reason": "INVALID_ISSUE"}
    current = state(repo)
    for key in ("repo_id", "branch", "commit", "status_sha256", "dirty"):
        if packet.get(key) != current[key]:
            return {"decision": "STALE", "reason": key}
    return {"decision": "PASS", "reason": "MATCHED_GIT_STATE"}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("capture", "verify"))
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--issue")
    p.add_argument("--file", type=Path)
    args = p.parse_args()
    try:
        if args.mode == "capture":
            if not args.issue or not args.file:
                raise ValueError("capture requires --issue and --file")
            packet = make_packet(args.repo, args.issue)
            data = (json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
            flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(args.file, flags, 0o600)
            with os.fdopen(descriptor, "wb") as out:
                out.write(data)
            print(json.dumps({"decision": "PASS", "mode": "CAPTURED", "dirty": packet["dirty"]}))
            return 0
        if not args.file or args.file.is_symlink() or args.file.stat().st_size > MAX_INPUT:
            raise ValueError("unsafe or missing file")
        result = verify_packet(args.repo, json.loads(args.file.read_text(encoding="utf-8")))
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        result = {"decision": "BLOCKED", "reason": type(exc).__name__}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
