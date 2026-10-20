#!/usr/bin/env python3
"""Issue #57: deterministic, offline contract probes, NOT a model evaluator.

No model runner, provider access, network, filesystem writes or tokens/cost estimation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
STATUS = {"PASS", "FAIL", "NOT_RUN", "NOT_MEASURED", "BLOCKED", "NOT_APPLICABLE"}
CASE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{1,63}$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SHA = re.compile(r"^[a-f0-9]{64}$")
STAGES = ("dataset_prepared", "contract_validated", "oracle_validated",
          "execution_completed", "acceptance_verified", "effectiveness_measured")
PROHIBITED_COST_KEYS = {"estimated_tokens", "estimated_cost", "inferred_usage"}
TYPES = {"str": str, "int": int, "bool": bool, "list": list}


def digest_cases(cases: list[dict]) -> str:
    """Hash canonical UTF-8 case contents; version and metadata are separate."""
    content = json.dumps(cases, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def validate_dataset(dataset: dict) -> list[str]:
    errors = []
    if not isinstance(dataset, dict):
        return ["dataset must be object"]
    required = ("dataset_id", "version", "sha256", "categories", "limitations", "cases")
    if any(key not in dataset for key in required):
        return ["dataset missing required fields"]
    if not isinstance(dataset["dataset_id"], str) or not CASE_ID.fullmatch(dataset["dataset_id"]):
        errors.append("invalid dataset_id")
    if not isinstance(dataset["version"], str) or not VERSION.fullmatch(dataset["version"]):
        errors.append("invalid dataset version")
    if not isinstance(dataset["limitations"], list) or not dataset["limitations"]:
        errors.append("dataset limitations missing")
    categories = dataset["categories"]
    if not isinstance(categories, list) or not categories or any(not isinstance(x, str) or not x for x in categories):
        errors.append("invalid categories")
        categories = []
    cases = dataset["cases"]
    if not isinstance(cases, list) or not cases:
        return errors + ["cases missing"]
    ids = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("invalid case")
            continue
        ident = case.get("id")
        if not isinstance(ident, str) or not CASE_ID.fullmatch(ident):
            errors.append("invalid Case ID")
        elif ident in ids:
            errors.append("duplicate Case ID: " + ident)
        ids.add(ident)
        for field in ("category", "source", "input", "oracle"):
            if not isinstance(case.get(field), (str if field != "oracle" else dict)) or not case[field]:
                errors.append(f"{ident}: missing {field}")
        if case.get("category") not in categories:
            errors.append(f"{ident}: unknown category")
        for field in ("expected_properties", "negative_conditions"):
            if not isinstance(case.get(field), list) or not case[field] or any(not isinstance(x, str) or not x for x in case[field]):
                errors.append(f"{ident}: invalid {field}")
        oracle = case.get("oracle")
        if isinstance(oracle, dict) and (
            oracle.get("type") not in {"schema", "reference", "tool_contract", "retrieval_membership", "human_review"}
            or not isinstance(oracle.get("assertion"), str) or not oracle["assertion"]):
            errors.append(f"{ident}: invalid independent oracle")
    if not isinstance(dataset["sha256"], str) or not SHA.fullmatch(dataset["sha256"]) or dataset["sha256"] != digest_cases(cases):
        errors.append("dataset SHA256 mismatch")
    return errors


def validate_evaluation(record: dict, dataset: dict) -> list[str]:
    errors = validate_dataset(dataset)
    if not isinstance(record, dict):
        return errors + ["evaluation must be object"]
    required = ("evaluation_id", "dataset_id", "dataset_version", "dataset_sha256",
                "scenario_id", "scenario_category", "model_id", "provider", "model_revision",
                "prompt_version", "tool_configuration", "retrieval_configuration",
                "baseline", "candidate", "expected_properties", "negative_conditions",
                "independent_oracle", "execution_environment", "actual_observations",
                "evidence_refs", "limitations", "lifecycle", "result_status",
                "execution_type", "metrics")
    if any(k not in record for k in required):
        return errors + ["evaluation missing required fields"]
    for a, b in (("dataset_id", "dataset_id"), ("dataset_version", "version"),
                 ("dataset_sha256", "sha256")):
        if record[a] != dataset[b]:
            errors.append("evaluation " + a + " mismatch")
    if record["scenario_id"] not in [c.get("id") for c in dataset["cases"] if isinstance(c, dict)]:
        errors.append("unknown scenario_id")
    if not isinstance(record["prompt_version"], str) or not VERSION.fullmatch(record["prompt_version"]):
        errors.append("invalid prompt_version")
    if record["result_status"] not in STATUS:
        errors.append("invalid result_status")
    if not isinstance(record["lifecycle"], dict) or set(record["lifecycle"]) != set(STAGES) or any(x not in STATUS for x in record["lifecycle"].values()):
        errors.append("invalid lifecycle")
    if record["execution_type"] != "real":
        for stage in STAGES[3:]:
            if record["lifecycle"].get(stage) == "PASS":
                errors.append("offline PASS claimed for " + stage)
    if record["execution_type"] == "real" and record["lifecycle"].get("execution_completed") == "PASS":
        if not record["evidence_refs"] or not record["actual_observations"]:
            errors.append("executed without actual observations/evidence")
    if record["lifecycle"].get("acceptance_verified") == "PASS" and record["lifecycle"].get("execution_completed") != "PASS":
        errors.append("acceptance without execution")
    if record["lifecycle"].get("effectiveness_measured") == "PASS" and record["lifecycle"].get("acceptance_verified") != "PASS":
        errors.append("effectiveness without acceptance")
    if not isinstance(record["metrics"], dict) or PROHIBITED_COST_KEYS.intersection(record["metrics"]):
        errors.append("invented metric field")
    else:
        for key in ("latency_seconds", "tokens", "cost"):
            item = record["metrics"].get(key)
            if not isinstance(item, dict) or item.get("status") not in STATUS:
                errors.append("missing metric evidence status: " + key)
            elif item["status"] == "PASS" and (item.get("value") is None or not item.get("source")):
                errors.append("invented " + key + " measurement")
    return errors


def retrieval_metrics(ranked: list[str], relevant: dict[str, int], k: int) -> dict:
    """Only for manually annotated relevance; zero relevant => NOT_MEASURED."""
    if not isinstance(k, int) or k < 1 or k > 1000:
        raise ValueError("invalid k")
    if len(ranked) != len(set(ranked)) or not all(isinstance(x, str) and x for x in ranked):
        raise ValueError("invalid or duplicated ranked IDs")
    if not isinstance(relevant, dict) or any(type(v) is not int or v < 0 or v > 3 for v in relevant.values()):
        raise ValueError("invalid gold relevance")
    positives = {ident for ident, grade in relevant.items() if grade > 0}
    if not positives:
        return {"status": "NOT_MEASURED"}
    top = ranked[:k]
    hits = sum(x in positives for x in top)
    first = next((i for i, x in enumerate(ranked, 1) if x in positives), None)
    gain = lambda grade: 2 ** grade - 1
    dcg = sum(gain(relevant.get(x, 0)) / math.log2(i + 1) for i, x in enumerate(top, 1))
    ideal = sorted(relevant.values(), reverse=True)[:k]
    idcg = sum(gain(v) / math.log2(i + 1) for i, v in enumerate(ideal, 1))
    return {"status": "PASS", "recall_at_k": hits / len(positives),
            "precision_at_k": hits / k, "mrr": 0 if first is None else 1 / first,
            "ndcg_at_k": dcg / idcg if idcg else 0}


def check_citations(retrieved: list[str], corpus: list[str], claims: list[dict]) -> list[str]:
    """Structural membership only; SEMANTIC_GROUNDING always NOT_MEASURED."""
    errors = []
    if not set(retrieved).issubset(corpus):
        errors.append("retrieved source outside corpus")
    for index, claim in enumerate(claims):
        citations = claim.get("citations", [])
        if not citations or not isinstance(citations, list):
            errors.append(f"claim {index}: unsupported claim")
        elif any(c not in retrieved or c not in corpus for c in citations):
            errors.append(f"claim {index}: fabricated citation")
    return errors


def check_prompt_regression(case: dict, observation: dict) -> list[str]:
    """Assert structured properties, not full natural-language equality."""
    errors = []
    for field in case.get("required_fields", []):
        if field not in observation:
            errors.append("missing field: " + field)
    for field in case.get("forbidden_fields", []):
        if field in observation:
            errors.append("forbidden field: " + field)
    for field, kind in case.get("types", {}).items():
        if field in observation and (kind not in TYPES or type(observation[field]) is not TYPES[kind]):
            errors.append("wrong type: " + field)
    for field, value in case.get("expected_values", {}).items():
        if observation.get(field) != value:
            errors.append("invariant mismatch: " + field)
    return errors


def check_tool_call(spec: dict, call: dict, grant: dict, seen: set[str]) -> list[str]:
    """Check authorization before any side effect. Does not execute calls."""
    errors = []
    ident = call.get("call_id")
    if not isinstance(ident, str) or not ident or ident in seen:
        errors.append("duplicate or invalid call ID")
    if call.get("tool_id") != spec.get("tool_id"):
        return errors + ["unknown tool"]
    operation = spec.get("operations", {}).get(call.get("operation"))
    if not isinstance(operation, dict):
        return errors + ["unknown operation"]
    arguments = call.get("arguments")
    if not isinstance(arguments, dict):
        return errors + ["invalid arguments"]
    fields = operation.get("args", {})
    if set(arguments) != set(fields):
        errors.append("missing or extra arguments")
    for name, typename in fields.items():
        if name in arguments and (typename not in TYPES or type(arguments[name]) is not TYPES[typename]):
            errors.append("incorrect argument type: " + name)
    if call.get("scope") != grant.get("scope"):
        errors.append("cross-scope operation")
    if grant.get("access") not in {"read-only", "write"}:
        errors.append("authorization denied")
    elif operation.get("effect") != "read" and grant.get("access") != "write":
        errors.append("write in read-only scope")
    if operation.get("effect") == "irreversible" and not call.get("approval"):
        errors.append("missing approval")
    if call.get("retry") and (operation.get("effect") != "read" and
                              (not operation.get("idempotent") or call.get("prior_outcome") == "unknown")):
        errors.append("unsafe retry or duplicate side effect")
    if call.get("retry") and call.get("prior_outcome") == "authorization_denied":
        errors.append("retry after authorization failure")
    if any(isinstance(v, str) and ("SYNTHETIC_SECRET_DO_NOT_USE" in v or "PRIVATE KEY" in v) for v in arguments.values()):
        errors.append("secret in arguments")
    if call.get("step", 0) < grant.get("minimum_step", 0):
        errors.append("incorrect call order")
    return errors


def validate_fixture(fixture: dict) -> list[str]:
    errors = validate_dataset(fixture.get("dataset"))
    dataset = fixture.get("dataset", {})
    if not isinstance(dataset, dict):
        return errors
    for record in fixture.get("evaluations", []):
        errors.extend(validate_evaluation(record, dataset))
    kind = fixture.get("kind")
    dataset_ids = {c.get("id") for c in dataset.get("cases", []) if isinstance(c, dict)}
    checks = fixture.get("checks", [])
    if not isinstance(checks, list) or {c.get("id") for c in checks if isinstance(c, dict)} != dataset_ids:
        errors.append("check/Case ID coverage mismatch")
    for case in checks:
        if kind == "feature":
            actual = check_prompt_regression(case["contract"], case["observation"])
        elif kind == "rag":
            actual = check_citations(case["retrieved"], case["corpus"], case["claims"])
            measured = retrieval_metrics(case["retrieved"], case["gold"], case["k"])
            if measured["status"] != case["expected_metrics_status"]:
                actual.append("wrong metric status")
            if ("minimum_recall" in case and measured["status"] == "PASS"
                    and measured["recall_at_k"] < case["minimum_recall"]):
                actual.append("retrieval below required recall")
        elif kind == "tool":
            actual = check_tool_call(fixture["tool_spec"], case["call"], case["grant"], set(case.get("seen", [])))
        else:
            return errors + ["unknown fixture kind"]
        expected = case["expected_verdict"]
        if expected not in ("PASS", "FAIL") or (not actual) != (expected == "PASS"):
            errors.append("oracle missed synthetic defect: " + case["id"])
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=ROOT / "fixtures" / "ai")
    args = parser.parse_args()
    if not args.fixtures.is_dir() or args.fixtures.is_symlink():
        print("FAIL: missing or unsafe offline fixture directory")
        return 2
    errors = []
    files = sorted(args.fixtures.glob("*.json"))
    if len(files) != 3:
        errors.append("expected exactly three synthetic examples")
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(args.fixtures.resolve()):
            errors.append("unsafe fixture")
            continue
        try:
            fixture = json.loads(path.read_text(encoding="utf-8"))
            errors.extend(f"{path.name}: {msg}" for msg in validate_fixture(fixture))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"{path.name}: {type(exc).__name__}")
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print(f"PASS: {len(files)} synthetic AI contracts; no model execution; effectiveness NOT_MEASURED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
