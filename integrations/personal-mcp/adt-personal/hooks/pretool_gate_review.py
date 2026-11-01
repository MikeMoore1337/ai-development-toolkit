#!/usr/bin/env python3
"""Offline, fail-closed GateGuard pre-action *review*, not an active Codex hook.

No commands are executed and no client permission or pre-execution hook is granted.
Input is untrusted data; owner and host permissions remain authoritative.
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

# No shell/PowerShell interpreter is implemented. Known, directly visible
# dangerous operations are highlighted; unfamiliar syntax always needs review.
SAFE_BASH = frozenset({
    ("pwd",), ("git", "status"), ("git", "status", "--short"),
    ("git", "diff"), ("git", "diff", "--stat"), ("git", "diff", "--check"),
    ("git", "log", "-1", "--oneline"), ("git", "rev-parse", "HEAD"),
})
SAFE_PS = frozenset({"get-location", "get-childitem", "pwd"})
# Metacharacters, command substitution and chaining can never be allowlisted.
UNSAFE_SHELL_CHARS = re.compile(r"[;&|\x60$<>\r\n\x00]")
UNSAFE_PS_CHARS = re.compile(r"[;&|\x60$<>\r\n\x00()]")
PLAIN_BASH = re.compile(r"[A-Za-z0-9_.\-/ \t]+\Z")
PLAIN_PS = re.compile(r"[A-Za-z-]+\Z")
# A recommendation for a visible command position, not substring matching
# inside quoted prose. Nested/obfuscated interpreters remain REVIEW_REQUIRED.
VISIBLE_DANGEROUS = re.compile(
    r"(?im)(?:^|[;&|\r\n]|\$\(|\x60|\{)\s*(?:"
    r"(?:git\s+(?:reset\s+--hard|clean\s+-[a-z]*f[a-z]*|"
    r"push\s+(?:--force\b|-f\b)|branch\s+-D\b|"
    r"filter-branch\b|worktree\s+remove\b))|"
    r"(?:rm|ri|del|erase|rmdir|unlink)\s+(?:-|/|\S)|"
    r"(?:Remove-Item|Format-Volume|Clear-Disk|Stop-Computer|"
    r"shutdown|diskpart|Invoke-Expression|iex|Start-Process|"
    r"curl|wget|Invoke-WebRequest)\b|"
    r"(?:DROP\s+TABLE|TRUNCATE\s+TABLE|DELETE\s+FROM)\b)"
)


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


def _invalid_text(value: str) -> bool:
    return any(ord(ch) < 32 and ch not in "\t\r\n" or
               ord(ch) == 127 or 0xD800 <= ord(ch) <= 0xDFFF for ch in value)


def _dangerous_bash_tokens(parts: list[str]) -> bool:
    """Spot known operations only when they are the direct command."""
    if not parts:
        return False
    head = parts[0]
    if head in {"rm", "rmdir", "unlink", "shred", "curl", "wget", "shutdown"}:
        return True
    if head == "git":
        # Inspect only the bounded, well-known Git global-option prefix.
        # Anything not recognized is REVIEW_REQUIRED, never an allow signal.
        index = 1
        while index < len(parts):
            option = parts[index]
            if option in {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}:
                index += 2
            elif (option in {"--no-pager", "-P", "--bare"} or
                  option.startswith(("-C", "-c", "--git-dir=", "--work-tree=",
                                     "--namespace="))):
                index += 1
            else:
                break
        if index >= len(parts):
            return False
        subcommand, args = parts[index], parts[index + 1:]
        if subcommand == "reset" and any(
            p == "--hard" or p.startswith("--hard=") for p in args
        ):
            return True
        if subcommand == "clean" and any(
            p == "--force" or (p.startswith("-") and not p.startswith("--")
                               and "f" in p[1:]) for p in args
        ):
            return True
        if subcommand == "push" and any(
            p in {"-f", "--force", "--force-with-lease"} or
            p.startswith("--force-with-lease=") for p in args
        ):
            return True
        if subcommand == "branch" and any(p in {"-D", "--force"} for p in args):
            return True
        if subcommand == "filter-branch" or (
            subcommand == "worktree" and args and args[0] == "remove"
        ):
            return True
    # SQL commands may be supplied as plain text to the Bash synthetic adapter.
    if head.upper() in {"DROP", "TRUNCATE", "DELETE"} and len(parts) > 1:
        return parts[1].upper() in {"TABLE", "FROM"}
    return False


def _shell_review(tool: str, command: str) -> dict[str, object]:
    if not command.strip() or len(command) > MAX_COMMAND_CHARS or _invalid_text(command):
        raise ReviewError("INVALID_COMMAND")
    if tool == "Bash":
        if UNSAFE_SHELL_CHARS.search(command):
            if VISIBLE_DANGEROUS.search(command):
                return _recommendation("BLOCK_RECOMMENDED", "DANGEROUS_OPERATION")
            return _recommendation("REVIEW_REQUIRED", "COMPOUND_OR_EXPANDED_SHELL")
        try:
            parts = shlex.split(command, posix=True)
        except ValueError as exc:
            raise ReviewError("INVALID_SHELL_SYNTAX") from exc
        if _dangerous_bash_tokens(parts):
            return _recommendation("BLOCK_RECOMMENDED", "DANGEROUS_OPERATION")
        if PLAIN_BASH.fullmatch(command) and tuple(parts) in SAFE_BASH:
            return _recommendation("ALLOW_CANDIDATE", "EXACT_READONLY_FORM")
    else:
        # Matching only at visible statement boundaries avoids a common false
        # positive: Write-Output 'Remove-Item' is not a Remove-Item invocation.
        if VISIBLE_DANGEROUS.search(command):
            return _recommendation("BLOCK_RECOMMENDED", "DANGEROUS_OPERATION")
        stripped = command.strip(" \t")
        if (not UNSAFE_PS_CHARS.search(command) and PLAIN_PS.fullmatch(stripped)
                and stripped.casefold() in SAFE_PS):
            return _recommendation("ALLOW_CANDIDATE", "EXACT_READONLY_FORM")
        if UNSAFE_PS_CHARS.search(command):
            return _recommendation("REVIEW_REQUIRED", "COMPOUND_OR_EXPANDED_SHELL")
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
        # Model-controlled approval flags are data, not authorization.
        if not payload or any(not isinstance(k, str) for k in payload):
            raise ReviewError("INVALID_WRITE_INPUT")
        return _recommendation("REVIEW_REQUIRED", "WRITE_NEEDS_OWNER_AND_HOST_GATE")
    expected = {"path"} if tool == "Read" else {"pattern"}
    if set(payload) != expected:
        raise ReviewError("INVALID_READ_INPUT")
    value = next(iter(payload.values()))
    if (not isinstance(value, str) or not value.strip() or
            len(value) > MAX_TOOL_PATH_CHARS or _invalid_text(value) or
            any(ch in value for ch in "\r\n\x00")):
        raise ReviewError("INVALID_READ_INPUT")
    return _recommendation("ALLOW_CANDIDATE", "READ_ONLY_DECLARATION")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReviewError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def _nonstandard_number(_value: str) -> None:
    raise ReviewError("NONSTANDARD_JSON_NUMBER")


def main() -> int:
    try:
        data = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if not data or len(data) > MAX_INPUT_BYTES:
            raise ReviewError("INPUT_SIZE")
        event = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_nonstandard_number)
        if not isinstance(event, dict):
            raise ReviewError("INVALID_SCHEMA")
        result = review_event(event)
        exit_code = 0
    except (ReviewError, ValueError, UnicodeError, TypeError, RecursionError, OverflowError):
        # No sensitive input or full exception text is returned.
        result = _recommendation("BLOCK_RECOMMENDED", "INVALID_OR_UNTRUSTED_INPUT")
        exit_code = 1
    sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
