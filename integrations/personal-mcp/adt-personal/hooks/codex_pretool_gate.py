#!/usr/bin/env python3
"""Optional Codex PreToolUse projection of the existing offline reviewer.

This is a guardrail, not a security boundary: Codex can skip hooks or continue
when a hook fails. This module never installs itself or executes tool input.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

from pretool_gate_review import (
    ReviewError, _nonstandard_number, _unique_object, review_event,
)

MAX_EVENT_BYTES = 65536
MAX_NAME_CHARS = 512
REQUIRED_FIELDS = frozenset({
    "session_id", "cwd", "hook_event_name", "tool_use_id", "tool_name", "tool_input",
})
OPTIONAL_FIELDS = frozenset({
    "transcript_path", "model", "permission_mode", "turn_id", "agent_id", "agent_type",
})


def deny(reason: str) -> dict[str, object]:
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}


def _inside_project(root: Path, candidate: object) -> bool:
    """Resolve existing directories, including Windows symlinks and junctions.

    Filesystem state can change after this check; this does not attest host
    isolation. An absent or unresolvable effective directory never passes.
    """
    if (not isinstance(candidate, str) or not candidate or len(candidate) > 4096
            or "\x00" in candidate):
        return False
    try:
        path = Path(candidate)
        if not path.is_absolute():
            return False
        resolved = path.resolve(strict=True)
        if not resolved.is_dir():
            return False
        resolved.relative_to(root)
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def evaluate(event: object, project_root: Path, assume_local_exec_cwd: bool = False) -> dict[str, object]:
    if not isinstance(event, dict):
        return deny("Invalid hook event")
    keys = set(event)
    if not REQUIRED_FIELDS <= keys or not keys <= REQUIRED_FIELDS | OPTIONAL_FIELDS:
        return deny("Invalid hook event")
    if event.get("hook_event_name") != "PreToolUse":
        return deny("Invalid hook event")
    for key in ("session_id", "tool_use_id", "tool_name"):
        value = event.get(key)
        if (not isinstance(value, str) or not value or len(value) > MAX_NAME_CHARS
                or any(ord(ch) < 32 or 0xD800 <= ord(ch) <= 0xDFFF for ch in value)):
            return deny("Invalid hook event")
    if not isinstance(event.get("tool_input"), dict):
        return deny("Invalid hook event")
    for key in ("model", "permission_mode", "turn_id", "agent_id", "agent_type"):
        if key in event and (not isinstance(event[key], str) or len(event[key]) > 4096):
            return deny("Invalid hook event")
    for key in ("transcript_path",):
        if key in event and event[key] is not None and (
                not isinstance(event[key], str) or len(event[key]) > 4096):
            return deny("Invalid hook event")
    try:
        if not project_root.is_absolute():
            return deny("Project root unavailable")
        root = project_root.resolve(strict=True)
        if not root.is_dir():
            return deny("Project root unavailable")
    except (OSError, RuntimeError, ValueError):
        return deny("Project root unavailable")
    if not _inside_project(root, event.get("cwd")):
        return deny("Session directory outside project")

    name = event["tool_name"]
    payload = event["tool_input"]
    if name == "Bash":
        # This owner opt-in is an assumption about the pinned local host,
        # never an attestation from model-controlled event data. Remote and
        # unverified host versions must not use it.
        if not assume_local_exec_cwd:
            return deny("Local execution directory semantics not verified")
        if set(payload) != {"command"} or not isinstance(payload.get("command"), str):
            return deny("Invalid shell input")
        projected = {"schema_version": 1, "tool_name": "Bash", "tool_input": payload}
    elif name == "apply_patch":
        if set(payload) != {"command"} or not isinstance(payload.get("command"), str):
            return deny("Invalid patch input")
        # Writes always require review. Never parse or apply patch content.
        projected = {"schema_version": 1, "tool_name": "Write", "tool_input": {"write": True}}
    else:
        # MCP and unknown tools are never promoted to a host allow. The
        # existing reviewer classifies unsupported names as BLOCK_RECOMMENDED.
        projected = {"schema_version": 1, "tool_name": "CodexUnsupportedTool", "tool_input": {}}
    try:
        recommendation = review_event(projected).get("decision")
    except (ReviewError, ValueError, TypeError, RecursionError, OverflowError):
        return deny("Invalid tool input")
    if recommendation == "ALLOW_CANDIDATE":
        # Empty output decision defers to the host, OS, sandbox and owner.
        return {}
    if recommendation == "REVIEW_REQUIRED":
        return deny("Operation requires review")
    return deny("Operation blocked by GateGuard recommendation")


def main() -> int:
    try:
        if (len(sys.argv) not in (3, 4) or sys.argv[1] != "--project-root"
                or (len(sys.argv) == 4 and sys.argv[3] != "--assume-local-exec-cwd")):
            result = deny("Project root unavailable")
        else:
            raw = sys.stdin.buffer.read(MAX_EVENT_BYTES + 1)
            if not raw or len(raw) > MAX_EVENT_BYTES:
                raise ReviewError("INPUT_SIZE")
            event = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                               parse_constant=_nonstandard_number)
            result = evaluate(event, Path(sys.argv[2]), len(sys.argv) == 4)
    except (ReviewError, ValueError, UnicodeError, TypeError, RecursionError,
            OverflowError, OSError):
        result = deny("Invalid hook event")
    sys.stdout.write(json.dumps(result, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
