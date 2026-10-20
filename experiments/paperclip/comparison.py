#!/usr/bin/env python3
"""Read-only GitHub baseline against ephemeral Paperclip board state.

This is NOT an agent A/B benchmark. GitHub Issues/PR remain authoritative.
No GitHub writes, model invocations, agent creations, or credentials.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from smoke import request

REPO = "MikeMoore1337/ai-development-toolkit"
ISSUE = 80
PR = 81
BRANCH = "experiment/paperclip-zero-spend-smoke"
BASE_URL = f"https://api.github.com/repos/{REPO}"


def require(predicate: bool, reason: str) -> None:
    if not predicate:
        raise RuntimeError(reason)


def github_get(suffix: str) -> dict:
    # Only two known, public, read-only endpoints. Never use API credentials.
    if suffix not in {f"/issues/{ISSUE}", f"/pulls/{PR}"}:
        raise RuntimeError("Unapproved GitHub endpoint")
    req = Request(BASE_URL + suffix, headers={
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ai-development-toolkit-paperclip-pilot",
    }, method="GET")
    try:
        with urlopen(req, timeout=15) as response:
            if response.status != 200:
                raise RuntimeError(f"GitHub read failed: HTTP {response.status}")
            data = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"GitHub read failed: HTTP {exc.code}") from None
    except URLError:
        raise RuntimeError("GitHub is unreachable from ephemeral CI") from None
    require(isinstance(data, dict), "GitHub response is not an object")
    return data


def main(receipt: Path) -> None:
    state = json.loads(receipt.read_text(encoding="utf-8"))
    gh_issue = github_get(f"/issues/{ISSUE}")
    gh_pr = github_get(f"/pulls/{PR}")
    require(gh_issue.get("number") == ISSUE and gh_issue.get("state") == "open",
            "GitHub authoritative issue is unavailable or closed")
    require("pull_request" not in gh_issue, "GitHub issue unexpectedly a PR")
    require(isinstance(gh_issue.get("body"), str) and
            "TECHNICAL_CONTROL_PLANE_PASS" in gh_issue["body"],
            "GitHub issue does not include the prior technical result")
    require(gh_pr.get("number") == PR and gh_pr.get("state") == "open"
            and gh_pr.get("draft") is True and gh_pr.get("merged") is False,
            "GitHub pilot PR is not open, unmerged and draft")
    require((gh_pr.get("head") or {}).get("ref") == BRANCH
            and (gh_pr.get("base") or {}).get("ref") == "main",
            "GitHub pilot PR target or source branch changed")

    root = request("GET", f"/api/issues/{state['root_id']}")
    child = request("GET", f"/api/issues/{state['child_id']}")
    plan = request("GET", f"/api/issues/{state['root_id']}/documents/plan")
    interactions = request("GET", f"/api/issues/{state['root_id']}/interactions")
    require(isinstance(root, dict) and root.get("title") ==
            "Synthetic regression investigation",
            "Synthetic Paperclip root task missing")
    require(isinstance(child, dict) and
            child.get("parentId") == state["root_id"],
            "Synthetic Paperclip subtask missing")
    require(isinstance(plan, dict) and
            plan.get("latestRevisionId") == state["second_revision"],
            "Paperclip latest plan revision missing")
    require(isinstance(interactions, list) and any(
        isinstance(item, dict)
        and item.get("id") == state["interaction_id"]
        and item.get("status") == "pending"
        and item.get("effectiveResolverPolicy") == "human_only"
        for item in interactions
    ), "Paperclip pending human-only request missing")

    # Different tasks/systems were inspected: this does not compare throughput
    # or measure identical-task performance. No fabricated parity/quality score.
    print(json.dumps({
        "classification": "PAPERCLIP_VS_GITHUB_STRUCTURAL_READ_ONLY_NOT_AGENT_AB",
        "github_source_of_truth_verified": True,
        "github_issue_and_draft_pr_read": True,
        "github_http_gets": 2,
        "github_writes_performed": 0,
        "paperclip_synthetic_parent_child_verified": True,
        "paperclip_revision_and_human_review_verified": True,
        "paperclip_http_gets": 4,
        "autonomous_workflow_comparison": "NOT_PERFORMED",
        "same_task_execution_compared": False,
        "measured_productivity_improvement": False,
        "github_bidirectional_sync_tested": False,
        "server_restarted": False,
        "agents_created": 0,
        "real_agent_trials": 0,
        "model_calls_requested_by_test": 0,
    }, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: comparison.py <private-receipt.json>")
    main(Path(sys.argv[1]))
