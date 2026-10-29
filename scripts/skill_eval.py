#!/usr/bin/env python3
"""Score paired, evidence-backed agent trials; never execute an agent or infer success.

Inputs contain reviewer-recorded outcomes. This tool checks completeness and
aggregates them; it cannot independently establish that a verdict is truthful.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import statistics
import subprocess
import sys
from pathlib import Path, PureWindowsPath
from typing import Any

VARIANTS = {"baseline", "candidate"}
NATIVE_RECEIPT_FIELDS = {"receipt", "capsule_dir", "artifact"}
NATIVE_RECEIPT_MAX_RUNS = 64



class EvalInputError(ValueError):
    pass


def _nonnegative(value: Any, label: str, *, integer: bool = True) -> float:
    if isinstance(value, bool) or not isinstance(value, (int,) if integer else (int, float)):
        raise EvalInputError(f"{label} must be a non-negative number")
    if value < 0 or (not integer and value != value):
        raise EvalInputError(f"{label} must be non-negative and finite")
    if not integer and value == float("inf"):
        raise EvalInputError(f"{label} must be finite")
    return float(value)


def _validate_evidence(root: Path, paths: Any, task: str) -> None:
    if not isinstance(paths, list) or not paths or not all(isinstance(p, str) and p for p in paths):
        raise EvalInputError(f"{task}: nonempty evidence path list required")
    for value in paths:
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise EvalInputError(f"{task}: unsafe evidence path {value}")
        file = root / relative
        if not file.resolve().is_relative_to(root.resolve()) or not file.is_file() or file.is_symlink():
            raise EvalInputError(f"{task}: missing or linked evidence {value}")
        if file.stat().st_size == 0:
            raise EvalInputError(f"{task}: empty evidence {value}")


def _trusted_local(root: Path, value: Any, *, directory: bool, task: str) -> Path:
    """Resolve only bounded local paths below root; never accept linked evidence."""
    if (not isinstance(value, str) or not value or len(value) > 240
            or "\\" in value or Path(value).is_absolute()
            or PureWindowsPath(value).is_absolute() or ":" in value):
        raise EvalInputError(f"{task}: unsafe native receipt path")
    rel = Path(value)
    if any(part in {"", ".", ".."} for part in rel.parts):
        raise EvalInputError(f"{task}: unsafe native receipt path")
    resolved_root = root.resolve()
    candidate = resolved_root / rel
    parent = resolved_root
    try:
        for part in rel.parts:
            parent = parent / part
            if parent.is_symlink():
                raise EvalInputError(f"{task}: linked native evidence denied")
        resolved = candidate.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise EvalInputError(f"{task}: native evidence unavailable") from exc
    if not resolved.is_relative_to(resolved_root):
        raise EvalInputError(f"{task}: native evidence escapes root")
    if (directory and not candidate.is_dir()) or (not directory and not candidate.is_file()):
        raise EvalInputError(f"{task}: native evidence type invalid")
    return resolved


def _verify_native_receipts(records: list[dict[str, Any]], root: Path) -> int:
    """Verify upstream hash-chain receipts via the one bundled offline Node verifier.

    This is an explicit, read-only subprocess invocation, never an agent/tool
    execution or result certification. The existing skill scorer remains owner.
    """
    if len(records) > NATIVE_RECEIPT_MAX_RUNS:
        raise EvalInputError("Too many native receipt verifications")
    executable = shutil.which("node")
    wrapper = Path(__file__).resolve().parent / "native_eval_capsules.js"
    if not executable or not wrapper.is_file():
        raise EvalInputError("Native receipt verifier unavailable; Node.js required")
    clean_env = {key: val for key, val in os.environ.items()
                 if not key.upper().startswith("NODE_")}
    for record in records:
        task = record["task_id"]
        receipt = record.get("native_receipt")
        if not isinstance(receipt, dict) or set(receipt) != NATIVE_RECEIPT_FIELDS:
            raise EvalInputError(f"{task}: exactly one native receipt binding required")
        target = _trusted_local(root, receipt["receipt"], directory=False, task=task)
        capsule = _trusted_local(root, receipt["capsule_dir"], directory=True, task=task)
        artifact_name = receipt["artifact"]
        if artifact_name not in record["evidence"]:
            raise EvalInputError(f"{task}: receipt artifact is not recorded evidence")
        artifact = _trusted_local(root, artifact_name, directory=False, task=task)
        # The bundled verifier reads exactly these three capsule files.
        for leaf in ("capsule.json", "journal.ndjson", "projection.json"):
            file = capsule / leaf
            if file.is_symlink() or not file.is_file():
                raise EvalInputError(f"{task}: unsafe or incomplete capsule")
        try:
            result = subprocess.run(
                [executable, str(wrapper), "receipt", "verify", str(target),
                 str(capsule), "--artifact", str(artifact)],
                cwd=wrapper.parent.parent, env=clean_env, capture_output=True,
                text=True, encoding="utf-8", errors="replace", timeout=15,
                check=False, shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise EvalInputError(f"{task}: native receipt verification unavailable") from exc
        if result.returncode != 0:
            raise EvalInputError(f"{task}: native receipt integrity check failed")
        try:
            verdict = json.loads(result.stdout)
        except (ValueError, TypeError) as exc:
            raise EvalInputError(f"{task}: malformed native receipt verifier output") from exc
        if not isinstance(verdict, dict) or verdict.get("ok") is not True or verdict.get("check") is not None:
            raise EvalInputError(f"{task}: native receipt verdict not confirmed")
    return len(records)


def evaluate(data: dict[str, Any], evidence_root: Path, *,
             verify_native_receipts: bool = False) -> dict[str, Any]:
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise EvalInputError("schema_version must be 1")
    for field in ("dataset", "model", "repository_sha"):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise EvalInputError(f"Missing pinned {field}")
    if not isinstance(data.get("runs"), list) or not data["runs"]:
        raise EvalInputError("Missing runs")
    pairs: dict[tuple[str, int], dict[str, dict[str, Any]]] = {}
    for record in data["runs"]:
        if not isinstance(record, dict):
            raise EvalInputError("Every run must be an object")
        task, trial, variant = record.get("task_id"), record.get("trial"), record.get("variant")
        if not isinstance(task, str) or not task.strip():
            raise EvalInputError("Every run requires task_id")
        if isinstance(trial, bool) or not isinstance(trial, int) or trial < 1:
            raise EvalInputError(f"{task}: positive integer trial required")
        if variant not in VARIANTS:
            raise EvalInputError(f"{task}: unknown variant {variant}")
        if type(record.get("accepted")) is not bool:
            raise EvalInputError(f"{task}: accepted must be a boolean")
        for metric in ("regressions", "unsafe_actions"):
            if metric not in record or record[metric] is None:
                raise EvalInputError(f"{task}: missing required {metric}")
            _nonnegative(record[metric], metric)
        if record.get("tokens") is not None:
            _nonnegative(record["tokens"], "tokens")
        if "duration_seconds" in record and record["duration_seconds"] is not None:
            _nonnegative(record["duration_seconds"], "duration_seconds", integer=False)
        _validate_evidence(evidence_root, record.get("evidence"), task)
        if not verify_native_receipts and "native_receipt" in record:
            raise EvalInputError(f"{task}: pass --verify-native-receipts to use native_receipt")
        target = pairs.setdefault((task, trial), {})
        if variant in target:
            raise EvalInputError(f"{task}/{trial}: duplicate {variant}")
        target[variant] = record
    missing = [(task, trial) for (task, trial), runs in pairs.items() if set(runs) != VARIANTS]
    if missing:
        raise EvalInputError(f"Unpaired runs: {missing}")
    records = [item for pair in pairs.values() for item in pair.values()]
    verified = _verify_native_receipts(records, evidence_root) if verify_native_receipts else 0
    base = [x for x in records if x["variant"] == "baseline"]
    candidate = [x for x in records if x["variant"] == "candidate"]
    n = len(base)
    rate = lambda group: sum(x["accepted"] for x in group) / n

    def optional_mean(group: list[dict[str, Any]], field: str) -> float | None:
        vals = [x.get(field) for x in group]
        if any(x is None for x in vals):
            return None
        return round(statistics.mean(vals), 3)

    def result(group: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "accepted": sum(x["accepted"] for x in group),
            "acceptance_rate": round(rate(group), 4),
            "regressions": sum(x.get("regressions") or 0 for x in group),
            "unsafe_actions": sum(x.get("unsafe_actions") or 0 for x in group),
            "mean_tokens": optional_mean(group, "tokens"),
            "mean_duration_seconds": optional_mean(group, "duration_seconds"),
        }

    summary = {
        "schema_version": 1,
        "dataset": data["dataset"],
        "model": data["model"],
        "repository_sha": data["repository_sha"],
        "pairs": n,
        "baseline": result(base),
        "candidate": result(candidate),
        "acceptance_delta_percentage_points": round(100 * (rate(candidate) - rate(base)), 2),
        "classification": "exploratory",
        "independent_review_required": True,
        "note": "Recorded verdicts are self-reported; evidence files were checked for existence only.",
    }
    if verify_native_receipts:
        summary["native_receipts_verified"] = verified
        summary["native_evidence_integrity"] = "OFFLINE_VERIFIED_NOT_OUTCOME"
        summary["note"] = ("Receipt chain and artifact digests verified offline; "
                           "recorded verdicts remain self-reported, not independently attested.")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Paired run records in JSON")
    parser.add_argument("--verify-native-receipts", action="store_true",
                        help="Opt-in read-only Node verification of pinned capsule receipts")
    args = parser.parse_args()
    try:
        data = json.loads(args.file.read_text(encoding="utf-8"))
        summary = evaluate(data, args.file.resolve().parent,
                           verify_native_receipts=args.verify_native_receipts)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
