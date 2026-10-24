#!/usr/bin/env python3
"""Deterministic, offline orchestration advice. Never starts agents or runs tests."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FIELDS = {
    "schema_version", "scope", "independent_readonly_streams",
    "writes_required", "parallel_capability", "owner_parallel_approval",
    "zero_incremental_cost_verified", "isolation_verified",
}
CAPABILITY = {"VERIFIED", "NOT_VERIFIED", "UNAVAILABLE"}
SCOPE = {"SMALL", "MEDIUM", "LARGE"}


class DecisionError(ValueError):
    """Invalid or overclaimed orchestration evidence."""


def decide(request: Any) -> dict[str, Any]:
    """Return safe advice; claimed capability is an input, not tool verification."""
    if not isinstance(request, dict) or set(request) != FIELDS:
        raise DecisionError("INVALID_REQUEST_FIELDS")
    if type(request["schema_version"]) is not int or request["schema_version"] != 1:
        raise DecisionError("INVALID_SCHEMA_VERSION")
    if not isinstance(request["scope"], str) or request["scope"] not in SCOPE:
        raise DecisionError("INVALID_SCOPE")
    count = request["independent_readonly_streams"]
    if type(count) is not int or not 0 <= count <= 3:
        raise DecisionError("INVALID_STREAM_COUNT")
    if not isinstance(request["parallel_capability"], str) or request["parallel_capability"] not in CAPABILITY:
        raise DecisionError("INVALID_PARALLEL_CAPABILITY")
    for field in ("writes_required", "owner_parallel_approval",
                  "zero_incremental_cost_verified", "isolation_verified"):
        if type(request[field]) is not bool:
            raise DecisionError("INVALID_BOOLEAN_" + field.upper())

    qualified = (
        request["scope"] != "SMALL"
        and not request["writes_required"]
        and count >= 2
        and request["parallel_capability"] == "VERIFIED"
        and request["owner_parallel_approval"]
        and request["zero_incremental_cost_verified"]
        and request["isolation_verified"]
    )
    if qualified:
        route, reason = "OPTIONAL_PARALLEL_READONLY_REVIEW", "INDEPENDENT_READONLY_APPROVED_AND_VERIFIED"
    elif request["scope"] == "SMALL":
        route, reason = "SINGLE_AGENT", "LOCALIZED_TASK_NO_EXTRA_COORDINATION"
    elif request["writes_required"]:
        route, reason = "SEQUENTIAL_REVIEW", "ONE_WRITER_AVOIDS_CONCURRENT_MUTATION"
    else:
        route, reason = "SEQUENTIAL_REVIEW", "PARALLEL_GATE_UNSATISFIED"

    blockers = []
    if not qualified and request["scope"] != "SMALL":
        if request["writes_required"]:
            blockers.append("WRITES_REQUIRED")
        if count < 2:
            blockers.append("NOT_INDEPENDENT_STREAMS")
        if request["parallel_capability"] != "VERIFIED":
            blockers.append("PARALLEL_CAPABILITY_NOT_VERIFIED")
        if not request["owner_parallel_approval"]:
            blockers.append("OWNER_APPROVAL_MISSING")
        if not request["zero_incremental_cost_verified"]:
            blockers.append("ZERO_COST_NOT_VERIFIED")
        if not request["isolation_verified"]:
            blockers.append("ISOLATION_NOT_VERIFIED")
    return {
        "schema_version": 1,
        "recommended_route": route,
        "reason_code": reason,
        "parallel_gate_blockers": blockers,
        "scope": request["scope"],
        "advice_only": True,
        "execution": "NOT_RUN",
        "workers_launched": 0,
        "target_project_changed": False,
        "client_activation": "NOT_VERIFIED",
        "time_savings": "NOT_MEASURED",
        "token_savings": "NOT_MEASURED",
        "client_benefit": "NOT_MEASURED",
        "evidence_basis": "BOUNDED_INPUT_DECLARATION_NOT_RUNTIME_PROOF",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request", type=Path, help="Local JSON declaration. No filesystem writes.")
    args = parser.parse_args(argv)
    try:
        result = decide(json.loads(args.request.read_text(encoding="utf-8")))
    except (OSError, UnicodeError, ValueError) as exc:
        print(json.dumps({"status": "INVALID_REQUEST", "reason": str(exc)}))
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
