#!/usr/bin/env python3
"""Native, explicitly invoked, read-only MCP adapter for #436.

Reuses the existing strict v2 preview and typed public GitHub fact verifier.
No files, clients, sessions, models, hooks or skills are written or started.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from skill_observation_review import MAX_BYTES, preview_learning
from skill_learning_verification import check_skill_lock, public_github_get, verify_learning


class LearningMcpError(ValueError):
    """Fixed public error code. Never expose raw inputs or paths."""


def _size_guard(value: object) -> None:
    try:
        raw = json.dumps(value, ensure_ascii=False, allow_nan=False,
                         separators=(",", ":")).encode("utf-8")
    except (ValueError, TypeError, RecursionError, OverflowError) as exc:
        raise LearningMcpError("INVALID_OR_UNSAFE_INPUT") from exc
    if len(raw) > MAX_BYTES:
        raise LearningMcpError("INPUT_TOO_LARGE")


def review(*, packet: object, project_repo: object, as_of: object,
           claims: object = None, allow_public_github_get: object = False,
           skill_id: object = None, skill_file: object = None,
           expected_skill_sha256: object = None,
           source_root: Path, fetch: Callable[[str], dict] | None = None) -> dict:
    """Review supplied sanitized observations; optional explicitly allowed GET.

    The injected fetch argument exists for offline unit tests only; MCP never
    accepts it from the caller. In-process execution is distinct from the
    native Codex skill lifecycle and from any claimed model improvement.
    """
    if type(allow_public_github_get) is not bool:
        raise LearningMcpError("INVALID_NETWORK_CONSENT")
    if not isinstance(project_repo, str) or not isinstance(as_of, str):
        raise LearningMcpError("INVALID_PROJECT_OR_DATE")
    if (claims is None and allow_public_github_get) or (
            claims is not None and not allow_public_github_get):
        raise LearningMcpError("EXPLICIT_PUBLIC_GITHUB_OPT_IN_REQUIRED")
    lock_parts = (skill_id, skill_file, expected_skill_sha256)
    if any(x is not None for x in lock_parts) and not all(
            isinstance(x, str) for x in lock_parts):
        raise LearningMcpError("INCOMPLETE_SKILL_LOCK")
    _size_guard(packet)
    if claims is not None:
        _size_guard(claims)
    try:
        if claims is None:
            if any(x is not None for x in lock_parts):
                raise LearningMcpError("SKILL_LOCK_REQUIRES_VERIFICATION")
            result = preview_learning(packet, project_repo=project_repo, as_of=as_of)
            mode = "OFFLINE_PREVIEW"
        else:
            lock = None
            if all(isinstance(x, str) for x in lock_parts):
                lock = check_skill_lock(source_root, skill_id, skill_file,
                                        expected_skill_sha256)
            # Fetching a public fact never proves the practice is beneficial.
            result = verify_learning(
                packet, claims, project_repo=project_repo, as_of=as_of,
                skill_lock=lock,
                fetch=public_github_get if fetch is None else fetch,
            )
            mode = "EXPLICIT_PUBLIC_GITHUB_GET"
    except LearningMcpError:
        raise
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            RecursionError, OverflowError) as exc:
        raise LearningMcpError("INVALID_OR_UNSAFE_INPUT") from exc
    return {
        **result,
        "mcp_review_mode": mode,
        "mcp_review_executed": True,
        "client_native_skill_activation": "NOT_ATTESTED_BY_MCP",
        "model_quality_improvement": "NOT_MEASURED",
        "owner_approval": "NOT_GRANTED",
        "practice_auto_promotion": False,
        "approved_practices_written": 0,
        "additional_cost": 0,
    }
