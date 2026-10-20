#!/usr/bin/env python3
"""Issue #59: bounded in-process performance contracts and synthetic examples.

No HTTP, external targets, production load, paid dependencies or speed SLO in CI.
Virtual samples are arithmetic fixtures, NOT actual performance measurements.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
import json
import math
import statistics
import time

MAX_SECONDS = 10.0
MAX_RPS = 5.0
MAX_OPS = 50
MAX_CONCURRENCY = 2
STATUSES = frozenset({
    "SUCCESS", "APPLICATION_ERROR", "TIMEOUT", "TRANSPORT_ERROR",
    "TEST_HARNESS_ERROR", "CANCELLED",
})
RESULTS = frozenset({
    "PASS", "REGRESSION", "INCONCLUSIVE", "COMPARISON_INVALID",
    "NOT_MEASURED", "BLOCKED",
})


class UnsafeWorkload(ValueError):
    """Rejected before any load is generated."""


def _number(value: object, name: str, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise UnsafeWorkload(f"{name}: finite number required")
    if not math.isfinite(value) or not 0 < value <= maximum:
        raise UnsafeWorkload(f"{name}: must be > 0 and <= {maximum}")
    return float(value)


@dataclass(frozen=True)
class Workload:
    profile: str = "constant"
    operations: int = 12
    rps: float = 5.0
    duration: float = 5.0
    concurrency: int = 1
    warmup: int = 2
    dataset: str = "fictional-v1"
    cache_state: str = "in-process-cold"
    environment: str = "local-synthetic"

    def slots(self) -> list[float]:
        if self.profile not in {"constant", "step", "mixed"}:
            raise UnsafeWorkload("unsupported workload profile")
        if type(self.operations) is not int or not 1 <= self.operations <= MAX_OPS:
            raise UnsafeWorkload("operations out of bounds")
        if type(self.concurrency) is not int or not 1 <= self.concurrency <= MAX_CONCURRENCY:
            raise UnsafeWorkload("concurrency out of bounds")
        if type(self.warmup) is not int or not 0 <= self.warmup <= 4:
            raise UnsafeWorkload("warmup out of bounds")
        if self.operations + self.warmup > MAX_OPS:
            raise UnsafeWorkload("total work including warmup exceeds 50")
        rate = _number(self.rps, "rps", MAX_RPS)
        duration = _number(self.duration, "duration", MAX_SECONDS)
        for name in ("dataset", "cache_state", "environment"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 80:
                raise UnsafeWorkload(f"{name}: nonempty bounded identifier required")
        if self.profile != "step":
            slots = [i / rate for i in range(self.operations)]
        else:
            half = self.operations // 2
            low_rate = rate / 2
            slots = [i / low_rate for i in range(half)]
            offset = half / low_rate
            slots += [offset + j / rate for j in range(self.operations - half)]
        if slots and slots[-1] >= duration:
            raise UnsafeWorkload("scheduled operations exceed duration")
        return slots


def _reference(n: int) -> int:
    return sum((i * i) % 97 for i in range(n))


def _candidate(n: int) -> int:
    cycles, remainder = divmod(n, 97)
    return cycles * sum((i * i) % 97 for i in range(97)) + sum(
        (i * i) % 97 for i in range(remainder)
    )


def _operation(index: int, profile: str, variant: str) -> tuple[str, int, bool]:
    operation = "checksum-plus" if profile == "mixed" and index % 2 else "checksum"
    n = 200 + (index % 5) * 17 + (1 if operation == "checksum-plus" else 0)
    expected = _reference(n)
    if variant == "baseline":
        observed = _reference(n)
    elif variant == "candidate":
        observed = _candidate(n)
    elif variant == "broken-fast":
        observed = 0
    else:
        raise UnsafeWorkload("unknown variant")
    return operation, observed, observed == expected


def percentile(values: list[float], q: float) -> float:
    """Type-7 linear interpolation (index=(n-1)*q), never nearest-rank."""
    if not values or not 0 <= q <= 1:
        raise ValueError("nonempty values and 0 <= q <= 1 required")
    ordered = sorted(values)
    index = (len(ordered) - 1) * q
    lower = math.floor(index)
    upper = math.ceil(index)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def aggregate(samples: list[dict], interval_s: float) -> dict:
    duration = _number(interval_s, "measurement interval", MAX_SECONDS + 1)
    if not samples:
        raise ValueError("no samples")
    if any(not isinstance(s, dict) or s.get("status") not in STATUSES for s in samples):
        raise ValueError("unknown or missing sample status")
    completed = [s for s in samples if s.get("end_ms") is not None]
    successes = [s for s in completed if s["status"] == "SUCCESS"]
    latencies = [float(s["latency_ms"]) for s in completed]
    if any(not math.isfinite(x) or x < 0 for x in latencies):
        raise ValueError("invalid latency")
    errors = len(samples) - len(successes)
    return {
        "attempted": len(samples),
        "completed": len(completed),
        "successful": len(successes),
        "errors": errors,
        "timeouts": sum(s["status"] == "TIMEOUT" for s in samples),
        "error_fraction": errors / len(samples),
        "error_numerator": errors,
        "error_denominator": len(samples),
        "attempted_ops_s": len(samples) / duration,
        "completed_ops_s": len(completed) / duration,
        "successful_ops_s": len(successes) / duration,
        "latency_ms": {
            "n": len(latencies),
            "mean": statistics.mean(latencies) if latencies else None,
            "median": statistics.median(latencies) if latencies else None,
            "min": min(latencies) if latencies else None,
            "max": max(latencies) if latencies else None,
            "range": max(latencies) - min(latencies) if latencies else None,
            "p95": percentile(latencies, .95) if len(latencies) >= 20 else None,
            "p99": percentile(latencies, .99) if len(latencies) >= 100 else None,
        },
    }


def run(workload: Workload, variant: str = "baseline", *,
        virtual: bool = True, budget_ms: float | None = None,
        budget_approved: bool = False) -> dict:
    """Execute only a bounded built-in function; virtual times are explicitly fictional."""
    slots = workload.slots()
    if variant not in {"baseline", "candidate", "broken-fast"}:
        raise UnsafeWorkload("unsupported local variant")
    if budget_ms is not None:
        _number(budget_ms, "budget_ms", 60000)
    if type(budget_approved) is not bool:
        raise UnsafeWorkload("budget_approved must be bool")
    if budget_approved and budget_ms is None:
        raise UnsafeWorkload("approved budget must have a threshold")

    for i in range(workload.warmup):
        _operation(i, workload.profile, variant)

    samples: list[dict] = []
    if virtual:
        for i, slot in enumerate(slots):
            name, _, correct = _operation(i, workload.profile, variant)
            latency = (0.5 if variant == "broken-fast" else
                       3.0 if variant == "candidate" else 5.0) + i % 3
            samples.append({
                "id": i, "operation": name, "start_ms": slot * 1000,
                "end_ms": slot * 1000 + latency, "latency_ms": latency,
                "status": "SUCCESS" if correct else "APPLICATION_ERROR",
                "functional_ok": correct,
            })
        interval = max(slots[-1] + samples[-1]["latency_ms"] / 1000, .001)
    else:
        start = time.monotonic()
        def invoke(index: int) -> dict:
            began = time.monotonic_ns()
            name, _, correct = _operation(index, workload.profile, variant)
            ended = time.monotonic_ns()
            return {
                "id": index, "operation": name,
                "start_ms": (began / 1e6),
                "end_ms": (ended / 1e6),
                "latency_ms": (ended - began) / 1e6,
                "status": "SUCCESS" if correct else "APPLICATION_ERROR",
                "functional_ok": correct,
            }
        with ThreadPoolExecutor(max_workers=workload.concurrency) as executor:
            futures = []
            for i, slot in enumerate(slots):
                remaining = start + slot - time.monotonic()
                if remaining > 0:
                    time.sleep(remaining)
                if time.monotonic() - start >= workload.duration:
                    raise UnsafeWorkload("hard measurement deadline reached")
                futures.append(executor.submit(invoke, i))
            samples = [future.result(timeout=1) for future in futures]
        interval = time.monotonic() - start
        if interval > MAX_SECONDS + 0.5:
            raise UnsafeWorkload("hard overall deadline exceeded")
    measured = aggregate(samples, interval)
    return {
        "test_id": "issue-59-synthetic", "scenario_id": workload.profile,
        "source_requirement": "Issue #59",
        "target_component": "in-process fictional checksum",
        "revision": variant,
        "conditions": {
            "profile": workload.profile, "operations": workload.operations,
            "rps": workload.rps, "duration": workload.duration,
            "concurrency": workload.concurrency, "warmup": workload.warmup,
            "dataset": workload.dataset, "cache_state": workload.cache_state,
            "environment": workload.environment,
            "mode": "VIRTUAL_FIXTURE" if virtual else "LOCAL_SMOKE",
            "method": "monotonic_ns" if not virtual else "fixed virtual timestamps",
            "percentile": "type-7 linear",
        },
        "bounds": {
            "rps_max": MAX_RPS, "operations_max": MAX_OPS,
            "concurrency_max": MAX_CONCURRENCY, "duration_max_s": MAX_SECONDS,
            "network": "DISABLED_BY_DESIGN",
        },
        "measurement_interval_s": interval,
        "samples": samples, "metrics": measured,
        "functional_correctness": all(s["functional_ok"] for s in samples),
        "budget": {"metric": "median_latency_ms", "threshold": budget_ms,
                   "approval": "APPROVED" if budget_approved else "PROPOSED"},
        "resource_usage": "NOT_MEASURED",
        "limitations": ["synthetic in-process only", "no production or real-app evidence"],
    }


def validate_report(report: object) -> None:
    if not isinstance(report, dict):
        raise ValueError("report must be an object")
    for key in ("conditions", "samples", "metrics", "budget", "functional_correctness"):
        if key not in report:
            raise ValueError(f"report missing {key}")
    samples = report["samples"]
    if not isinstance(samples, list) or not samples:
        raise ValueError("missing raw samples")
    metrics = aggregate(samples, report.get("measurement_interval_s"))
    if metrics != report["metrics"]:
        raise ValueError("aggregate metrics differ from raw samples")
    if any("functional_ok" not in s or "id" not in s for s in samples):
        raise ValueError("missing operation oracle")
    if report["functional_correctness"] != all(s["functional_ok"] for s in samples):
        raise ValueError("functional oracle mismatch")
    if not isinstance(report["conditions"], dict) or not isinstance(report["budget"], dict):
        raise ValueError("invalid conditions/budget")


def compare(baseline: dict | None, candidate: dict | None) -> dict:
    if baseline is None or candidate is None:
        return {"status": "NOT_MEASURED", "reason": "baseline or candidate missing"}
    try:
        validate_report(baseline)
        validate_report(candidate)
    except (ValueError, TypeError, KeyError, ZeroDivisionError) as exc:
        return {"status": "COMPARISON_INVALID", "reason": f"invalid report: {exc}"}
    if baseline["conditions"] != candidate["conditions"]:
        return {"status": "COMPARISON_INVALID", "reason": "environment/workload/method mismatch"}
    if baseline["budget"] != candidate["budget"]:
        return {"status": "COMPARISON_INVALID", "reason": "budget changed between measurements"}
    if not baseline["functional_correctness"] or not candidate["functional_correctness"]:
        return {"status": "BLOCKED", "reason": "functional oracle failed"}
    a, b = baseline["metrics"], candidate["metrics"]
    if a["successful"] < 5 or b["successful"] < 5:
        return {"status": "INCONCLUSIVE", "reason": "too few valid observations"}
    if b["error_fraction"] > a["error_fraction"] or b["successful"] < a["successful"]:
        return {"status": "REGRESSION", "reason": "errors increased or successes dropped"}
    base, new = a["latency_ms"]["median"], b["latency_ms"]["median"]
    threshold = baseline["budget"]["threshold"]
    if baseline["budget"]["approval"] == "APPROVED" and threshold is not None and new > threshold:
        return {"status": "REGRESSION", "reason": "approved median budget exceeded"}
    raw = [s["latency_ms"] for s in baseline["samples"] if s["status"] == "SUCCESS"]
    noise = statistics.median(abs(x - base) for x in raw) / base if base else 0
    tolerance = max(.05, 2 * noise)
    status = "REGRESSION" if new > base * (1 + tolerance) else "PASS"
    return {
        "status": status, "baseline_median_ms": base, "candidate_median_ms": new,
        "relative_change": (new / base - 1) if base else None,
        "noise_tolerance": tolerance,
        "reason": "observed median regression" if status == "REGRESSION"
                  else "no demonstrated regression; not proof of universal speed",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("constant", "step", "mixed"),
                        default="constant")
    parser.add_argument("--operations", type=int, default=12)
    parser.add_argument("--rps", type=float, default=5.0)
    parser.add_argument("--duration", type=float, default=5.0)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--mode", choices=("virtual", "local"), default="virtual")
    parser.add_argument("--budget-ms", type=float)
    args = parser.parse_args()
    try:
        workload = Workload(profile=args.profile, operations=args.operations,
                            rps=args.rps, duration=args.duration,
                            concurrency=args.concurrency)
        baseline = run(workload, "baseline", virtual=args.mode == "virtual",
                       budget_ms=args.budget_ms)
        candidate = run(workload, "candidate", virtual=args.mode == "virtual",
                        budget_ms=args.budget_ms)
        print(json.dumps({"comparison": compare(baseline, candidate),
                          "baseline": baseline, "candidate": candidate}, indent=2))
    except (UnsafeWorkload, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
