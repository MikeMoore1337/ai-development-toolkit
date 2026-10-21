#!/usr/bin/env python3
"""Zero-provider-call smoke for the *measurement harness*, NOT an AI benchmark.

For each synthetic fixture, test the buggy baseline and a deterministic
human-authored reference correction against the same hidden acceptance oracle.
Only Python, Node and Go standard-library processes and local Git are used.
No model, API, network client, subscription or provider authentication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

from agent_eval_fixtures import FIXTURES, init_git, materialize, oracle_command, snapshot_digest
from agent_eval_runner import prepare_oracle_destination

# Deliberately independent of real CLI agent dispatch and human review.
REFERENCE_FIXES = {
    "python-api": {
        "retry.py": """def parse_retry_after(value: str | None) -> int | None:
    if value is None:
        return None
    stripped = value.strip(" \\t\\n\\r\\v\\f")
    if not stripped or any(c < "0" or c > "9" for c in stripped):
        return None
    return int(stripped)
""",
    },
    "javascript-ui": {
        "port.mjs": """export function parsePort(value) {
  if (typeof value !== 'string') return null;
  const normalized = value.trim();
  if (!/^[0-9]+$/.test(normalized)) return null;
  const n = Number(normalized);
  return Number.isSafeInteger(n) && n >= 1 && n <= 65535 ? n : null;
}
""",
    },
    "go-cli": {
        "timeout.go": """package timeout

import (
    "errors"
    "strconv"
    "strings"
)

