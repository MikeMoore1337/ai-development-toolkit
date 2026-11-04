#!/usr/bin/env python3
"""Explicit project-reviewed reference index. No second database, ingestion or inference."""
from __future__ import annotations

import argparse
import http.client
import hmac
import json
import re
import subprocess
import unicodedata
from datetime import datetime, timedelta, timezone
from pathlib import Path

import session_handoff_checkpoint as handoff

KINDS = frozenset(("DECISION", "PRACTICE", "LIMITATION"))
RECORD_FIELDS = frozenset((
    "schema", "source", "scope", "project_url", "issue_url", "review_url",
    "kind", "summary", "references", "review_attestation", "trust",
    "owner_approval", "sha256",
))
REVIEW_URL = re.compile(
    r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/"
    r"(?:issues/[1-9][0-9]*#issuecomment-[1-9][0-9]*|"
    r"pull/[1-9][0-9]*#(?:issuecomment|pullrequestreview)-[1-9][0-9]*)\Z"
)
DANGER = re.compile(
    r"(?:https?://|-----BEGIN|(?:sk-(?:proj-)?|gh[pousr]_|github_pat_|xox[baprs]-)"
    r"|AKIA[A-Z0-9]{16}|\b(?:api[_-]?key|password|secret|token|bearer|"
    r"private[_-]?key)\b|[A-Z]:\\|/(?:home|Users|root|etc|var|workspace)/|"
    r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,})", re.IGNORECASE,
)

def _project_url(issue_url: str) -> str:
    return issue_url.rsplit("/issues/", 1)[0].casefold()


def _fields(repo: Path, issue_url: str, review_url: str, kind: str,
            summary: str, references: list[str]) -> None:
    if not isinstance(references, list) or any(not isinstance(item, str) for item in references):
        raise ValueError("References must be a list of GitHub URLs")
    handoff._handoff_fields(issue_url, "codex", "hermes", references, "NONE")
    if not handoff._project_matches_origin(repo, issue_url):
        raise ValueError("Issue does not match project GitHub origin")
    found = REVIEW_URL.fullmatch(review_url) if isinstance(review_url, str) else None
    if not found:
        raise ValueError("An exact GitHub review permalink is required")
    if "https://github.com/" + found[1].casefold() + "/" + found[2].casefold() != _project_url(issue_url):
        raise ValueError("Review reference is outside project")
    if not isinstance(kind, str) or kind not in KINDS:
        raise ValueError("Unsupported memory category")
    if not isinstance(summary, str) or not 8 <= len(summary) <= 240:
        raise ValueError("Invalid short summary")
    if summary != summary.strip() or any(ord(c) < 32 or ord(c) == 127 for c in summary):
        raise ValueError("Summary must be one clean line")
    if any(c in summary for c in ("\\", "<", ">", "\x00")):
        raise ValueError("Summary contains unsafe characters")
    if DANGER.search(unicodedata.normalize("NFKC", summary)):
        raise ValueError("Summary contains unsafe secret/path-like text")


def prepare_record(repo: Path, issue_url: str, review_url: str,
                   kind: str, summary: str, references: list[str]) -> dict:
    """Prepare a review-reference candidate; this function NEVER persists it."""
    _fields(repo, issue_url, review_url, kind, summary, references)
    record = {
        "schema": 1, "source": "TOOLKIT_REVIEWED_MEMORY_REFERENCE",
        "scope": "project", "project_url": _project_url(issue_url),
        "issue_url": issue_url, "review_url": review_url,
        "kind": kind, "summary": summary, "references": list(references),
        "review_attestation": "OPERATOR_CLAIM_NOT_AUTHENTICATED",
        "trust": "UNTRUSTED_REFERENCE", "owner_approval": "NOT_GRANTED",
    }
    record["sha256"] = handoff._handoff_digest(record)
    return record


