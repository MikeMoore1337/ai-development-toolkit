#!/usr/bin/env python3
"""Offline client-policy advisory. Does not launch clients, install skills or pay.

Combines the #394 user/project/task resolver with existing #68 capability
contracts. Neither declared preferences nor a user-supplied session claim proves
that an external client is installed, its skills invoked, or spending authorized.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import client_capabilities
import toolkit_preferences as prefs

ROUTES = {
    "chatgpt": ("chatgpt", client_capabilities.CLIENT_TYPE, "conversation"),
    "chatgpt-plugin": ("chatgpt", client_capabilities.CLIENT_TYPE, "hosted-plugin"),
    "claude-web": ("claude-ai", client_capabilities.CLIENT_TYPE, "conversation"),
    "codex-desktop": ("codex", "FILESYSTEM_SKILL_CLIENT", "desktop"),
    "codex-cli": ("codex", "FILESYSTEM_SKILL_CLIENT", "cli"),
    "claude-code": ("claude-code", "FILESYSTEM_SKILL_CLIENT", "cli"),
    "mcp": (None, "EXTERNAL_PROTOCOL", "protocol"),
    "api": (None, "EXTERNAL_PROTOCOL", "api"),
}
OPERATIONS = frozenset({
    "guidance", "install", "file-write", "git-merge", "deploy",
    "cli-agent", "network", "paid-api", "agent-pilot",
})
PERMISSIONS = {
    "install": ("approvals.file_writes",),
    "file-write": ("approvals.file_writes",),
    "git-merge": ("approvals.git_merge",),
    "deploy": ("approvals.deployment",),
    "cli-agent": ("execution.allow_cli_agents",),
    "network": ("execution.allow_network",),
    "paid-api": ("execution.allow_paid_api", "execution.additional_spend_allowed",
                 "execution.allow_network"),
    "agent-pilot": ("execution.real_agent_pilots",),
}
NO_RUNTIME = "NOT_EXECUTED"
UNKNOWN = "NOT_VERIFIED"
ROOT = Path(__file__).resolve().parents[1]


class RoutingError(ValueError):
    """Invalid cross-client route or invalid trust boundary."""


def _contracts(root: Path) -> tuple[set[str], set[str]]:
    from client_capabilities import load_conversations
    from verify_client_compatibility import load_registry
    # Read only the canonical, validated Toolkit registries, never user-provided
    # replacement registries, executable hooks or external model metadata.
    fs = load_registry(root / "compatibility" / "clients.json")
    chat = load_conversations(root / "compatibility" / "conversational_clients.json")
    return {v["client_id"] for v in fs["clients"]}, {v["client_id"] for v in chat["clients"]}


def _policy_value(policy: dict, dotted: str) -> object:
    section, key = dotted.split(".", 1)
    return policy[section][key]


def assess(
    preference_report: dict, client: str, operation: str = "guidance",
    *, root: Path = ROOT, session_capabilities: dict | None = None,
) -> dict:
    """Decision-support only: even permitted operations remain unexecuted."""
    if operation not in OPERATIONS:
        raise RoutingError("Unsupported operation")
    if client not in ROUTES:
        raise RoutingError("Unsupported client route")
    if not isinstance(preference_report, dict) or preference_report.get(
            "classification") != "READ_ONLY_PREFERENCES_PREVIEW" or (
            preference_report.get("execution_authorized") is not False):
        raise RoutingError("Invalid or non-preview preferences")
    effective = preference_report.get("effective")
    if not isinstance(effective, dict):
        raise RoutingError("Missing effective preferences")
    # The *schema-valid* policy may be supplied via resolve() or preview().
    try:
        validated = prefs.resolve({"schema_version": 1, **effective})["effective"]
    except (prefs.PreferencesError, KeyError, TypeError) as exc:
        raise RoutingError("Invalid effective policy") from exc
    if effective != validated:
        raise RoutingError("Inconsistent preferences")
    fs, chats = _contracts(root)
    contract, ctype, transport = ROUTES[client]
    if contract and contract not in (chats if ctype == client_capabilities.CLIENT_TYPE else fs):
        raise RoutingError("Unknown contract in Toolkit registry")
    reasons: list[str] = []
    if client not in effective["clients"]["allowed"]:
        reasons.append("CLIENT_DISALLOWED")
    if transport == "cli" and not effective["execution"]["allow_cli_agents"]:
        reasons.append("CLI_AGENTS_DISABLED")
    if transport == "api" and not all(effective["execution"][k] for k in (
            "allow_paid_api", "additional_spend_allowed", "allow_network")):
        reasons.append("PAID_ROUTE_RESTRICTED")
    for key in PERMISSIONS.get(operation, ()):
        if _policy_value(effective, key) in (False, "deny"):
            reasons.append("RESTRICTION:" + key)
    if operation == "cli-agent" and transport != "cli":
        reasons.append("NOT_A_CLI_ROUTE")
    if operation == "paid-api" and transport != "api":
        reasons.append("NOT_AN_API_ROUTE")
    if operation == "agent-pilot" and transport not in {"cli", "desktop"}:
        reasons.append("PILOT_NOT_SUPPORTED_BY_ROUTE")
    cap_data = None
    selected = "MANUAL_FALLBACK"
    if session_capabilities is not None:
        if ctype not in {"FILESYSTEM_SKILL_CLIENT", client_capabilities.CLIENT_TYPE}:
            raise RoutingError("Session claims unsupported for generic protocols")
        if not isinstance(session_capabilities, dict):
            raise RoutingError("Invalid capability claims")
        try:
            cap_data = client_capabilities.select_route(
                ctype, session_capabilities,
                installed_skill=False, toolkit_url=True, toolkit_attachment=False,
            )
        except (client_capabilities.CapabilityError, TypeError) as exc:
            raise RoutingError("Invalid session capabilities") from exc
        selected = cap_data["route"]
    status = ("BLOCKED_BY_POLICY" if reasons else
              "GUIDANCE_ONLY" if operation == "guidance" else "REVIEW_REQUIRED")
    return {
        "schema_version": 1,
        "client": client,
        "client_contract": contract or "NO_CLIENT_CONTRACT",
        "transport": transport,
        "operation": operation,
        "status": status,
        "policy_reasons": sorted(set(reasons)),
        "capability_route_candidate": selected,
        "capability_basis": "USER_DECLARED_NOT_VERIFIED" if cap_data else UNKNOWN,
        "live_installation": UNKNOWN,
        "L4_skill_discovery": UNKNOWN,
        "L5_skill_invocation": UNKNOWN,
        "L6_effectiveness": "NOT_MEASURED",
        "execution": NO_RUNTIME,
        "model_calls": 0,
        "paid_api_calls": 0,
        "project_files_changed": False,
        "approval_required_for_real_actions": True,
        "execution_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--client", choices=sorted(ROUTES), required=True)
    p.add_argument("--operation", choices=sorted(OPERATIONS), default="guidance")
    p.add_argument("--target", type=Path)
    p.add_argument("--user-config", type=Path)
    p.add_argument("--project-config", type=Path)
    p.add_argument("--task-config", type=Path)
    args = p.parse_args(argv)
    try:
        preferences = prefs.preview(args.target, user_path=args.user_config,
                                    project_path=args.project_config,
                                    task_path=args.task_config)
        report = assess(preferences, args.client, args.operation)
    except (prefs.PreferencesError, RoutingError, OSError, TypeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if report["status"] != "BLOCKED_BY_POLICY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