func ParseTimeout(raw string) (int, error) {
    normalized := strings.TrimSpace(raw)
    if normalized == "" {
        return 0, errors.New("invalid timeout")
    }
    for _, character := range normalized {
        if character < '0' || character > '9' {
            return 0, errors.New("invalid timeout")
        }
    }
    result, err := strconv.Atoi(normalized)
    if err != nil || result < 1 || result > 60000 {
        return 0, errors.New("timeout out of range")
    }
    return result, nil
}
""",
    },
}
EXPECTED_CASES = frozenset({"python-api", "javascript-ui", "go-cli"})
ALLOWED_EXECUTABLES = {"node", "go", Path(sys.executable).name.lower()}
DEFAULT_ORACLE_TIMEOUT = 45
# An isolated Go cache requires an initial standard-library build on clean Windows.
# Retain hard failure on timeout; only allow enough time for a genuine test verdict.
GO_COLD_BUILD_TIMEOUT = 110


def allowed_runtime(case_id: str) -> bool:
    language = FIXTURES[case_id]["language"]
    if language == "python":
        return Path(sys.executable).is_file()
    return shutil.which({"javascript": "node", "go": "go"}[language]) is not None


def _classify_oracle_output(stdout: bytes, stderr: bytes) -> str:
    """Return a fixed diagnostic category; never expose oracle output or secrets."""
    signal = (stdout[:16384] + b"\n" + stderr[:16384]).lower()
    if b"--- fail:" in signal or b"fail\t" in signal or b"test failed" in signal:
        return "TEST_ASSERTION_FAILURE"
    if any(part in signal for part in (b"[build failed]", b"syntax error:", b"undefined:")):
        return "COMPILATION_FAILURE"
    if any(part in signal for part in (b"access is denied", b"permission denied",
                                       b"failed to create cache", b"cannot find goroot")):
        return "ENVIRONMENT_FAILURE"
    return "OTHER_OUTPUT" if signal.strip() else "NO_OUTPUT"


def _safe_verdict(verdict: dict) -> dict:
    """Never serialize stdout, stderr, paths, or environment values."""
    return {name: verdict.get(name) for name in
            ("returncode", "timed_out", "duration_ms", "outcome_class")}


def _go_version_label(workspace: Path) -> str:
    """Read only the local Go version token; no network, user hooks or raw output."""
    env = {key: val for key in ("PATH", "SYSTEMROOT", "WINDIR", "PATHEXT")
           if (val := os.environ.get(key)) is not None}
    env.update({"HOME": str(workspace), "USERPROFILE": str(workspace),
                "GOTOOLCHAIN": "local", "GOPROXY": "off", "GOSUMDB": "off"})
    try:
        version = subprocess.run(
            ["go", "version"], cwd=workspace, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False, timeout=5)
    except (OSError, subprocess.SubprocessError):
        return "UNAVAILABLE"
    match = re.search(rb"\bgo[0-9]+\.[0-9]+(?:\.[0-9]+)?\b", version.stdout[:512])
    return match.group(0).decode("ascii") if match and version.returncode == 0 else "UNKNOWN"


def oracle_exit(case_id: str, workspace: Path, *, timeout: int = 45) -> dict:
    """Use a fixed, allowlisted local stdlib oracle, never an agent command."""
    if timeout < 1 or timeout > 120:
        raise ValueError("Invalid offline oracle timeout")
    argv = oracle_command(case_id)
    if Path(argv[0]).name.lower() not in ALLOWED_EXECUTABLES:
        raise ValueError("Refusing unexpected oracle executable")
    # Synthetic source must not inherit provider credentials, CLI hooks or
    # Python/Node/Go injection options from the invoking user's environment.
    runtime_tmp = workspace.parent / ".oracle-runtime-tmp"
    runtime_tmp.mkdir(mode=0o700, exist_ok=True)
    env = {key: value for key in ("PATH", "SYSTEMROOT", "WINDIR", "PATHEXT")
           if (value := os.environ.get(key)) is not None}
    env.update({
        "HOME": str(workspace), "USERPROFILE": str(workspace),
        "TMP": str(runtime_tmp), "TEMP": str(runtime_tmp), "TMPDIR": str(runtime_tmp),
        "PYTHONPATH": str(workspace), "PYTHONNOUSERSITE": "1",
        "PYTHONSAFEPATH": "1", "GOPROXY": "off", "GOSUMDB": "off",
        "GOTOOLCHAIN": "local", "GOWORK": "off",
        "GOCACHE": str(workspace.parent / ".go-build-cache"),
        "GOPATH": str(workspace.parent / ".go-path"),
    })
    # Fixed command; no shell, no provider client, no downloading packages.
    started = time.monotonic()
    try:
        result = subprocess.run(argv, cwd=workspace, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                check=False, timeout=timeout)
        return {"returncode": result.returncode, "timed_out": False,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "outcome_class": _classify_oracle_output(result.stdout, result.stderr)}
    except subprocess.TimeoutExpired:
        return {"returncode": None, "timed_out": True,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "outcome_class": "TIMEOUT"}


def perform_smoke(cases: list[str], *, strict_runtimes: bool = False,
                  timeout: int | None = None) -> dict:
    if not cases or len(set(cases)) != len(cases) or any(c not in EXPECTED_CASES for c in cases):
        raise ValueError("Only unique, known synthetic fixture case IDs are allowed")
    if set(REFERENCE_FIXES) != EXPECTED_CASES:
        raise ValueError("Reference fixture registry is incomplete")
    results: list[dict] = []
    # Automatically removed. No GitHub, external network, provider logs or
    # user working tree is touched (only isolated synthetic temporary files).
    with tempfile.TemporaryDirectory(prefix="adt-offline-oracle-") as parent:
        root = Path(parent)
        for case_id in cases:
            if not allowed_runtime(case_id):
                if strict_runtimes:
                    raise ValueError(f"Required offline runtime unavailable: {case_id}")
                results.append({"case_id": case_id, "state": "SKIPPED_RUNTIME_MISSING"})
                continue
            case = FIXTURES[case_id]
            hashes: dict[str, str] = {}
            verdicts: dict[str, dict] = {}
            for variant in ("baseline", "reference"):
                workspace = root / f"{case_id}-{variant}"
                materialize(case_id, workspace)
                if (workspace / case["oracle_path"]).exists():
                    raise ValueError(f"Hidden oracle leaked into {variant} workspace")
                fixture_sha = init_git(workspace)
                hashes[variant] = fixture_sha
                if variant == "reference":
                    repairs = REFERENCE_FIXES[case_id]
                    if not repairs or not set(repairs).issubset(case["files"]):
                        raise ValueError("Reference edit not restricted to original source")
                    for name, content in repairs.items():
                        target = workspace / name
                        if target.is_symlink() or not target.is_file():
                            raise ValueError("Unexpected linked/missing reference file")
                        target.write_text(content, encoding="utf-8", newline="\n")
                hidden = prepare_oracle_destination(workspace, case_id)
                hidden.write_text(case["oracle"], encoding="utf-8", newline="\n")
                effective_timeout = (timeout if timeout is not None else
                                     (GO_COLD_BUILD_TIMEOUT if case["language"] == "go"
                                      else DEFAULT_ORACLE_TIMEOUT))
                verdicts[variant] = oracle_exit(case_id, workspace, timeout=effective_timeout)
            if hashes["baseline"] != hashes["reference"]:
                raise ValueError("Paired fixture Git SHA differs before reference correction")
            baseline, reference = verdicts["baseline"], verdicts["reference"]
            # Go cold-build latency is measurable without exposing logs or passing
            # over a timeout. A successful test still needs a real process exit.
            if case["language"] == "go":
                print("OFFLINE_GO_ORACLE_DIAGNOSTIC " + json.dumps({
                    "go_version": _go_version_label(root),
                    "timeout_seconds": effective_timeout,
                    "baseline": _safe_verdict(baseline),
                    "reference": _safe_verdict(reference),
                }, sort_keys=True), file=sys.stderr)
            if (baseline["timed_out"] or baseline["returncode"] in (None, 0) or
                    reference["timed_out"] or reference["returncode"] != 0):
                details = {"baseline": _safe_verdict(baseline),
                           "reference": _safe_verdict(reference)}
                raise ValueError(f"Offline hidden oracle not discriminative: {case_id}: "
                                 + json.dumps(details, sort_keys=True))
            results.append({
                "case_id": case_id, "state": "OFFLINE_ORACLE_DISCRIMINATES",
                "language": case["language"],
                "initial_git_sha": hashes["baseline"],
                "initial_snapshot_sha256": snapshot_digest(case_id),
                "baseline_oracle_failed": True, "reference_oracle_passed": True,
                "provider_calls": 0,
            })
    return {
        "schema_version": 1,
        "classification": "SYNTHETIC_OFFLINE_HARNESS_SMOKE_NOT_MODEL_EVAL",
        "real_agent_trials": 0,
        "real_agent_outcomes": "NOT_MEASURED",
        "independent_review": "NOT_PERFORMED",
        "owner_zero_spend_lock_preserved": True,
        "all_requested_cases_exercised": all(
            x["state"] == "OFFLINE_ORACLE_DISCRIMINATES" for x in results),
        "cases": results,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases", nargs="+", choices=sorted(EXPECTED_CASES),
                   default=sorted(EXPECTED_CASES))
    p.add_argument("--strict-runtimes", action="store_true",
                   help="Require Python, Node and Go (for example on Ubuntu CI)")
    args = p.parse_args()
    try:
        report = perform_smoke(args.cases, strict_runtimes=args.strict_runtimes)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"FAIL: offline smoke: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["all_requested_cases_exercised"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