def verify_record(repo: Path, record: object) -> dict:
    invalid = {"decision": "BLOCKED", "reason": "INVALID_REVIEWED_MEMORY"}
    if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
        return invalid
    if (type(record.get("schema")) is not int or record["schema"] != 1
            or record.get("source") != "TOOLKIT_REVIEWED_MEMORY_REFERENCE"
            or record.get("scope") != "project"
            or record.get("review_attestation") != "OPERATOR_CLAIM_NOT_AUTHENTICATED"
            or record.get("trust") != "UNTRUSTED_REFERENCE"
            or record.get("owner_approval") != "NOT_GRANTED"):
        return invalid
    try:
        _fields(repo, record["issue_url"], record["review_url"], record["kind"],
                record["summary"], record["references"])
    except (TypeError, ValueError):
        return invalid
    if record["project_url"] != _project_url(record["issue_url"]):
        return invalid
    digest = record.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        return invalid
    if not hmac.compare_digest(digest, handoff._handoff_digest(record)):
        return {"decision": "BLOCKED", "reason": "TAMPERED_REVIEWED_MEMORY"}
    return {
        "decision": "REVIEW_REQUIRED", "reason": "REVIEW_SOURCE_NOT_AUTHENTICATED",
        "issue_url": record["issue_url"], "review_url": record["review_url"],
        "kind": record["kind"], "summary": record["summary"],
        "references": list(record["references"]), "sha256": record["sha256"],
        "scope": "project", "trust": "UNTRUSTED_REFERENCE",
        "review_attestation": "NOT_VERIFIED", "owner_approval": "NOT_GRANTED",
        "next_action": "REVIEW_ISSUE", "execution": "NOT_RUN", "network": "NOT_USED",
    }


def _file(repo: Path, path: Path, *, create: bool) -> None:
    if ".." in path.parts:
        raise ValueError("Parent traversal is forbidden in memory paths")
    if not handoff.HANDOFF_NAME.fullmatch(path.name):
        raise ValueError("Unexpected memory filename")
    handoff._handoff_file(path, repo, create=create)


def read_record(repo: Path, file: Path) -> dict:
    _file(repo, file, create=False)
    return verify_record(repo, json.loads(file.read_text(encoding="utf-8")))


# A separate same-Issue owner attestation binds the digest without changing
# legacy create-only records or granting action authority.
OWNER_REVIEW_URL = re.compile(
    r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/issues/"
    r"([1-9][0-9]*)#issuecomment-([1-9][0-9]*)\Z"
)
OWNER_REVIEW_BODY = re.compile(
    r"TOOLKIT-MEMORY-OWNER-REVIEW-V1\n"
    r"record_sha256=([0-9a-f]{64})\n"
    r"decision=APPROVE_REFERENCE\n"
    r"expires_utc=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\n?\Z"
)
MAX_GITHUB_RESPONSE = 32_768


def _public_github_json(path: str) -> dict:
    """GET only from GitHub's fixed TLS host; no tokens, proxy or redirects."""
    connection = http.client.HTTPSConnection("api.github.com", timeout=5)
    try:
        connection.request("GET", path, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "toolkit-owner-review-readonly",
        })
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError("GITHUB_NOT_AVAILABLE")
        raw = response.read(MAX_GITHUB_RESPONSE + 1)
        if len(raw) > MAX_GITHUB_RESPONSE:
            raise ValueError("GITHUB_RESPONSE_TOO_LARGE")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("GITHUB_RESPONSE_INVALID")
        return data
    finally:
        connection.close()


