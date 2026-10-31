#!/usr/bin/env python3
"""Explicit project-reviewed reference index. No second database, ingestion or inference."""
from __future__ import annotations

import argparse
import hmac
import json
import re
import subprocess
import unicodedata
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
    parser.add_argument("mode", choices=("prepare", "record", "read", "search"))
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--issue")
    parser.add_argument("--review-url")
    parser.add_argument("--kind", choices=sorted(KINDS))
    parser.add_argument("--summary")
    parser.add_argument("--ref", action="append", default=[])
    parser.add_argument("--file", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--operator-reviewed", action="store_true")
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
