#!/usr/bin/env python3
"""Offline #432 synthetic benchmark; diagnostic only, never executes fixture commands.

The 38 labeled cases live in a separate SHA256-inventoried JSON file.
They were committed before the baseline run. Findings never contain fixture
text, secret-like literals, or absolute temporary paths.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tempfile

import cisco_mcp_gate
import external_skill_gate

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "fixtures" / "native_security_holdout_432.json"
# Explicitly version and review any corpus changes, independently of SHA256SUMS.
CORPUS_SHA256 = "6697030f91649f0b05a113216bb49e6636d2bfe60f7d91cbf9062d807b18265e"
MAX_CORPUS_BYTES = 65536
CASE_ID = re.compile(r"[MH][0-9]{2}\Z")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate benchmark key")
        result[name] = value
    return result


def load_cases() -> tuple[list[dict], str]:
    if CORPUS.is_symlink() or not CORPUS.is_file():
        raise ValueError("benchmark corpus absent or linked")
    raw = CORPUS.read_bytes()
    if len(raw) > MAX_CORPUS_BYTES:
        raise ValueError("oversized benchmark corpus")
    if hashlib.sha256(raw).hexdigest() != CORPUS_SHA256:
        raise ValueError("benchmark corpus digest mismatch")
    doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                     parse_constant=lambda _: (_ for _ in ()).throw(ValueError("NaN")))
    if (not isinstance(doc, dict) or doc.get("schema_version") != 1
            or doc.get("origin") != "AUTHOR_CREATED_SYNTHETIC_NOT_REAL_WORLD"
            or doc.get("tuning_role") != "FROZEN_BEFORE_BASELINE_MEASUREMENT"):
        raise ValueError("unverified benchmark declaration")
    cases = doc.get("cases")
    if not isinstance(cases, list) or len(cases) != 38:
        raise ValueError("unexpected benchmark case count")
    names = set()
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError("invalid benchmark case")
        name = case.get("id")
        if not isinstance(name, str) or not CASE_ID.fullmatch(name) or name in names:
            raise ValueError("duplicate/invalid benchmark ID")
        names.add(name)
        if type(case.get("attack")) is not bool:
            raise ValueError("missing attack label")
        if case.get("surface") == "mcp_description":
            if (set(case) != {"id", "surface", "category", "attack", "description", "nested"}
                    or not isinstance(case["description"], str)
                    or not isinstance(case["nested"], bool)
                    or len(case["description"].encode("utf-8")) > 2048):
                raise ValueError("invalid MCP fixture")
        elif case.get("surface") == "host_config":
            if (set(case) != {"id", "surface", "category", "attack", "path", "text"}
                    or case["path"] not in external_skill_gate.HOST_FILES
                    or not isinstance(case["text"], str)
                    or len(case["text"].encode("utf-8")) > 4096):
                raise ValueError("invalid host fixture")
        else:
            raise ValueError("unknown benchmark surface")
        if not isinstance(case["category"], str) or not re.fullmatch(
                r"[a-z_]{3,32}", case["category"]):
            raise ValueError("invalid category")
    if sum(case["attack"] for case in cases) != 19:
        raise ValueError("unexpected benchmark labels")
    return cases, hashlib.sha256(raw).hexdigest()


def _scan(case: dict) -> bool:
    """Only the existing first-party scanners are used - no forked scanner."""
    if case["surface"] == "mcp_description":
        desc = case["description"]
        definition = {"name": "toolkit_fixture", "description": "Read-only synthetic fixture",
                      "inputSchema": {"type": "object", "properties": {}}}
        if case["nested"]:
            definition["inputSchema"]["properties"] = {
                "payload": {"type": "string", "description": desc}}
        else:
            definition["description"] = desc
        result = cisco_mcp_gate.scan_native_descriptions(
            data={"tools": [definition]})
        if (result.get("reason") != "HEURISTIC_STATIC_ONLY"
                or result.get("external_scanner") != "NOT_USED"
                or result.get("live_mcp") != "NOT_RUN"):
            raise ValueError("MCP fixture evaluation incomplete")
        return result["status"] != "PASS"

    with tempfile.TemporaryDirectory(prefix="adt-432-synthetic-") as directory:
        root = Path(directory)
        target = root / case["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        content = case["text"].encode("utf-8")
        target.write_bytes(content)
        report = external_skill_gate.review_host_config(root)
        if (report.get("network") != "NOT_USED"
                or report.get("execution") != "NOT_RUN"
                or report.get("decision") not in ("PASS", "REVIEW_REQUIRED", "BLOCKED")
                or not report["evidence"]["files"]
                or report["evidence"]["files"][0]["sha256"] != hashlib.sha256(content).hexdigest()
                or target.read_bytes() != content):
            raise ValueError("host fixture evaluation incomplete or mutated")
        return report["decision"] != "PASS"


def _metrics(tp: int, fp: int, tn: int, fn: int) -> dict:
    return {
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "precision": round(tp / (tp + fp), 4) if tp + fp else None,
        "recall": round(tp / (tp + fn), 4) if tp + fn else None,
        "f1": round(2 * tp / (2 * tp + fp + fn), 4)
        if 2 * tp + fp + fn else None,
    }


def benchmark() -> dict:
    cases, digest = load_cases()
    counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    grouped: dict[str, dict] = {}
    errors = {"false_positive_ids": [], "false_negative_ids": []}
    for case in cases:
        alert = _scan(case)
        expected = case["attack"]
        key = ("tp" if alert else "fn") if expected else ("fp" if alert else "tn")
        counts[key] += 1
        category = case["surface"] + "/" + case["category"]
        row = grouped.setdefault(category, {"tp": 0, "fp": 0, "tn": 0, "fn": 0})
        row[key] += 1
        if key == "fp":
            errors["false_positive_ids"].append(case["id"])
        if key == "fn":
            errors["false_negative_ids"].append(case["id"])
    if sum(counts.values()) != len(cases):
        raise ValueError("incomplete benchmark")
    return {
        "schema_version": 1,
        "dataset": CORPUS.name,
        "dataset_sha256": digest,
        "sample_count": len(cases),
        "positive_count": sum(c["attack"] for c in cases),
        "negative_count": sum(not c["attack"] for c in cases),
        "confusion_matrix": counts,
        **{key: value for key, value in _metrics(**counts).items() if key not in counts},
        "by_category": {category: _metrics(**row) for category, row in sorted(grouped.items())},
        **errors,
        "status": "DIAGNOSTIC_ONLY",
        "holdout": "NEW_SYNTHETIC_DISJOINT_FROM_V1_NOT_INDEPENDENT_REAL_DATA",
        "upstream_agentshield_comparison": "NOT_RUN",
        "representative_real_world_accuracy": "NOT_MEASURED",
        "client_runtime": "NOT_VERIFIED",
        "network": "NOT_USED",
        "model_api": "NOT_USED",
    }


def main() -> int:
    try:
        result = benchmark()
    except (ValueError, UnicodeError, OSError, TypeError, KeyError) as exc:
        # Never echo untrusted text or absolute file paths in errors.
        print(json.dumps({"status": "BLOCKED", "reason": type(exc).__name__}))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0  # Measurement finished, NOT a security authorization.


if __name__ == "__main__":
    raise SystemExit(main())
