#!/usr/bin/env python3
"""Opt-in, synthetic-only, offline acceptance gate for original Headroom.

No Codex CLI, network, API keys, hooks, proxy, or real user/session inputs.
Source-only release does not imply user-client installation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Callable

UPSTREAM = "headroomlabs-ai/headroom@3fef15d376d9899f77a28464e2e91f8b99514930"
PACKAGE_VERSION = "0.41.0"
CRITICAL = {
    "sha": "a" * 40,
    "approval": "DENIED",
    "deploy": "NOT_VERIFIED",
    "ci": "UNKNOWN",
    "status": "HOLD",
}
MIN_SAVINGS_PCT = 5.0


def synthetic_messages() -> list[dict[str, Any]]:
    """Only deterministic synthetic data; never load sessions from disk."""
    rows = [
        {"id": n, "path": f"/synthetic/p/{n:04d}.py",
         "code": "abcxyz" * 20, "result": "OK"}
        for n in range(600)
    ]
    tool_payload = json.dumps(
        {"evidence": CRITICAL, "rows": rows}, sort_keys=True, separators=(",", ":")
    )
    return [
        {"role": "system", "content": "Preserve exact SHA, approval and deploy states."},
        {"role": "user", "content": "Review the synthetic evidence."},
        {"role": "tool", "tool_call_id": "synthetic-call-1", "content": tool_payload},
    ]


def evaluate(
    compressor: Callable[[list[dict[str, Any]]], Any],
    *,
    minimum_savings_pct: float = MIN_SAVINGS_PCT,
) -> dict[str, Any]:
    """Measure a candidate; UNKNOWN or lossy means NO_GO, not release."""
    if not 0 <= minimum_savings_pct <= 100:
        raise ValueError("invalid_savings_threshold")
    source = synthetic_messages()
    try:
        candidate = compressor(source)
    except Exception:
        # Never render exception text: third-party errors can include tool payload.
        return {"decision": "NO_GO", "reason": "compression_failed"}
    before = getattr(candidate, "tokens_before", None)
    after = getattr(candidate, "tokens_after", None)
    output = getattr(candidate, "messages", None)
    lossless = getattr(candidate, "lossless", None)
    if not (
        type(before) is int and type(after) is int
        and before > 0 and 0 <= after <= before
        and isinstance(output, list)
    ):
        return {"decision": "NO_GO", "reason": "invalid_measurement"}
    try:
        tool = [item for item in output
                if isinstance(item, dict) and item.get("role") == "tool"]
        if len(tool) != 1 or not isinstance(tool[0].get("content"), str):
            raise ValueError("tool_response_missing")
        decoded = json.loads(tool[0]["content"])
        evidence_preserved = (
            isinstance(decoded, dict) and decoded.get("evidence") == CRITICAL
        )
    except (ValueError, TypeError):
        evidence_preserved = False
    saved = before - after
    pct = round(100 * saved / before, 2)
    eligible = lossless is True and evidence_preserved and pct >= minimum_savings_pct
    reasons = []
    if lossless is not True:
        reasons.append("lossless_not_proven")
    if not evidence_preserved:
        reasons.append("critical_evidence_not_preserved")
    if pct < minimum_savings_pct:
        reasons.append("insufficient_savings")
    return {
        "decision": "PILOT_ELIGIBLE" if eligible else "NO_GO",
        "reason": ",".join(reasons) if reasons else "offline_gate_passed",
        "model_api_calls": 0,
        "codex_cli_calls": 0,
        "package": f"headroom-ai=={PACKAGE_VERSION}",
        "upstream": UPSTREAM,
        "sample": "synthetic_only",
        "mode": "agent",
        "tokens_before": before,
        "tokens_after": after,
        "tokens_saved": saved,
        "savings_pct": pct,
        "lossless_verified": lossless is True,
        "critical_evidence_preserved": bool(evidence_preserved),
        "user_runtime_verified": False,
        "actual_model_usage_measured": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--minimum-savings-pct", type=float, default=MIN_SAVINGS_PCT)
    args = parser.parse_args(argv)
    if not 0 <= args.minimum_savings_pct <= 100:
        parser.error("minimum savings must be 0 through 100")
    try:
        from headroom import CompressConfig, compress
    except ImportError:
        print(json.dumps({"decision": "BLOCKED", "reason": "upstream_not_installed",
                          "model_api_calls": 0, "codex_cli_calls": 0}, sort_keys=True))
        return 3

    def run(messages: list[dict[str, Any]]) -> Any:
        return compress(
            messages,
            model="gpt-4o",  # Tokenizer selector only; NEVER a model invocation.
            config=CompressConfig(
                mode="agent",
                protect_recent=0,
                protect_analysis_context=False,
                diagnostics=True,
                kompress_model="disabled",
            ),
        )

    report = evaluate(run, minimum_savings_pct=args.minimum_savings_pct)
    print(json.dumps(report, sort_keys=True))
    return 0 if report["decision"] == "PILOT_ELIGIBLE" else 2


if __name__ == "__main__":
    sys.exit(main())
