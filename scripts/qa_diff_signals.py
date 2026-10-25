#!/usr/bin/env python3
"""Bounded, read-only token indicators from a locally verified exact-SHA git patch.

Never returns changed source lines, secrets, call graphs, test execution or
claims of complete dependency analysis. No subprocess shell, network or writes.
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess

MAX_PATCH_BYTES = 256 * 1024
MAX_HITS_PER_SURFACE = 50

# Intentionally narrow regex hints: these are NOT language parsers.
MARKERS = {
    "AUTH": re.compile(r"\b(?:login_required|authorize|permission|permissions|tenant_id|"
                       r"jwt|require_role|is_admin|access_token|scopes)\b", re.I),
    "API": re.compile(r"(?:@(?:app|router)\.(?:get|post|put|patch|delete)\s*\(|"
                      r"\b(?:response_model|openapi|graphql|request_schema|response_schema|"
                      r"status_code)\b)", re.I),
    "DB": re.compile(r"\b(?:ALTER\s+TABLE|DROP\s+(?:TABLE|COLUMN)|CREATE\s+INDEX|"
                     r"FOREIGN\s+KEY|NOT\s+NULL|SELECT\s+FOR\s+UPDATE|"
                     r"transaction\.atomic|BEGIN\s+TRANSACTION)\b", re.I),
    "UI": re.compile(r"\b(?:useEffect|setState|onClick|onSubmit|localStorage|"
                     r"sessionStorage|addEventListener)\b|aria-[a-z-]+", re.I),
    "ASYNC": re.compile(r"\b(?:idempotency|retry|retries|consumer|producer|"
                        r"enqueue|dead_letter|nack|ack_message)\b", re.I),
    # A mutation token is an advisory risk hint, not proof of a migration or callers.
    "PERSISTED_STATE": re.compile(
        r"\b(?:mutation_id|expected_version|applied_version|request_fingerprint|"
        r"replayed_mutation|is_completed|version_conflict|state_transition|"
        r"with_for_update)\b|\bversion\s*(?:\+=|=)", re.I),
    "PRIVACY": re.compile(r"\b(?:api_key|private_key|secret|password|pii|"
                          r"credential|sensitive_data|encrypt|decrypt)\b", re.I),
    "CI": re.compile(r"\b(?:cap_drop|no_new_privileges|deploy|workflow_call|"
                     r"permissions:|secrets\.)\b", re.I),
}


class DiffEvidenceError(ValueError):
    """Insufficient or unsafe local git evidence."""


def _paths(paths: list[str]) -> set[str]:
    # Reuse the project-approved safe path validation without importing
    # the CLI module (avoids cyclic imports).
    from qa_change_impact import validate_paths
    try:
        return set(validate_paths(paths))
    except ValueError as exc:
        raise DiffEvidenceError("Invalid changed-path inventory") from exc


def inspect_patch(patch: bytes, changed_paths: list[str]) -> dict:
    """Read an in-memory patch; never expose its original text."""
    expected = _paths(changed_paths)
    if len(patch) > MAX_PATCH_BYTES:
        raise DiffEvidenceError("Patch exceeds bounded 256KiB inspection limit")
    try:
        source = patch.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise DiffEvidenceError("Non-UTF8 patch requires manual review") from exc
    data = {path: {"added_lines": 0, "removed_lines": 0, "hunks": 0,
                    "binary_or_unparsed": False, "signals": {}}
            for path in sorted(expected)}
    old_path = None
    active = None
    in_hunk = False
    seen_files = set()
    for line in source.splitlines():
        if line.startswith("diff --git "):
            old_path = None
            active = None
            in_hunk = False
            continue
        if line.startswith("--- "):
            old_path = line[6:] if line.startswith("--- a/") else None
            in_hunk = False
            continue
        if line.startswith("+++ "):
            new_path = line[6:] if line.startswith("+++ b/") else None
            active = new_path or old_path
            if active is None or active not in expected:
                raise DiffEvidenceError("Patch path not in verified changed-path inventory")
            seen_files.add(active)
            continue
        if line.startswith("Binary files ") or line.startswith("GIT binary patch"):
            # No shell or textconv is used for this; never infer content.
            if active is not None:
                data[active]["binary_or_unparsed"] = True
            continue
        if line.startswith("@@ "):
            if active is None:
                raise DiffEvidenceError("Patch hunk without verified file")
            in_hunk = True
            data[active]["hunks"] += 1
            continue
        if not in_hunk or active is None or not line.startswith(("+", "-")):
            continue
        kind = "added_lines" if line.startswith("+") else "removed_lines"
        data[active][kind] += 1
        # The original line is immediately discarded; only static token classes
        # are retained, not matches, excerpts or credential contents.
        for surface, pattern in MARKERS.items():
            if pattern.search(line[1:]):
                hints = data[active]["signals"]
                hints[surface] = min(MAX_HITS_PER_SURFACE, hints.get(surface, 0) + 1)
    for path, item in data.items():
        if path not in seen_files or (item["hunks"] == 0 and not item["binary_or_unparsed"]):
            item["binary_or_unparsed"] = True
    inspected = sum(not item["binary_or_unparsed"] for item in data.values())
    return {
        "classification": "LOCAL_PATCH_TOKEN_HINTS_ONLY",
        "evidence": "EXACT_SHA_LOCAL_GIT_PATCH",
        "raw_source_lines_returned": False,
        "file_count": len(data),
        "text_files_with_hunks": inspected,
        "requires_manual_review": sorted(path for path, item in data.items()
                                         if item["binary_or_unparsed"]),
        "files": data,
        "limitations": [
            "Static token hints are not semantic change detection or proof of consumers",
            "No external call graph, affected-test discovery, execution or authorization",
            "Binary, textconv, oversized and non-UTF8 changes require separate review",
        ],
    }


def inspect_git(root: Path, base: str, head: str,
                changed_paths: list[str]) -> dict:
    """Only two full git revisions; no user-controlled Git options or shell."""
    from qa_change_impact import SHA_RE
    if not SHA_RE.fullmatch(base) or not SHA_RE.fullmatch(head):
        raise DiffEvidenceError("Exact full commit SHA pair required")
    if not (root / ".git").exists():
        raise DiffEvidenceError("Local Git metadata missing")
    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "diff", "--no-ext-diff", "--no-textconv",
             "--no-color", "--no-renames", "--unified=0", "--patch",
             base, head, "--"],
            capture_output=True, timeout=20, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DiffEvidenceError("Local git patch unavailable") from exc
    if proc.returncode != 0:
        raise DiffEvidenceError("Local git patch could not be verified")
    return inspect_patch(proc.stdout, changed_paths)
