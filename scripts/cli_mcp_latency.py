#!/usr/bin/env python3
"""Offline CI/local wall-clock samples for Toolkit CLI and MCP handlers.

No AI client, model, network calls, paid API or user project is exercised.
Process-start timings and in-process handler timings are reported separately.
No latency threshold is used as a release gate.
"""
from __future__ import annotations

import argparse
import json
import math
import platform
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
MCP = ROOT / "integrations" / "personal-mcp" / "adt-personal" / "mcp"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(MCP))

import adt_mcp  # noqa: E402
import toolkit_mcp  # noqa: E402


def summarize(milliseconds: list[float]) -> dict:
    """Nearest-rank p95; never pretend a small sample is an SLA."""
    if len(milliseconds) < 10 or not all(math.isfinite(x) and x >= 0 for x in milliseconds):
        raise ValueError("Require at least ten finite nonnegative samples")
    ordered = sorted(milliseconds)
    return {
        "n": len(ordered),
        "median_ms": round(statistics.median(ordered), 3),
        "p95_ms": round(ordered[math.ceil(0.95 * len(ordered)) - 1], 3),
        "min_ms": round(ordered[0], 3),
        "max_ms": round(ordered[-1], 3),
    }


def take_samples(operation: Callable[[], dict], count: int) -> dict:
    """One untimed warmup followed by real elapsed wall-clock observations."""
    result = operation()
    if not isinstance(result, dict):
        raise ValueError("Operation returned no structured result")
    timings = []
    for _ in range(count):
        started = time.perf_counter_ns()
        result = operation()
        timings.append((time.perf_counter_ns() - started) / 1_000_000)
        if not isinstance(result, dict):
            raise ValueError("Operation returned no structured result")
    return summarize(timings)


def read_cli(*args: str, root: Path) -> dict:
    response = subprocess.run(
        [sys.executable, str(root / "scripts" / "adt.py"), "--json", *args],
        cwd=root, check=False, capture_output=True, text=True, encoding="utf-8",
        timeout=30,
    )
    if response.returncode:
        raise ValueError("Read-only CLI failed with status " + str(response.returncode))
    data = json.loads(response.stdout)
    if not isinstance(data, dict):
        raise ValueError("Read-only CLI did not return a JSON object")
    return data


def measure(root: Path = ROOT, samples: int = 12) -> dict:
    """Measure actual offline operations only, never extrapolate model tokens/cost."""
    if not isinstance(samples, int) or isinstance(samples, bool) or not 10 <= samples <= 100:
        raise ValueError("samples must be between 10 and 100")
    root = root.resolve()
    if not (root / "MANIFEST.json").is_file():
        raise ValueError("Expected existing Toolkit source root")
    personal = adt_mcp.Toolkit(root)
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=False, capture_output=True, text=True, encoding="utf-8", timeout=15,
    )
    if head.returncode or len(head.stdout.strip()) != 40:
        raise ValueError("Unable to pin exact source revision")
    with tempfile.TemporaryDirectory(prefix="adt-latency-synthetic-") as disposable:
        # Only the disposable temporary directory is created. CLI status is read-only.
        operations = {
            "cli_profile_list_process": lambda: read_cli("profile", "list", root=root),
            "cli_skill_manager_status_process": lambda: read_cli(
                "status", "--target", disposable, root=root
            ),
            "project_mcp_catalog_inprocess": lambda: toolkit_mcp.invoke("toolkit_catalog", {}),
            "project_mcp_skill_read_inprocess": lambda: toolkit_mcp.invoke(
                "toolkit_read_skill", {"skill": "qa-strategy"}
            ),
            "personal_mcp_info_inprocess": personal.info,
            "personal_mcp_prepare_task_inprocess": lambda: personal.prepare_task(
                "Design negative Python API tests", profile="qa-python",
                existing_skills=[], existing_roles=[], max_skills=3
            ),
        }
        observations = {
            name: take_samples(operation, samples)
            for name, operation in operations.items()
        }
    return {
        "classification": "OFFLINE_CI_OR_LOCAL_OPERATION_TIMINGS_NOT_CLIENT_PERFORMANCE",
        "source_sha": head.stdout.strip(),
        "python": platform.python_version(),
        "platform": platform.system(),
        "samples_per_operation": samples,
        "warmup_per_operation": 1,
        "latency_unit": "wall_clock_milliseconds",
        "p95_method": "nearest_rank",
        "categories": {
            "cli_*_process": "Includes Python startup and subprocess overhead",
            "*_inprocess": "Handler only; excludes MCP client, IPC, model and network",
        },
        "observations": observations,
        "user_project_execution": "NOT_RUN",
        "native_skill_activation": "NOT_OBSERVED",
        "model_tokens": "NOT_MEASURED",
        "model_effectiveness": "NOT_MEASURED",
        "model_or_paid_api_calls": 0,
        "recommendation": "MEASURED_BASELINE_ONLY_NO_OPTIMIZATION_WITHOUT_CONFIRMED_NEED",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--samples", type=int, default=12)
    args = parser.parse_args(argv)
    try:
        result = measure(args.root, args.samples)
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