def verify_owner_review(repo: Path, file: Path, attestation_url: str, *,
                        allow_public_github_fetch: bool = False,
                        fetcher=None, now: datetime | None = None) -> dict:
    """Optional live GitHub owner-account review of a reference, never consent.

    Only an explicit public GitHub GET is permitted. A record checksum is not
    authentication, and a GitHub account does not establish physical human presence.
    """
    common = {
        "decision": "REVIEW_REQUIRED", "review_attestation": "NOT_VERIFIED",
        "owner_approval": "NOT_GRANTED", "action_authorized": False,
        "execution_authorized": False, "execution": "NOT_RUN",
        "trust": "UNTRUSTED_REFERENCE", "network": "NOT_USED",
    }

    def refused(reason: str, *, blocked: bool = False, network: str = "NOT_USED") -> dict:
        return {**common, "decision": "BLOCKED" if blocked else "REVIEW_REQUIRED",
                "reason": reason, "network": network}

    if allow_public_github_fetch is not True:
        return refused("PUBLIC_GITHUB_OPT_IN_REQUIRED")
    try:
        entry = read_record(repo, file)
    except (OSError, ValueError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired):
        return refused("INVALID_LOCAL_REFERENCE", blocked=True)
    if entry.get("decision") != "REVIEW_REQUIRED":
        return refused("INVALID_LOCAL_REFERENCE", blocked=True)
    url = (OWNER_REVIEW_URL.fullmatch(attestation_url)
           if isinstance(attestation_url, str) and len(attestation_url) <= 256 else None)
    if (not url or len(url[3]) > 12 or len(url[4]) > 20
            or entry["issue_url"].casefold() != (
            f"https://github.com/{url[1]}/{url[2]}/issues/{url[3]}".casefold())):
        return refused("INVALID_OWNER_ATTESTATION_SCOPE", blocked=True)

    owner, project, issue_number, comment_number = url.groups()
    api_prefix = f"/repos/{owner}/{project}"
    issue_api_url = f"https://api.github.com{api_prefix}/issues/{issue_number}"
    getter = fetcher if fetcher is not None else _public_github_json
    network = "PUBLIC_GITHUB_READ_ATTEMPTED"
    try:
        metadata = getter(api_prefix)
        comment = getter(f"{api_prefix}/issues/comments/{comment_number}")
    except (OSError, ValueError, TypeError, KeyError, http.client.HTTPException):
        return refused("GITHUB_OWNER_REVIEW_NOT_VERIFIED", network=network)

    identity = metadata.get("owner") if isinstance(metadata, dict) else None
    author = comment.get("user") if isinstance(comment, dict) else None
    if (not isinstance(identity, dict) or not isinstance(author, dict)
            or metadata.get("private") is not False
            or str(metadata.get("full_name", "")).casefold() != f"{owner}/{project}".casefold()
            or identity.get("type") != "User" or author.get("type") != "User"
            or type(identity.get("id")) is not int or identity["id"] <= 0
            or type(author.get("id")) is not int or author["id"] != identity["id"]
            or not isinstance(identity.get("login"), str)
            or not isinstance(author.get("login"), str)
            or author["login"].casefold() != identity["login"].casefold()
            or identity["login"].casefold() != owner.casefold()
            or comment.get("author_association") != "OWNER"
            or type(comment.get("id")) is not int or comment["id"] != int(comment_number)
            or str(comment.get("issue_url", "")).casefold() != issue_api_url.casefold()
            or str(comment.get("html_url", "")).casefold() != attestation_url.casefold()):
        return refused("GITHUB_OWNER_IDENTITY_OR_SCOPE_MISMATCH", network=network)

    body = comment.get("body")
    statement = OWNER_REVIEW_BODY.fullmatch(body) if isinstance(body, str) and len(body) <= 256 else None
    if not statement or not hmac.compare_digest(statement[1], entry["sha256"]):
        return refused("OWNER_ATTESTATION_MISSING_OR_REVOKED", network=network)
    try:
        issued = datetime.strptime(comment["created_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        expiry = datetime.strptime(statement[2], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        current = now if now is not None else datetime.now(timezone.utc)
        if not isinstance(current, datetime) or current.tzinfo is None:
            raise ValueError("Invalid verification clock")
    except (ValueError, TypeError, KeyError):
        return refused("OWNER_ATTESTATION_TIME_INVALID", network=network)
    if (issued > current + timedelta(minutes=5) or expiry <= current
            or expiry > issued + timedelta(days=30)):
        return refused("OWNER_ATTESTATION_EXPIRED_OR_OUT_OF_BOUNDS", network=network)
    return {
        **common, "decision": "REFERENCE_REVIEW_ATTESTED",
        "reason": "PUBLIC_GITHUB_OWNER_ACCOUNT_MATCH",
        "review_attestation": "GITHUB_REPOSITORY_OWNER_ACCOUNT_VERIFIED",
        "review_scope": "REFERENCE_ONLY",
        "human_presence": "NOT_VERIFIED",
        "reviewer_login": identity["login"],
        "reviewer_user_id": identity["id"],
        "record_sha256": entry["sha256"],
        "attestation_url": attestation_url,
        "expires_utc": statement[2], "network": network,
    }


def _directory(repo: Path, directory: Path) -> list[Path]:
    if ".." in directory.parts:
        raise ValueError("Parent traversal is forbidden in memory paths")
    if not directory.is_absolute() or not directory.is_dir():
        raise ValueError("Explicit absolute memory directory required")
    for parent in (directory, *directory.parents):
        if parent.is_symlink() or (hasattr(parent, "is_junction") and parent.is_junction()):
            raise ValueError("Linked memory directory")
    root = Path(handoff._git(repo, "rev-parse", "--show-toplevel")).resolve()
    if directory.resolve().is_relative_to(root):
        raise ValueError("Memory directory cannot be within checkout")
    entries = sorted(directory.iterdir(), key=lambda p: p.name)
    if len(entries) > handoff.MAX_HANDOFF_SEARCH:
        raise ValueError("Too many memory candidates")
    return entries


def search_records(repo: Path, directory: Path, issue_url: str) -> dict:
    """Exact-Issue search in an explicitly selected Toolkit file folder only."""
    if not isinstance(issue_url, str) or not handoff.ISSUE.fullmatch(issue_url):
        raise ValueError("Exact GitHub Issue required")
    if not handoff._project_matches_origin(repo, issue_url):
        raise ValueError("Issue does not match project")
    entries = _directory(repo, directory)
    matches = []
    seen = set()
    for path in entries:
        result = read_record(repo, path)
        if result["decision"] != "REVIEW_REQUIRED":
            raise ValueError("Invalid memory entry")
        if result["sha256"] in seen:
            raise ValueError("Duplicate memory entry")
        seen.add(result["sha256"])
        if result["issue_url"] == issue_url:
            matches.append(result)
    return {
        "schema_version": 1, "source": "TOOLKIT_MANUAL_REVIEWED_MEMORY_SEARCH",
        "decision": "REVIEW_REQUIRED", "matches": matches,
        "found_count": len(matches), "inspected_count": len(entries),
        "search_type": "EXACT_ISSUE_ONLY", "semantic_search": "NOT_AVAILABLE",
        "review_attestation": "NOT_VERIFIED", "owner_approval": "NOT_GRANTED",
        "network": "NOT_USED", "execution": "NOT_RUN",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "record", "read", "search", "verify-owner-review"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--issue")
    parser.add_argument("--review-url")
    parser.add_argument("--kind", choices=sorted(KINDS))
    parser.add_argument("--summary")
    parser.add_argument("--ref", action="append", default=[])
    parser.add_argument("--file", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--operator-reviewed", action="store_true")
    parser.add_argument("--attestation-url")
    parser.add_argument("--allow-public-github-fetch", action="store_true")
    args = parser.parse_args()
    try:
        if args.mode in ("prepare", "record"):
            record = prepare_record(args.repo, args.issue, args.review_url, args.kind,
                                    args.summary, args.ref)
            if args.mode == "prepare":
                print(json.dumps({"decision": "REVIEW_REQUIRED", "record": record,
                                  "storage": "NOT_PERSISTED", "owner_approval": "NOT_GRANTED"},
                                 sort_keys=True, ensure_ascii=False))
                return 2
            if not args.operator_reviewed or not args.file:
                raise ValueError("Explicit review flag and file are required")
            _file(args.repo, args.file, create=True)
            handoff._capture_handoff_file(args.file, record)
            print(json.dumps({"decision": "RECORDED_UNVERIFIED", "stored": True,
                              "owner_approval": "NOT_GRANTED"}))
            return 0
        if args.mode == "verify-owner-review":
            if not args.file or not args.attestation_url:
                raise ValueError("Explicit memory file and owner attestation required")
            result = verify_owner_review(args.repo, args.file, args.attestation_url,
                                         allow_public_github_fetch=args.allow_public_github_fetch)
            print(json.dumps(result, sort_keys=True, ensure_ascii=False))
            return 2  # A reviewed reference is never execution consent.
        if args.mode == "read":
            if not args.file:
                raise ValueError("Explicit memory file required")
            result = read_record(args.repo, args.file)
        else:
            if not args.directory or not args.issue:
                raise ValueError("Directory and Issue required")
            result = search_records(args.repo, args.directory, args.issue)
    except (OSError, ValueError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        result = {"decision": "BLOCKED", "reason": type(exc).__name__}
    print(json.dumps(result, sort_keys=True, ensure_ascii=False))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
