#!/usr/bin/env python3
"""Ephemeral Paperclip board-only task, document and interaction smoke.

No agent is created, assigned, started or authenticated. No model is called.
Usage: python control_plane.py create <private-receipt.json>
       python control_plane.py recover <private-receipt.json>
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from smoke import BASE, make_restricted_company, request

PLAN_V1 = "# Example plan\n\n1. Inspect tests.\n2. Propose a minimal fix.\n"
PLAN_V2 = "# Example plan\n\n1. Inspect tests.\n2. Add a focused regression check.\n3. Request human review.\n"
COMMENT = "Synthetic board-only checkpoint: scope confirmed, no agent execution."
REASON = "Synthetic CI interaction only; no actual owner decision."


def check(cond: bool, reason: str) -> None:
    if not cond:
        raise RuntimeError(reason)


def expect_stale_conflict(path: str, payload: dict) -> None:
    """Use raw localhost HTTP only to assert a 409, never log the response body."""
    req = Request(
        BASE + path,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with urlopen(req, timeout=20) as response:
            raise RuntimeError(
                f"Stale document write unexpectedly succeeded: HTTP {response.status}"
            )
    except HTTPError as exc:
        if exc.code != 409:
            raise RuntimeError(
                f"Stale document write returned HTTP {exc.code}, expected 409"
            ) from None


def create(receipt_path: Path) -> None:
    company_id = make_restricted_company(
        "Paperclip Control Plane CI",
        "Ephemeral human-only task context test; no agents",
    )
    agents = request("GET", f"/api/companies/{company_id}/agents")
    check(isinstance(agents, list) and len(agents) == 0,
          "The board-only test company must have no agents")

    root = request("POST", f"/api/companies/{company_id}/issues", {
        "title": "Synthetic regression investigation",
        "description": "Test Paperclip control-plane persistence only.",
        "status": "todo",
        "priority": "high",
        "idempotencyKey": "paperclip-phase2-root",
    })
    root_id = root.get("id") if isinstance(root, dict) else None
    check(isinstance(root_id, str) and bool(root_id), "Root issue was not created")
    check(root.get("assigneeAgentId") is None, "Root issue unexpectedly assigned an agent")

    child = request("POST", f"/api/companies/{company_id}/issues", {
        "title": "Synthetic focused regression check",
        "description": "A human-owned checklist item; no execution.",
        "status": "todo",
        "priority": "medium",
        "parentId": root_id,
        "idempotencyKey": "paperclip-phase2-child",
    })
    child_id = child.get("id") if isinstance(child, dict) else None
    check(isinstance(child_id, str) and bool(child_id), "Child issue was not created")
    check(child.get("parentId") == root_id, "Child issue lost its parent")
    check(child.get("assigneeAgentId") is None, "Child unexpectedly assigned an agent")

    changed = request("PATCH", f"/api/issues/{child_id}", {
        "priority": "high",
        "comment": "Synthetic reprioritization; no work has been performed.",
    })
    check(isinstance(changed, dict) and changed.get("priority") == "high",
          "Child issue priority change was not persisted")
    check(isinstance(changed.get("changes"), dict) and
          "priority" in changed["changes"], "Issue change receipt missing priority")

    note = request("POST", f"/api/issues/{root_id}/comments", {"body": COMMENT})
    note_id = note.get("id") if isinstance(note, dict) else None
    check(isinstance(note_id, str) and bool(note_id), "Synthetic comment not created")

    first = request("PUT", f"/api/issues/{root_id}/documents/plan", {
        "title": "Synthetic implementation plan",
        "format": "markdown",
        "body": PLAN_V1,
    })
    first_revision = first.get("latestRevisionId") if isinstance(first, dict) else None
    check(isinstance(first_revision, str) and bool(first_revision),
          "First plan revision was not recorded")
    second = request("PUT", f"/api/issues/{root_id}/documents/plan", {
        "title": "Synthetic implementation plan",
        "format": "markdown",
        "body": PLAN_V2,
        "baseRevisionId": first_revision,
    })
    second_revision = second.get("latestRevisionId") if isinstance(second, dict) else None
    check(isinstance(second_revision, str) and second_revision != first_revision,
          "Plan revision did not advance")
    expect_stale_conflict(f"/api/issues/{root_id}/documents/plan", {
        "title": "Synthetic implementation plan",
        "format": "markdown",
        "body": PLAN_V1,
        "baseRevisionId": first_revision,
    })

    interaction = request("POST", f"/api/issues/{root_id}/interactions", {
        "kind": "request_confirmation",
        "resolverPolicy": "human_only",
        "idempotencyKey": "paperclip-phase2-board-review",
        "title": "Synthetic board review",
        "summary": "Record human-only confirmation; never execute agents.",
        "continuationPolicy": "none",
        "payload": {
            "version": 1,
            "prompt": "Review this synthetic plan without enabling execution?",
            "rejectRequiresReason": True,
            "detailsMarkdown": "Disposable CI example; no production approval.",
            "target": {
                "type": "issue_document",
                "issueId": root_id,
                "documentId": second.get("id"),
                "key": "plan",
                "revisionId": second_revision,
                "revisionNumber": second.get("latestRevisionNumber"),
            },
        },
    })
    interaction_id = interaction.get("id") if isinstance(interaction, dict) else None
    check(isinstance(interaction_id, str) and bool(interaction_id),
          "Human-only review interaction was not created")
    check(interaction.get("effectiveResolverPolicy") == "human_only",
          "Effective interaction policy is not human_only")
    check(interaction.get("status") == "pending",
          "Human-only review must remain pending; no synthetic approval")

    agents_after = request("GET", f"/api/companies/{company_id}/agents")
    check(isinstance(agents_after, list) and len(agents_after) == 0,
          "Agent appeared during board-only control-plane check")

    # Never publish this receipt as an artifact. It contains only ephemeral IDs.
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps({
        "company_id": company_id,
        "root_id": root_id,
        "child_id": child_id,
        "note_id": note_id,
        "interaction_id": interaction_id,
        "first_revision": first_revision,
        "second_revision": second_revision,
    }), encoding="utf-8")
    os.chmod(receipt_path, 0o600)
    print(json.dumps({
        "classification": "PAPERCLIP_BOARD_ONLY_CONTEXT_CREATE",
        "issues_created": 2,
        "hierarchy_verified": True,
        "revision_guard_http": 409,
        "human_only_confirmation_pending": True,
        "assigned_agents": 0,
        "real_agent_trials": 0,
        "model_calls_requested_by_test": 0,
    }, sort_keys=True))


def recover(receipt_path: Path) -> None:
    # A separate interpreter invocation proves context is read back over API,
    # not held in this script's memory. It does not prove restart persistence.
    state = json.loads(receipt_path.read_text(encoding="utf-8"))
    company_id, root_id, child_id = (
        state["company_id"], state["root_id"], state["child_id"]
    )
    root = request("GET", f"/api/issues/{root_id}")
    child = request("GET", f"/api/issues/{child_id}")
    check(root.get("title") == "Synthetic regression investigation",
          "Root issue context was not recovered")
    check(child.get("parentId") == root_id and child.get("priority") == "high",
          "Child hierarchy or updated priority was not recovered")
    check(root.get("assigneeAgentId") is None and
          child.get("assigneeAgentId") is None,
          "An agent was unexpectedly assigned")

    comments = request("GET", f"/api/issues/{root_id}/comments")
    check(isinstance(comments, list) and any(
        isinstance(x, dict) and x.get("id") == state["note_id"] and
        x.get("body") == COMMENT for x in comments
    ), "Original human-board checkpoint was not recovered")

    plan = request("GET", f"/api/issues/{root_id}/documents/plan")
    check(isinstance(plan, dict) and plan.get("body") == PLAN_V2 and
          plan.get("latestRevisionId") == state["second_revision"],
          "Latest plan content or revision was not recovered")
    revisions = request("GET", f"/api/issues/{root_id}/documents/plan/revisions")
    check(isinstance(revisions, list) and len(revisions) >= 2,
          "Plan revision history is not available")

    cards = request("GET", f"/api/issues/{root_id}/interactions")
    check(isinstance(cards, list) and any(
        isinstance(card, dict)
        and card.get("id") == state["interaction_id"]
        and card.get("kind") == "request_confirmation"
        and card.get("status") == "pending"
        and card.get("effectiveResolverPolicy") == "human_only"
        for card in cards
    ), "Pending human-only approval was not recovered")

    company = request("GET", f"/api/companies/{company_id}")
    check(company.get("budgetMonthlyCents") == 0
          and company.get("requireBoardApprovalForNewAgents") is True,
          "Zero-spend/approval settings changed")
    agents = request("GET", f"/api/companies/{company_id}/agents")
    check(isinstance(agents, list) and not agents, "Unexpected agent created")

    print(json.dumps({
        "classification": "PAPERCLIP_BOARD_ONLY_FRESH_PROCESS_READBACK",
        "issue_hierarchy_recovered": True,
        "comment_recovered": True,
        "latest_plan_revision_recovered": True,
        "plan_revision_history_recovered": True,
        "human_only_approval_still_pending": True,
        "organization_approval_gate_still_enabled": True,
        "agents_created": 0,
        "real_agent_trials": 0,
        "model_calls_requested_by_test": 0,
        "server_restarted": False,
        "autonomous_task_orchestration_tested": False,
    }, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in {"create", "recover"}:
        raise SystemExit("Usage: control_plane.py create|recover <private-receipt.json>")
    mode, dest = sys.argv[1], Path(sys.argv[2])
    (create if mode == "create" else recover)(dest)
