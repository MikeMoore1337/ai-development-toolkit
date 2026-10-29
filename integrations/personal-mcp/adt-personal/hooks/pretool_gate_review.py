#!/usr/bin/env python3
"""Offline, fail-closed GateGuard pre-action *review*, not an active Codex hook.

This code DOES NOT execute a tool, approve a filesystem mutation, or establish
that an installed desktop client emits/enforces PreToolUse. Tool input is
untrusted data. Host permissions and owner authorization remain authoritative.
"""
from __future__ import annotations

import json
import re
import shlex
import sys

MAX_INPUT_BYTES = 16384
MAX_COMMAND_CHARS = 4096
MAX_TOOL_PATH_CHARS = 1024
SCHEMA_VERSION = 1

READ_TOOLS = frozenset({"Read", "Grep", "Glob"})
WRITE_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})
SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
SUPPORTED_TOOLS = READ_TOOLS | WRITE_TOOLS | SHELL_TOOLS

# Source-only classification: these syntactic patterns are NOT a sandbox and
# absence of a match never proves a command harmless.
DANGEROUS = re.compile(
    r"(?i)(?:\bgit\s+(?:reset\s+--hard|clean\s+-(?=[a-zA-Z]*f)[a-zA-Z]+|push\s+--force|"
    r"branch\s+-D|filter-branch)\b|"
    r"\b(?:rm\s+-[^\s]*r|rm\s+-[^\s]*f|rmdir\s+/s|del\s+/[sq]|"
    r"Remove-Item\b|Format-Volume\b|Clear-Disk\b|"
    r"Stop-Computer\b|shutdown\b|diskpart\b|"
    r"Invoke-Expression\b|iex\b|Start-Process\b|"
    r"curl\b|wget\b|Invoke-WebRequest\b)\b|"
    r"\b(?:DROP\s+TABLE|TRUNCATE\s+TABLE|DELETE\s+FROM)\b)"
)
# Permit only exact small, non-parameterized read-only command forms.
SAFE_BASH = frozenset({
    ("pwd",), ("git", "status"), ("git", "status", "--short"),
    ("git", "diff"), ("git", "diff", "--stat"), ("git", "diff", "--check"),
    ("git", "log", "-1", "--oneline"), ("git", "rev-parse", "HEAD"),
})
SAFE_PS = frozenset({"Get-Location", "Get-ChildItem", "pwd"})
UNSAFE_SHELL_CHARS = re.compile(r"[;&|\x60$<>\r\n\x00]")
UNSAFE_PS_CHARS = re.compile(r"[;&|\x60$<>\r\n\x00()]")

class ReviewError(ValueError):
    pass

def _recommendation(decision: str, reason: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "decision": decision,
        "reason_code": reason,
        "host_enforcement": "NOT_VERIFIED",
        "blocking_effect": "NONE_SOURCE_ONLY",
        "owner_authorization": "NOT_ATTESTED",
        "model_calls": 0,
        "network_calls": 0,
        "tool_executed": False,
        "state_written": False,
        "hook_registered": False,
    }

def _shell_review(tool: str, command: str) -> dict[str, object]:
    if not command.strip() or len(command) > MAX_COMMAND_CHARS:
        raise ReviewError("INVALID_COMMAND")
    if DANGEROUS.search(command):
        return _recommendation("BLOCK_RECOMMENDED", "DANGEROUS_OPERATION")
    if tool == "Bash":
        if UNSAFE_SHELL_CHARS.search(command):
            return _recommendation("REVIEW_REQUIRED", "COMPOUND_OR_EXPANDED_SHELL")
        try:
            parts = shlex.split(command, posix=True)
        except ValueError as exc:
            raise ReviewError("INVALID_SHELL_SYNTAX") from exc
        if tuple(parts) in SAFE_BASH:
            return _recommendation("ALLOW_CANDIDATE", "EXACT_READONLY_FORM")
    else:
        if not UNSAFE_PS_CHARS.search(command) and command.strip() in SAFE_PS:
            return _recommendation("ALLOW_CANDIDATE", "EXACT_READONLY_FORM")
    return _recommendation("REVIEW_REQUIRED", "UNRECOGNIZED_COMMAND")

def review_event(event: object) -> dict[str, object]:
    """Deterministic review of an explicitly supplied synthetic tool event."""
    if not isinstance(event, dict) or set(event) != {
        "schema_version", "tool_name", "tool_input"
    }:
        raise ReviewError("INVALID_SCHEMA")
    if type(event["schema_version"]) is not int or event["schema_version"] != SCHEMA_VERSION:
        raise ReviewError("INVALID_VERSION")
    tool = event["tool_name"]
    payload = event["tool_input"]
    if not isinstance(tool, str) or tool not in SUPPORTED_TOOLS:
        return _recommendation("BLOCK_RECOMMENDED", "UNKNOWN_TOOL")
    if not isinstance(payload, dict):
        raise ReviewError("INVALID_TOOL_INPUT")
    if tool in SHELL_TOOLS:
        if set(payload) != {"command"} or not isinstance(payload.get("command"), str):
            raise ReviewError("INVALID_SHELL_INPUT")
        return _shell_review(tool, payload["command"])
    if tool in WRITE_TOOLS:
        # Never trust a model-controlled approval flag or attempt to infer
        # authorization from intent. This is a warning, not a host denial.
        if not payload or any(not isinstance(k, str) for k in payload):
            raise ReviewError("INVALID_WRITE_INPUT")
        return _recommendation("REVIEW_REQUIRED", "WRITE_NEEDS_OWNER_AND_HOST_GATE")
    if set(payload) not in ({"path"}, {"pattern"}):
        raise ReviewError("INVALID_READ_INPUT")
    value = next(iter(payload.values()))
    if not isinstance(value, str) or not value or len(value) > MAX_TOOL_PATH_CHARS:
        raise ReviewError("INVALID_READ_INPUT")
    return _recommendation("ALLOW_CANDIDATE", "READ_ONLY_DECLARATION")

def main() -> int:
    try:
        data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if not data or len(data) > MAX_INPUT_BYTES:
            raise ReviewError("INPUT_SIZE")
        event = json.loads(data.decode("utf-8"))
        if not isinstance(event, dict):
            raise ReviewError("INVALID_SCHEMA")
        result = review_event(event)
        exit_code = 0
    except (ReviewError, ValueError, UnicodeError, TypeError):
        # No sensitive input or full exception text is returned.
        result = _recommendation("BLOCK_RECOMMENDED", "INVALID_OR_UNTRUSTED_INPUT")
        exit_code = 1
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
