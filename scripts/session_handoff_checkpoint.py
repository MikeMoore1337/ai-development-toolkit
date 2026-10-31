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
    run = subprocess.run(["git", "-c", "core.fsmonitor=false", "-C", str(repo), *args], capture_output=True, check=True,
                         timeout=10, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"})
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


def verify_handoff_portable(repo: Path, packet: object, to_client: str) -> dict:
    """Compare GitHub project and tracked Git state across devices, never identity.

    A local path hash is intentionally not portable. All v2 validation (including
    digest, recipient and origin) must succeed before comparing portable fields.
    This mode NEVER authenticates the sender or grants execution consent.
    """
    checked = verify_handoff(repo, packet, to_client)
    if checked["decision"] == "BLOCKED":
        return checked
    if checked["decision"] not in ("PASS", "STALE"):
        return {"decision": "BLOCKED", "reason": "INVALID_HANDOFF"}
    if checked["decision"] == "STALE" and checked["reason"] != "repo_id":
        return checked
    # verify_handoff checked the full packet schema, digest, recipient and origin.
    checkpoint = packet["checkpoint"]
    current = state(repo)
    for key in ("branch", "commit", "status_sha256", "dirty"):
        if checkpoint[key] != current[key]:
            return {"decision": "STALE", "reason": key}
    return {
        "decision": "REVIEW_REQUIRED",
        "reason": "PORTABLE_GIT_MATCH_UNAUTHENTICATED",
        "git_check": "MATCHED_PORTABLE",
        "issue_url": packet["issue_url"],
        "references": list(packet["references"]),
        "sha256": packet["sha256"],
        "trust": "UNREVIEWED",
        "sender_identity": "NOT_VERIFIED",
        "owner_approval": "NOT_GRANTED",
        "next_action": "REVIEW_ISSUE",
        "execution": "NOT_RUN",
        "network": "NOT_USED",
    }


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



# #433 native read-only retrieval: no new vault, database or transcript index.
# This is deliberately link/exact-Issue search, NOT semantic session memory.
HANDOFF_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}\.json\Z")
MAX_HANDOFF_SEARCH = 16


def search_handoffs(repo: Path, directory: Path, issue_url: str, to_client: str) -> dict:
    """Search a specifically selected directory of manual handoff packets only."""
    if not isinstance(issue_url, str) or not ISSUE.fullmatch(issue_url):
        raise ValueError("search requires exact public GitHub Issue URL")
    if not isinstance(to_client, str) or not CLIENT.fullmatch(to_client):
        raise ValueError("invalid recipient")
    if not _project_matches_origin(repo, issue_url):
        raise ValueError("Issue does not match local GitHub origin")
    if not directory.is_absolute() or not directory.is_dir():
        raise ValueError("handoff directory must be existing absolute directory")
    for parent in (directory, *directory.parents):
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError("linked directory")
    root = Path(_git(repo, "rev-parse", "--show-toplevel")).resolve()
    if directory.resolve().is_relative_to(root):
        raise ValueError("handoff directory cannot be inside project checkout")
    entries = sorted(directory.iterdir(), key=lambda p: p.name)
    if len(entries) > MAX_HANDOFF_SEARCH:
        raise ValueError("too many handoff candidates")
    seen_hashes: set[str] = set()
    matches: list[dict] = []
    for item in entries:
        if not HANDOFF_NAME.fullmatch(item.name):
            raise ValueError("unexpected handoff filename")
        _handoff_file(item, repo, create=False)
        packet = json.loads(item.read_text(encoding="utf-8"))
        if not isinstance(packet, dict) or set(packet) != HANDOFF_FIELDS:
            raise ValueError("invalid handoff")
        if not isinstance(packet.get("issue_url"), str) or not _project_matches_origin(repo, packet["issue_url"]):
            raise ValueError("mixed project handoffs denied")
        if packet.get("issue_url") != issue_url or packet.get("to_client") != to_client:
            continue
        verified = verify_handoff(repo, packet, to_client)
        if verified["decision"] == "BLOCKED":
            raise ValueError("untrusted matching handoff")
        digest = packet["sha256"]
        if digest in seen_hashes:
            raise ValueError("duplicate handoff")
        seen_hashes.add(digest)
        matches.append({
            "sha256": digest,
            "issue_url": issue_url,
            "references": packet["references"] if verified["decision"] == "PASS" else [],
            "next_action": packet["next_action"] if verified["decision"] == "PASS" else "NONE",
            "git_check": verified["decision"],
            "trust": "UNREVIEWED",
            "owner_approval": "NOT_GRANTED",
        })
    count = sum(m["git_check"] == "PASS" for m in matches)
    return {
        "schema_version": 1,
        "source": "TOOLKIT_MANUAL_HANDOFF_SEARCH",
        "decision": "PASS" if count else "REVIEW_REQUIRED",
        "matches": matches,
        "verified_count": count,
        "inspected_count": len(entries),
        "search_type": "EXACT_ISSUE_AND_RECIPIENT_ONLY",
        "semantic_search": "NOT_AVAILABLE",
        "client_activation": "NOT_VERIFIED",
        "execution": "NOT_RUN",
        "network": "NOT_USED",
        "owner_approval": "NOT_GRANTED",
    }



def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("capture", "verify", "capture-handoff", "verify-handoff", "verify-portable-handoff", "search-handoffs"))
    p.add_argument("--repo", type=Path, default=Path.cwd())
    p.add_argument("--issue")
    p.add_argument("--file", type=Path)
    p.add_argument("--directory", type=Path)
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
        if args.mode == "search-handoffs":
            if not args.directory or not args.issue or not args.to_client:
                raise ValueError("search-handoffs requires --directory --issue --to-client")
            result = search_handoffs(args.repo, args.directory, args.issue, args.to_client)
            print(json.dumps(result, sort_keys=True, ensure_ascii=False))
            return 0 if result["decision"] == "PASS" else 2
        if args.mode in ("verify-handoff", "verify-portable-handoff"):
            if not args.file or not args.to_client:
                raise ValueError("handoff verification requires --file and --to-client")
            _handoff_file(args.file, args.repo, create=False)
            verifier = (verify_handoff_portable if args.mode == "verify-portable-handoff"
                        else verify_handoff)
            result = verifier(
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
