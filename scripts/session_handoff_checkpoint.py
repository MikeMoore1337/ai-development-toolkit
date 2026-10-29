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
    run = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, check=True,\n                         timeout=10, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
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


# #433: reference-only cross-client handoff layered on the existing #374
# Git checkpoint. There is no transcript import, daemon, or ECC dependency.
CLIENT = re.compile(r"[a-z][a-z0-9-]{0,31}\Z")
REFERENCE = re.compile(
    r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/(?:issues|pull)/[1-9][0-9]*\Z"
)
ACTIONS = frozenset(("REVIEW_ISSUE", "REVIEW_PR", "RUN_TESTS", "CHECK_CI", "WAIT_FOR_OWNER", "NONE"))
HANDOFF_FIELDS = frozenset((
    "schema", "source", "issue_url", "from_client", "to_client",
    "next_action", "references", "checkpoint", "trust", "owner_approval", "sha256",
))
CHECKPOINT_FIELDS = frozenset((
    "schema", "source", "issue_url", "repo_id", "branch", "commit", "status_sha256", "dirty",
))


# Match explicit GitHub remote identity; no network or Git credentials are read.
GITHUB_REMOTE = re.compile(
    r"(?:https://github\.com/|git@github\.com:|ssh://git@github\.com/)"
    r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?\Z"
)


def _project_matches_origin(repo: Path, issue_url: str) -> bool:
    try:
        url = _git(repo, "remote", "get-url", "origin")
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    origin = GITHUB_REMOTE.fullmatch(url)
    issue = ISSUE.fullmatch(issue_url)
    if not origin or not issue:
        return False
    expected = "https://github.com/" + origin.group(1) + "/" + origin.group(2) + "/issues/"
    return issue_url.casefold().startswith(expected.casefold())


def _handoff_digest(packet: dict) -> str:
    """Non-authenticating integrity digest, NOT an authorization signature."""
    unsigned = {key: value for key, value in packet.items() if key != "sha256"}
    encoded = json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _handoff_fields(issue_url: str, from_client: str, to_client: str,
                    references: list[str], next_action: str) -> None:
    if not isinstance(issue_url, str) or not ISSUE.fullmatch(issue_url):
        raise ValueError("invalid issue URL")
    if not isinstance(from_client, str) or not CLIENT.fullmatch(from_client):
        raise ValueError("invalid sender")
    if not isinstance(to_client, str) or not CLIENT.fullmatch(to_client) or from_client == to_client:
        raise ValueError("invalid recipient")
    if next_action not in ACTIONS:
        raise ValueError("invalid next action")
    if not isinstance(references, list) or len(references) > 8 or len(set(references)) != len(references):
        raise ValueError("invalid references")
    project = issue_url.rsplit("/issues/", 1)[0]
    for reference in references:
        if not isinstance(reference, str) or not REFERENCE.fullmatch(reference):
            raise ValueError("invalid reference")
        if reference.rsplit("/", 2)[0] != project:
            raise ValueError("cross-project reference")


def make_handoff(repo: Path, issue_url: str, from_client: str, to_client: str,
                 references: list[str], next_action: str) -> dict:
    """Create a bounded handoff; never accept arbitrary model-written prose."""
    _handoff_fields(issue_url, from_client, to_client, references, next_action)
    if not _project_matches_origin(repo, issue_url):
        raise ValueError("issue does not match GitHub origin")
    packet = {
        "schema": 2,
        "source": "TOOLKIT_MANUAL_HANDOFF",
        "issue_url": issue_url,
        "from_client": from_client,
        "to_client": to_client,
        "next_action": next_action,
        "references": list(references),
        "checkpoint": make_packet(repo, issue_url),
        "trust": "UNREVIEWED",
        "owner_approval": "NOT_GRANTED",
    }
    packet["sha256"] = _handoff_digest(packet)
    return packet


