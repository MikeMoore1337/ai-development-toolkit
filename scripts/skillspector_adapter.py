#!/usr/bin/env python3
"""Opt-in external SkillSpector static adapter for a pre-validated local Skill.

No provider, model, remote code from the candidate, or installation is invoked.
The pinned scanner may be downloaded by uvx and may look up dependency
coordinates in OSV.dev; this is not an offline or zero-network guarantee.
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Callable, Mapping

SKILLSPECTOR_COMMIT = "d162d9b343e559be13df8ebba093df3bc9d58c90"
SKILLSPECTOR_SOURCE = f"git+https://github.com/NVIDIA/SkillSpector.git@{SKILLSPECTOR_COMMIT}"
MAX_OUTPUT = 1024 * 1024
TIMEOUT_SECONDS = 180

# Explicit allowlist: caller credentials, proxy URLs, package index credentials,
# injected LLM providers and arbitrary subprocess config must not reach uvx.
ALLOWED_ENV = frozenset({
    "PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "WINDIR", "COMSPEC",
    "TEMP", "TMP", "TMPDIR", "APPDATA", "LOCALAPPDATA", "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME", "XDG_DATA_HOME", "LANG", "LC_ALL",
    "PYTHONIOENCODING", "CI", "NO_COLOR", "UV_CACHE_DIR", "UV_PYTHON",
    "SSL_CERT_FILE", "SSL_CERT_DIR",
})


def _blocked(reason: str) -> dict:
    return {
        "status": "BLOCKED",
        "reason": reason,
        "scanner": "NVIDIA SkillSpector",
        "source_commit": SKILLSPECTOR_COMMIT,
        "llm": "DISABLED",
        "installation": "NOT_AUTHORIZED",
    }


def _integer(value: object) -> int | None:
    return value if type(value) is int and value >= 0 else None


def verdict(report: object, exit_code: int) -> dict:
    """Fail closed for incomplete, anomalous or malformed scanner reports."""
    if not isinstance(report, dict):
        return _blocked("INVALID_REPORT")
    metadata = report.get("metadata")
    complete = report.get("analysis_completeness")
    risk = report.get("risk_assessment")
    if not isinstance(metadata, dict) or not isinstance(complete, dict) or not isinstance(risk, dict):
        return _blocked("INCOMPLETE_REPORT_SCHEMA")
    if (metadata.get("llm_requested") is not False
            or _integer(metadata.get("llm_calls_attempted")) != 0):
        return _blocked("LLM_NOT_PROVEN_DISABLED")
    if (report.get("execution_successful") is not True
            or complete.get("execution_successful") is not True
            or complete.get("is_complete") is not True
            or complete.get("status") != "complete"
            or complete.get("limitations")
            or _integer(complete.get("entirely_uninspected_files")) != 0
            or _integer(complete.get("partially_inspected_files")) != 0):
        return _blocked("INCOMPLETE_ANALYSIS")
    recommendation = risk.get("recommendation")
    severity = risk.get("severity")
    score = risk.get("score")
    if (recommendation not in ("SAFE", "CAUTION", "DO_NOT_INSTALL")
            or severity not in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
            or isinstance(score, bool) or not isinstance(score, (int, float))
            or not 0 <= score <= 100):
        return _blocked("INVALID_RISK_ASSESSMENT")
    status = ("BLOCKED" if recommendation == "DO_NOT_INSTALL" or severity in ("HIGH", "CRITICAL")
              else "REVIEW_REQUIRED" if recommendation == "CAUTION" or severity == "MEDIUM"
              else "PASS")
    if exit_code != 0 and status != "BLOCKED":
        return _blocked("NONZERO_SCANNER_EXIT")
    return {
        "status": status, "reason": "RISK_ASSESSMENT",
        "scanner": "NVIDIA SkillSpector", "source_commit": SKILLSPECTOR_COMMIT,
        "recommendation": recommendation, "severity": severity, "score": score,
        "llm": "DISABLED", "installation": "NOT_AUTHORIZED",
    }


def scan(candidate: Path, *,
         runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
         executable: str = "uvx",
         environ: Mapping[str, str] | None = None) -> dict:
    """Run only on already vetted local candidate paths, with explicit opt-in.

    The caller must first validate file inventory, SHA-256, symlinks and source
    allowlist using external_skill_gate; this function does not confer trust.
    """
    if (not isinstance(candidate, Path) or not candidate.is_dir()
            or candidate.is_symlink() or not (candidate / "SKILL.md").is_file()):
        return _blocked("INVALID_CANDIDATE")
    command = [
        executable, "--from", SKILLSPECTOR_SOURCE, "skillspector", "scan",
        str(candidate.resolve()), "--no-llm", "--format", "json",
        "--fail-on-incomplete",
    ]
    raw_env = os.environ if environ is None else environ
    safe_env = {k: v for k, v in raw_env.items() if k.upper() in ALLOWED_ENV}
    # No --output: stdout JSON works on Windows, whose newer versions
    # explicitly reject POSIX-only secure file-output operations.
    try:
        process = runner(command, capture_output=True, text=True,
                         encoding="utf-8", errors="replace",
                         timeout=TIMEOUT_SECONDS, env=safe_env, check=False)
    except (OSError, subprocess.TimeoutExpired, ValueError):
        return _blocked("SCANNER_UNAVAILABLE_OR_TIMEOUT")
    if process.returncode not in (0, 1):
        return _blocked("SCANNER_EXECUTION_ERROR")
    data = process.stdout
    if not isinstance(data, str) or len(data.encode("utf-8")) > MAX_OUTPUT:
        return _blocked("INVALID_REPORT_SIZE")
    try:
        report = json.loads(data)
    except (ValueError, TypeError):
        return _blocked("INVALID_REPORT_JSON")
    return verdict(report, process.returncode)
