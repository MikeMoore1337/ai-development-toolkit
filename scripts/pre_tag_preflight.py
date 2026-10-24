#!/usr/bin/env python3
"""Fail-closed read-only pre-tag gate against an exact local and GitHub revision.

This command does not publish, modify tags, authorize distribution or replace
the manual provenance/rights gate. GitHub API reads are explicit and free.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "MikeMoore1337/ai-development-toolkit"
REQUIRED = frozenset({
    "tests (ubuntu-latest, 3.12)",
    "tests (ubuntu-latest, 3.13)",
    "tests (windows-latest, 3.14)",
})
SHA = re.compile(r"[0-9a-f]{40}\Z")
TAG = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+\Z")


class GateBlocked(ValueError):
    """A release prerequisite could not be proven."""


def local_preflight(root: Path, tag: str, sha: str) -> None:
    if not TAG.fullmatch(tag) or not SHA.fullmatch(sha):
        raise GateBlocked("Invalid vX.Y.Z tag or 40-character lowercase SHA")
    try:
        version = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))["version"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise GateBlocked("Cannot read local manifest version") from exc
    if tag != "v" + version:
        raise GateBlocked("TAG_MANIFEST_VERSION_MISMATCH")

    def git(*args: str) -> str:
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), *args], capture_output=True,
                text=True, encoding="utf-8", timeout=15, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise GateBlocked("Git command unavailable") from exc
        if proc.returncode:
            raise GateBlocked("Git command failed: " + args[0])
        return proc.stdout.strip()

    if Path(git("rev-parse", "--show-toplevel")).resolve() != root.resolve():
        raise GateBlocked("Target must be the Git worktree root")
    if git("rev-parse", "HEAD") != sha:
        raise GateBlocked("LOCAL_HEAD_SHA_MISMATCH")
    if git("status", "--porcelain", "--untracked-files=normal"):
        raise GateBlocked("WORKTREE_NOT_CLEAN")
    if git("tag", "--list", tag):
        raise GateBlocked("TAG_EXISTS_LOCALLY")


def github_get(path: str, token: str | None = None) -> tuple[int, dict]:
    url = "https://api.github.com/repos/" + REPOSITORY + "/" + path
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "adt-readonly-pretag-check",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        with urlopen(Request(url, headers=headers), timeout=12) as response:
            return response.status, json.load(response)
    except HTTPError as exc:
        # Only the exact absent-tag reference is allowed to return 404.
        if exc.code == 404:
            return 404, {}
        raise GateBlocked("GitHub HTTP status " + str(exc.code)) from exc
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        raise GateBlocked("GitHub verification unavailable") from exc


def remote_preflight(tag: str, sha: str, token: str | None = None) -> None:
    status, existing = github_get("git/ref/tags/" + tag, token)
    if status != 404:
        raise GateBlocked("TAG_ALREADY_EXISTS_OR_UNVERIFIED")

    status, branch = github_get("branches/main", token)
    if status != 200 or branch.get("commit", {}).get("sha") != sha:
        raise GateBlocked("REMOTE_MAIN_SHA_MISMATCH")

    status, runs = github_get("commits/" + sha + "/check-runs?per_page=100", token)
    if status != 200 or runs.get("total_count", 101) > 100:
        raise GateBlocked("CI_CHECKS_INCOMPLETE_OR_UNVERIFIED")
    observed = {}
    for entry in runs.get("check_runs", []):
        name = entry.get("name")
        if name in REQUIRED:
            observed.setdefault(name, []).append(entry)
    for name in REQUIRED:
        checks = observed.get(name, [])
        if len(checks) != 1 or checks[0].get("status") != "completed" or checks[0].get("conclusion") != "success":
            raise GateBlocked("REQUIRED_CI_NOT_GREEN: " + name)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True, help="New unused tag, e.g. v6.0.0")
    parser.add_argument("--sha", required=True, help="Exact validated 40-character SHA")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    stage = "LOCAL"
    try:
        root = args.root.resolve()
        local_preflight(root, args.tag, args.sha)
        stage = "REMOTE"
        remote_preflight(args.tag, args.sha, os.environ.get("GITHUB_TOKEN"))
    except GateBlocked as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        print(stage + "_PRETAG_BLOCKED", file=sys.stderr)
        print("RELEASE_ACCEPTANCE=BLOCKED", file=sys.stderr)
        return 2
    print("LOCAL_PRETAG_PASS")
    print("REMOTE_PRETAG_PASS")
    print("RIGHTS_ATTESTATION=NOT_ATTESTED_BY_PREFLIGHT")
    print("RELEASE_ACCEPTANCE=AWAITING_OWNER_APPROVAL")
    print("READY_FOR_OWNER_APPROVAL: local SHA, clean worktree, tag absence, remote main and required CI verified")
    print("NOT_PUBLISHED: owner rights/provenance decision and publication remain separate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