def verify_handoff(repo: Path, packet: object, to_client: str) -> dict:
    """Read-only local Git-state check. Digest is not proof of a human author."""
    invalid = {"decision": "BLOCKED", "reason": "INVALID_HANDOFF"}
    if not isinstance(packet, dict) or set(packet) != HANDOFF_FIELDS:
        return invalid
    if packet.get("schema") != 2 or packet.get("source") != "TOOLKIT_MANUAL_HANDOFF":
        return invalid
    if packet.get("trust") != "UNREVIEWED" or packet.get("owner_approval") != "NOT_GRANTED":
        return invalid
    checkpoint = packet.get("checkpoint")
    if not isinstance(checkpoint, dict) or set(checkpoint) != CHECKPOINT_FIELDS:
        return invalid
    if checkpoint.get("issue_url") != packet.get("issue_url"):
        return invalid
    try:
        _handoff_fields(packet["issue_url"], packet["from_client"], packet["to_client"],
                        packet["references"], packet["next_action"])
    except (TypeError, ValueError):
        return invalid
    if not isinstance(packet.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", packet["sha256"]):
        return invalid
    import hmac
    if not hmac.compare_digest(packet["sha256"], _handoff_digest(packet)):
        return {"decision": "BLOCKED", "reason": "TAMPERED_HANDOFF"}
    if to_client != packet["to_client"]:
        return {"decision": "BLOCKED", "reason": "WRONG_RECIPIENT"}
    if not _project_matches_origin(repo, packet["issue_url"]):
        return {"decision": "BLOCKED", "reason": "PROJECT_MISMATCH"}
    return verify_packet(repo, checkpoint)


def _handoff_file(path: Path, repo: Path, *, create: bool) -> None:
    """Refuse linked parents and worktree writes; operator chooses an external file."""
    if not path.is_absolute():
        raise ValueError("handoff file must have an absolute path")
    # Windows 8.3 aliases and case canonicalization are not symlinks. Check
    # each parent explicitly instead of comparing resolve() and absolute().
    for parent in (path.parent, *path.parent.parents):
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError("handoff parent is a link or junction")
    root = Path(_git(repo, "rev-parse", "--show-toplevel")).resolve()
    if path.resolve().is_relative_to(root):
        raise ValueError("handoff file must be outside the project checkout")
    if create:
        if not path.parent.is_dir() or path.exists() or path.is_symlink():
            raise ValueError("output must be a new file in an existing directory")
    elif path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT:
        raise ValueError("unsafe or missing handoff")


def _capture_handoff_file(path: Path, packet: dict) -> None:
    data = (json.dumps(packet, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if len(data) > MAX_INPUT:
        raise ValueError("handoff too large")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "wb") as out:
        out.write(data)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("capture", "verify", "capture-handoff", "verify-handoff"))
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--issue")
    p.add_argument("--file", type=Path)
    p.add_argument("--from-client")
    p.add_argument("--to-client")
    p.add_argument("--ref", action="append", default=[])
    p.add_argument("--next-action", default="REVIEW_ISSUE", choices=sorted(ACTIONS))
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
        if args.mode == "capture-handoff":
            if not args.file or not args.issue:
                raise ValueError("capture-handoff requires --issue and --file")
            packet = make_handoff(args.repo, args.issue, args.from_client,
                                  args.to_client, args.ref, args.next_action)
            _handoff_file(args.file, args.repo, create=True)
            _capture_handoff_file(args.file, packet)
            print(json.dumps({"decision": "PASS", "mode": "CAPTURED_HANDOFF",
                              "trust": "UNREVIEWED", "owner_approval": "NOT_GRANTED"}))
            return 0
        if args.mode == "verify-handoff":
            if not args.file or not args.to_client:
                raise ValueError("verify-handoff requires --file and --to-client")
            _handoff_file(args.file, args.repo, create=False)
            result = verify_handoff(
                args.repo, json.loads(args.file.read_text(encoding="utf-8")), args.to_client
            )
            print(json.dumps(result, sort_keys=True))
            return 0 if result["decision"] == "PASS" else 2
        if not args.file or args.file.is_symlink() or args.file.stat().st_size > MAX_INPUT:
            raise ValueError("unsafe or missing file")
        result = verify_packet(args.repo, json.loads(args.file.read_text(encoding="utf-8")))
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        result = {"decision": "BLOCKED", "reason": type(exc).__name__}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["decision"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
