#!/usr/bin/env python3
"""Opt-in, single-writer GitHub Issue queue for an authorized Codex host.

The controller never starts models or agents. Only explicit 'finish --merge'
may call gh pr merge, after checking exact PR head evidence.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

MAX_ITEMS = 1000
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
BLOCK_LABELS = {"hold", "blocked", "do-not-automate", "do not automate",
                "manual-only", "needs-owner-approval", "backlog", "draft"}
DESIGN_LABELS = {"approval:design", "requires-design-approval"}
BLOCK_TITLE_MARKERS = re.compile(r"\[(?:HOLD|BLOCKED|DRAFT|PAUSED|BACKLOG|NO_GO)\]", re.I)
PR_TITLE_ISSUE_RE = re.compile(r"(?<![\w/])#([1-9][0-9]*)\b")
DEP_LINE = re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:blocked by|depends on|requires)\s*:?\s*(.*)$")
ISSUE_REF = re.compile(r"(?<![\w/])#([1-9][0-9]*)\b")
CLOSE_REF = re.compile(r"(?im)\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#([1-9][0-9]*)\b")


class QueueError(ValueError):
    """Fail closed on malformed or unverifiable queue state."""


def validate_repo(repo: str) -> str:
    if not REPO_RE.fullmatch(repo) or ".." in repo:
        raise QueueError("INVALID_REPOSITORY")
    return repo


def gh(*args: str) -> Any:
    try:
        cp = subprocess.run(["gh", *args], capture_output=True, text=True,
                            encoding="utf-8", timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise QueueError("GITHUB_CLIENT_UNAVAILABLE") from exc
    if cp.returncode:
        raise QueueError("GITHUB_COMMAND_FAILED: " + " ".join(args[:2]))
    return cp.stdout


def gh_json(*args: str) -> Any:
    try:
        return json.loads(gh(*args))
    except (ValueError, TypeError) as exc:
        raise QueueError("INVALID_GITHUB_JSON") from exc


def live_snapshot(repo: str, issue_scope: list[int] | None = None) -> dict[str, Any]:
    validate_repo(repo)
    issues = gh_json("issue", "list", "-R", repo, "--state", "open",
                     "--limit", str(MAX_ITEMS), "--json",
                     "number,title,body,state,labels,url")
    prs = gh_json("pr", "list", "-R", repo, "--state", "open",
                  "--limit", str(MAX_ITEMS), "--json",
                  "number,title,body,headRefName,baseRefName,isDraft,url")
    if not isinstance(issues, list) or not isinstance(prs, list):
        raise QueueError("INVALID_GITHUB_SNAPSHOT")
    if len(issues) >= MAX_ITEMS or len(prs) >= MAX_ITEMS:
        raise QueueError("GITHUB_RESULT_LIMIT_REACHED")
    # Fetch historical prerequisites and ALL selected scope members, including
    # closed predecessors no longer referenced by any currently open Issue.
    # Without this, sequential 1 -> 2 -> 3 stops after #2 is closed because
    # #1 disappears from the open-Issue snapshot and plan rejects the scope.
    indexed = {item["number"] for item in issues}
    required = set(issue_scope or ()) | set().union(
        *(dependencies(item) for item in issues))
    for number in sorted(required - indexed):
        remote = gh_json("issue", "view", str(number), "-R", repo,
                         "--json", "number,title,body,state,labels,url")
        if (not isinstance(remote, dict) or type(remote.get("number")) is not int or
                remote["number"] != number or
                remote.get("state") not in ("OPEN", "CLOSED")):
            raise QueueError("ISSUE_REFERENCE_MISMATCH")
        issues.append(remote)
    return {"issues": issues, "pull_requests": prs}


def labels(issue: dict[str, Any]) -> set[str]:
    entries = issue.get("labels", [])
    if not isinstance(entries, list):
        raise QueueError("INVALID_LABELS")
    return {str(item.get("name", "")).strip().lower() for item in entries
            if isinstance(item, dict)}


def dependencies(issue: dict[str, Any]) -> set[int]:
    body = issue.get("body") or ""
    if not isinstance(body, str):
        raise QueueError("INVALID_ISSUE_BODY")
    result: set[int] = set()
    for line in DEP_LINE.findall(body):
        result.update(int(n) for n in ISSUE_REF.findall(line))
    return result


def priority(issue: dict[str, Any]) -> int:
    found = labels(issue)
    for i in range(4):
        if found & {f"p{i}", f"priority:p{i}", f"priority: p{i}"}:
            return i
    title = issue.get("title") or ""
    match = re.search(r"\[P([0-3])\]", title, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 4


def pr_issue_numbers(pr: dict[str, Any]) -> set[int]:
    body = pr.get("body") or ""
    result = {int(n) for n in CLOSE_REF.findall(body)}
    # Title references are conservatively treated as already in progress:
    # e.g. fix(#401), feat: something (#437). The PR body may contain
    # unrelated references, so only explicit closing keywords count there.
    title = pr.get("title") or ""
    if not isinstance(title, str):
        raise QueueError("INVALID_PULL_REQUEST_TITLE")
    result.update(int(n) for n in PR_TITLE_ISSUE_RE.findall(title))
    # A deterministic orchestrator-owned branch is also a valid association.
    match = re.match(r"^issue-orchestrator/issue-([1-9][0-9]*)(?:-|$)",
                     str(pr.get("headRefName", "")))
    if match:
        result.add(int(match.group(1)))
    return result


def require_snapshot(snapshot: dict[str, Any]) -> tuple[dict[int, dict], list[dict]]:
    if not isinstance(snapshot, dict):
        raise QueueError("INVALID_SNAPSHOT")
    issues, prs = snapshot.get("issues"), snapshot.get("pull_requests")
    if not isinstance(issues, list) or not isinstance(prs, list):
        raise QueueError("INVALID_SNAPSHOT_COLLECTIONS")
    by_number: dict[int, dict] = {}
    for issue in issues:
        if not isinstance(issue, dict) or type(issue.get("number")) is not int:
            raise QueueError("INVALID_ISSUE")
        number = issue["number"]
        if number < 1 or number in by_number or issue.get("state") not in ("OPEN", "CLOSED"):
            raise QueueError("INVALID_ISSUE_STATE")
        by_number[number] = issue
    if any(not isinstance(pr, dict) for pr in prs):
        raise QueueError("INVALID_PULL_REQUEST")
    return by_number, prs


def is_cyclic(start: int, graph: dict[int, set[int]]) -> bool:
    remaining = list(graph.get(start, set()))
    visited: set[int] = set()
    while remaining:
        item = remaining.pop()
        if item == start:
            return True
        if item not in visited:
            visited.add(item)
            remaining.extend(graph.get(item, set()))
    return False


def parse_issue_scope(raw: str | None) -> list[int] | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw or len(raw) > 256:
        raise QueueError("INVALID_ISSUE_SCOPE")
    parts = raw.split(",")
    if len(parts) > 30 or any(not re.fullmatch(r"[1-9][0-9]*", p) for p in parts):
        raise QueueError("INVALID_ISSUE_SCOPE")
    numbers = [int(p) for p in parts]
    if len(numbers) != len(set(numbers)):
        raise QueueError("DUPLICATE_ISSUE_IN_SCOPE")
    return sorted(numbers)


def resolve_scope(state: dict[str, Any], requested: list[int] | None) -> list[int] | None:
    stored = state.get("issue_scope")
    if stored is not None:
        if (not isinstance(stored, list) or not stored or
                len(stored) > 30 or
                any(type(n) is not int or n <= 0 for n in stored) or
                stored != sorted(set(stored))):
            raise QueueError("INVALID_PERSISTED_ISSUE_SCOPE")
        if requested is not None and requested != stored:
            raise QueueError("ISSUE_SCOPE_CHANGE_REFUSED")
        return stored
    if requested is not None and state.get("entries"):
        raise QueueError("EXISTING_QUEUE_CANNOT_BE_RESCOPED")
    return requested


def plan(snapshot: dict[str, Any], state: dict[str, Any], branch: str,
         *, requested_scope: list[int] | None = None) -> dict[str, Any]:
    by_num, prs = require_snapshot(snapshot)
    scope = resolve_scope(state, requested_scope)
    if scope is not None and set(scope) - set(by_num):
        raise QueueError("SELECTED_ISSUE_NOT_FOUND")
    entries = state.get("entries", {})
    if not isinstance(entries, dict) or not isinstance(branch, str) or not branch:
        raise QueueError("INVALID_QUEUE_STATE")
    open_prs: dict[int, list[int]] = {}
    for pr in prs:
        for number in pr_issue_numbers(pr):
            open_prs.setdefault(number, []).append(pr.get("number", 0))
    graph = {number: {dep for dep in dependencies(issue)
                       if dep in by_num and by_num[dep]["state"] == "OPEN"}
             for number, issue in by_num.items() if issue["state"] == "OPEN"}
    available, excluded = [], []
    for number, issue in by_num.items():
        if issue["state"] != "OPEN" or (scope is not None and number not in scope):
            continue
        own = entries.get(str(number), {})
        if not isinstance(own, dict):
            raise QueueError("INVALID_TASK_STATE")
        stage = own.get("status", "NEW")
        lset = labels(issue)
        reasons = []
        if lset & BLOCK_LABELS:
            reasons.append("EXCLUDED_LABEL")
        if BLOCK_TITLE_MARKERS.search(str(issue.get("title") or "")):
            reasons.append("EXCLUDED_TITLE")
        if open_prs.get(number):
            reasons.append("EXISTING_OPEN_PR")
        if stage in ("IN_PROGRESS", "WAITING_DESIGN", "BLOCKED", "DONE"):
            reasons.append(stage)
        preview_needed = bool(lset & DESIGN_LABELS and own.get("design_approved") is not True)
        deps = dependencies(issue)
        if number in deps:
            reasons.append("SELF_DEPENDENCY")
        if is_cyclic(number, graph):
            reasons.append("DEPENDENCY_CYCLE")
        for dependent in sorted(deps):
            target = by_num.get(dependent)
            if target is None:
                reasons.append("UNKNOWN_DEPENDENCY")
            elif target.get("state") != "CLOSED":
                reasons.append("OPEN_DEPENDENCY")
        item = {"number": number, "title": issue.get("title", ""),
                "priority": priority(issue), "dependencies": sorted(deps),
                "phase": "DESIGN_PREVIEW" if preview_needed else "IMPLEMENTATION",
                "reasons": sorted(set(reasons))}
        (excluded if reasons else available).append(item)
    available.sort(key=lambda x: (x["priority"], x["number"]))
    excluded.sort(key=lambda x: (x["priority"], x["number"]))
    return {"available": available, "excluded": excluded,
            "active": state.get("active"), "branch": branch, "issue_scope": scope,
            "complete": not available and state.get("active") is None,
            "execution": "NOT_RUN"}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def state_directory(repo: str, override: str | None, *, create: bool = False) -> Path:
    root = Path(override).expanduser() if override else (
        Path.home() / ".adt" / "issue-orchestrator" / repo.split("/")[0] / repo.split("/")[1]
    )
    if not root.is_absolute():
        raise QueueError("STATE_DIRECTORY_MUST_BE_ABSOLUTE")
    # Refuse symlink/junction path components, including pre-existing parents.
    for path in (root, *root.parents):
        if path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction()):
            raise QueueError("LINKED_STATE_DIRECTORY")
    if create:
        root.mkdir(parents=True, exist_ok=True, mode=0o700)
    if root.exists() and not root.is_dir():
        raise QueueError("STATE_DIRECTORY_NOT_DIRECTORY")
    if root.exists() and os.name != "nt" and root.stat().st_mode & 0o077:
        raise QueueError("STATE_DIRECTORY_NOT_PRIVATE")
    return root


@contextmanager
def exclusive(root: Path):
    lock = root / "queue.lock"
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(lock, flags, 0o600)
    except FileExistsError as exc:
        raise QueueError("QUEUE_LOCK_EXISTS_CHECK_OWNER_BEFORE_REMOVING") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(str(os.getpid()))
            handle.flush()
            os.fsync(handle.fileno())
        yield
    finally:
        lock.unlink(missing_ok=True)


def read_state(root: Path, repo: str, branch: str) -> dict[str, Any]:
    path = root / "state.json"
    if path.is_symlink():
        raise QueueError("LINKED_STATE_FILE")
    if not path.exists():
        return {"schema": 1, "repo": repo, "branch": branch,
                "active": None, "entries": {}}
    if path.stat().st_size > 2_000_000:
        raise QueueError("STATE_FILE_TOO_LARGE")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise QueueError("CORRUPT_STATE_FILE") from exc
    if (not isinstance(state, dict) or state.get("schema") != 1 or
            state.get("repo") != repo or state.get("branch") != branch or
            not isinstance(state.get("entries"), dict)):
        raise QueueError("STATE_CONTEXT_MISMATCH")
    current = state.get("active")
    if current is not None and (type(current) is not int or current < 1):
        raise QueueError("INVALID_ACTIVE_ISSUE")
    for key, task in state["entries"].items():
        if (not isinstance(key, str) or not key.isdecimal() or
                not isinstance(task, dict) or
                task.get("status") not in
                ("NEW", "READY", "IN_PROGRESS", "WAITING_DESIGN", "BLOCKED", "DONE")):
            raise QueueError("INVALID_STATE_ENTRY")
    if current is not None and state["entries"].get(str(current), {}).get("status") != "IN_PROGRESS":
        raise QueueError("INCONSISTENT_ACTIVE_ISSUE")
    resolve_scope(state, None)
    return state


def write_state(root: Path, state: dict[str, Any]) -> None:
    # Atomic replace: interrupted writes leave the prior valid snapshot.
    fd, name = tempfile.mkstemp(prefix=".state-", suffix=".tmp", dir=root)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True, indent=2, ensure_ascii=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, root / "state.json")
        if os.name != "nt":
            directory_fd = os.open(root, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def approval_found(comments: list[dict], owner: str, issue: int,
                   revision: str, requested_at: str) -> bool:
    if not SHA_RE.fullmatch(revision) or not owner:
        raise QueueError("INVALID_DESIGN_APPROVAL_REQUEST")
    expected = f"/approve-design #{issue} {revision}"
    revoked = f"/reject-design #{issue} {revision}"
    decision = False
    for c in sorted(comments, key=lambda x: x.get("createdAt") or ""):
        if c.get("author", {}).get("login") != owner:
            continue
        if (c.get("createdAt") or "") < requested_at:
            continue
        text = str(c.get("body", "")).strip()
        if text == expected:
            decision = True
        elif text == revoked:
            decision = False
    return decision


def live_design_approved(repo: str, number: int, task: dict) -> bool:
    revision = task.get("preview_revision")
    requested = task.get("requested_at")
    if not isinstance(revision, str) or not isinstance(requested, str):
        return False
    owner = gh_json("repo", "view", repo, "--json", "owner").get("owner", {}).get("login")
    if not owner:
        raise QueueError("OWNER_NOT_VERIFIED")
    comments = gh_json("issue", "view", str(number), "-R", repo,
                       "--json", "comments").get("comments", [])
    if not isinstance(comments, list):
        raise QueueError("INVALID_DESIGN_COMMENTS")
    return approval_found(comments, owner, number, revision, requested)


def check_pr(pr: dict, issue: int, branch: str, *, merged: bool, repo: str) -> str:
    if not isinstance(pr, dict) or pr.get("baseRefName") != branch:
        raise QueueError("PR_BASE_BRANCH_MISMATCH")
    if (pr.get("headRepository") or {}).get("nameWithOwner") != repo:
        raise QueueError("CROSS_REPOSITORY_PR_REFUSED")
    head = str(pr.get("headRefOid") or "")
    if not SHA_RE.fullmatch(head):
        raise QueueError("PR_HEAD_SHA_NOT_VERIFIED")
    own_branch = re.fullmatch(
        rf"issue-orchestrator/issue-{issue}(?:-[A-Za-z0-9._/-]+)?",
        str(pr.get("headRefName", "")))
    body_refs = {int(n) for n in CLOSE_REF.findall(pr.get("body") or "")}
    if issue not in body_refs or not own_branch:
        raise QueueError("PR_NOT_ASSOCIATED_WITH_ISSUE")
    if pr.get("isDraft"):
        raise QueueError("DRAFT_PR")
    if merged:
        if not pr.get("mergedAt") or not pr.get("mergeCommit"):
            raise QueueError("PR_NOT_MERGED")
    elif pr.get("mergeStateStatus") != "CLEAN":
        raise QueueError("PR_NOT_MERGEABLE")
    checks = pr.get("statusCheckRollup")
    if not isinstance(checks, list) or not checks:
        raise QueueError("CI_EVIDENCE_MISSING")
    for check in checks:
        if not isinstance(check, dict):
            raise QueueError("INVALID_CI_EVIDENCE")
        status = check.get("status")
        conclusion = check.get("conclusion")
        state = check.get("state")
        if status is not None and status != "COMPLETED":
            raise QueueError("CI_NOT_COMPLETE")
        if conclusion is not None:
            if conclusion not in ("SUCCESS", "NEUTRAL"):
                raise QueueError("CI_NOT_SUCCESS")
        elif state != "SUCCESS":
            raise QueueError("CI_NOT_SUCCESS")
    if pr.get("reviewDecision") == "CHANGES_REQUESTED":
        raise QueueError("CHANGES_REQUESTED")
    if pr.get("reviewDecision") == "REVIEW_REQUIRED":
        raise QueueError("REVIEW_REQUIRED")
    return head


def pr_view(repo: str, number: int) -> dict:
    return gh_json("pr", "view", str(number), "-R", repo, "--json",
                   "number,body,headRefName,headRefOid,baseRefName,isDraft,"
                   "mergeStateStatus,mergedAt,mergeCommit,reviewDecision,statusCheckRollup,headRepository")


def execute(args: argparse.Namespace) -> dict[str, Any]:
    repo = validate_repo(args.repo)
    root = state_directory(repo, args.state_dir, create=args.action not in ("plan", "status"))
    branch = args.branch
    requested_scope = parse_issue_scope(getattr(args, "issues", None))
    if args.action == "plan":
        state = read_state(root, repo, branch)
        effective_scope = resolve_scope(state, requested_scope)
        return plan(live_snapshot(repo, effective_scope), state, branch,
                    requested_scope=requested_scope)
    if args.action == "status":
        return read_state(root, repo, branch)
    with exclusive(root):
        state = read_state(root, repo, branch)
        entries = state["entries"]
        current = state["active"]
        if args.action == "start":
            if current is not None:
                raise QueueError("ONE_WRITER_ALREADY_ACTIVE")
            selected = resolve_scope(state, requested_scope)
            queue = plan(live_snapshot(repo, selected), state, branch,
                         requested_scope=requested_scope)["available"]
            if not queue:
                return {"status": "NO_AVAILABLE_ISSUES"}
            target = queue[0]["number"]
            if selected is not None and "issue_scope" not in state:
                state["issue_scope"] = selected
            entries[str(target)] = {**entries.get(str(target), {}),
                                    "status": "IN_PROGRESS", "started_at": utcnow(),
                                    "phase": queue[0]["phase"]}
            state["active"] = target
            write_state(root, state)
            return {"status": "CLAIMED", "issue": target, "branch": branch,
                    "phase": queue[0]["phase"]}
        number = args.issue
        if number is None or str(number) not in entries:
            raise QueueError("ISSUE_NOT_CLAIMED")
        task = entries[str(number)]
        if args.action == "design-request":
            if current != number or task.get("status") != "IN_PROGRESS":
                raise QueueError("DESIGN_REQUEST_REQUIRES_ACTIVE_ISSUE")
            if not SHA_RE.fullmatch(args.revision):
                raise QueueError("DESIGN_REVISION_MUST_BE_COMMIT_SHA")
            if not args.preview_url.startswith("https://"):
                raise QueueError("PREVIEW_URL_REQUIRES_HTTPS")
            task.update(status="WAITING_DESIGN", design_approved=False,
                        preview_revision=args.revision, preview_url=args.preview_url,
                        requested_at=utcnow())
            state["active"] = None
            write_state(root, state)
            return {"status": "WAITING_DESIGN", "issue": number,
                    "owner_comment_required": f"/approve-design #{number} {args.revision}",
                    "preview_url": args.preview_url}
        if args.action == "approve":
            if task.get("status") != "WAITING_DESIGN":
                raise QueueError("ISSUE_NOT_WAITING_FOR_DESIGN")
            if not live_design_approved(repo, number, task):
                return {"status": "WAITING_DESIGN", "issue": number}
            task.update(status="READY", design_approved=True, approved_at=utcnow())
            write_state(root, state)
            return {"status": "DESIGN_APPROVED", "issue": number}
        if args.action == "retry":
            if current is not None or task.get("status") != "BLOCKED":
                raise QueueError("RETRY_REQUIRES_NO_ACTIVE_WRITER")
            task.update(status="READY", retry_at=utcnow(), reason="")
            write_state(root, state)
            return {"status": "RETRY_READY", "issue": number}
        if args.action == "block":
            if current != number or task.get("status") != "IN_PROGRESS":
                raise QueueError("BLOCK_REQUIRES_ACTIVE_ISSUE")
            task.update(status="BLOCKED", reason=args.reason, blocked_at=utcnow())
            state["active"] = None
            write_state(root, state)
            return {"status": "BLOCKED", "issue": number}
        if args.action == "finish":
            if current != number or task.get("status") != "IN_PROGRESS":
                raise QueueError("FINISH_REQUIRES_ACTIVE_ISSUE")
            if task.get("phase") == "DESIGN_PREVIEW" and task.get("design_approved") is not True:
                raise QueueError("DESIGN_APPROVAL_REQUIRED_BEFORE_MERGE")
            latest_issue = gh_json("issue", "view", str(number), "-R", repo,
                                   "--json", "labels")
            requires_design = bool(labels(latest_issue) & DESIGN_LABELS or
                                   task.get("preview_revision"))
            if requires_design and (task.get("design_approved") is not True or
                                    not live_design_approved(repo, number, task)):
                raise QueueError("DESIGN_APPROVAL_MISSING_OR_REVOKED")
            pr = pr_view(repo, args.pr)
            head = check_pr(pr, number, branch, merged=bool(pr.get("mergedAt")), repo=repo)
            if not pr.get("mergedAt"):
                if not args.merge:
                    return {"status": "AWAITING_MERGE", "issue": number,
                            "pr": args.pr, "verified_head": head}
                gh("pr", "merge", str(args.pr), "-R", repo, "--squash",
                   "--match-head-commit", head)
                pr = pr_view(repo, args.pr)
                if pr.get("headRefOid") != head:
                    raise QueueError("HEAD_CHANGED_DURING_MERGE")
            check_pr(pr, number, branch, merged=True, repo=repo)
            if args.close_issue:
                issue_info = gh_json("issue", "view", str(number), "-R", repo,
                                     "--json", "state")
                if issue_info.get("state") == "OPEN":
                    gh("issue", "close", str(number), "-R", repo)
            task.update(status="DONE", pr=args.pr, head_sha=head,
                        merge_sha=(pr["mergeCommit"] or {}).get("oid"),
                        finished_at=utcnow())
            state["active"] = None
            write_state(root, state)
            return {"status": "DONE", "issue": number, "pr": args.pr,
                    "head_sha": head, "merge_sha": task["merge_sha"]}
        raise QueueError("UNKNOWN_ACTION")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "status", "start", "design-request",
                                            "approve", "block", "retry", "finish"))
    parser.add_argument("--repo", required=True, help="GitHub owner/repository")
    parser.add_argument("--branch", required=True, help="Authorized delivery branch")
    parser.add_argument("--state-dir", help="Private, absolute directory outside repository")
    parser.add_argument("--issues", help="Pilot allowlist: comma-separated Issue numbers; persisted on first claim")
    parser.add_argument("--issue", type=int)
    parser.add_argument("--revision", default="")
    parser.add_argument("--preview-url", default="")
    parser.add_argument("--reason", default="")
    parser.add_argument("--pr", type=int)
    parser.add_argument("--close-issue", action="store_true",
                        help="Explicit opt-in: close issue only after verified merge")
    parser.add_argument("--merge", action="store_true",
                        help="Explicit opt-in: merge verified PR without --admin")
    args = parser.parse_args(argv)
    try:
        if args.action in ("design-request", "approve", "block", "retry", "finish") and (
                args.issue is None or args.issue < 1):
            raise QueueError("ISSUE_NUMBER_REQUIRED")
        if args.action == "finish" and (args.pr is None or args.pr < 1):
            raise QueueError("PR_NUMBER_REQUIRED")
        if args.action == "block" and not args.reason.strip():
            raise QueueError("BLOCK_REASON_REQUIRED")
        result = execute(args)
    except (QueueError, OSError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
