"""Independent #432 static-security measurements. Synthetic data, no dangerous execution.

The frozen corpus was committed separately before this evaluator. The holdout
cohort is run explicitly once after candidate remediation; it is never tuned on.
Run baseline: python -m unittest tests.test_native_security_independent_432 -v
Run sealed holdout: python tests/test_native_security_independent_432.py --cohort holdout
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import os
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cisco_mcp_gate as mcp_gate  # noqa: E402
import external_skill_gate as skill_gate  # noqa: E402

CORPUS = ROOT / "fixtures/native_security_independent_432.json"
CORPUS_SHA256 = "f629f87c955c5df0dc9c6e1b1f62294884ebd0779798dd8debf87c4957536f5b"
BASE_SHA = "cc65540cd9c4cf9b6c5daf29dd18b4639ecf0db8"


def load_cases() -> tuple[list[dict], str]:
    if CORPUS.is_symlink() or not CORPUS.is_file():
        raise ValueError("Missing or linked frozen corpus")
    raw = CORPUS.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != CORPUS_SHA256:
        raise ValueError("Frozen independent corpus SHA256 mismatch")
    obj = json.loads(raw.decode("utf-8"))
    if (not isinstance(obj, dict) or obj.get("schema_version") != 1
            or obj.get("baseline_source_sha") != BASE_SHA
            or obj.get("origin") != "INDEPENDENT_AUTHOR_SYNTHETIC_2026_11_05"
            or obj.get("not_real_world") is not True):
        raise ValueError("Invalid corpus provenance")
    cases = obj.get("cases")
    if not isinstance(cases, list) or len(cases) != 60:
        raise ValueError("Unexpected corpus size")
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case ID")
    if any(c["surface"] not in {"mcp_description", "host_config", "skill_candidate"}
           or c["cohort"] not in {"baseline", "holdout"} or type(c["attack"]) is not bool
           for c in cases):
        raise ValueError("Invalid independent case")
    return cases, digest


def scan_case(case: dict) -> tuple[bool, list[str]]:
    """Return advisory finding present, rule IDs. No command, hook or server executes."""
    with tempfile.TemporaryDirectory(prefix="adt432-isolated-") as temp_dir:
        root = Path(temp_dir)
        surface = case["surface"]
        if surface == "mcp_description":
            payload = {"tools": [{
                "name": "toolkit_synthetic_probe",
                "description": case["description"],
                "inputSchema": {"type": "object", "properties": {}},
            }]}
            report = mcp_gate.scan_native_descriptions(data=payload)
            if report["status"] not in {"PASS", "REVIEW_REQUIRED", "BLOCKED"}:
                raise AssertionError("Unclassified MCP result")
            if report.get("reason") == "INVALID_OR_INCOMPLETE_SNAPSHOT":
                raise AssertionError("Invalid independent MCP fixture")
            return report["status"] != "PASS", [r["rule"] for r in report["findings"]]
        if surface == "host_config":
            path = root / case["path"]
            if case["path"] not in skill_gate.HOST_FILES:
                raise AssertionError("Unsafe host fixture path")
            path.parent.mkdir(parents=True, exist_ok=True)
            body = case.get("toml")
            if body is None:
                body = json.dumps(case["config"], ensure_ascii=False, sort_keys=True)
            path.write_text(body, encoding="utf-8")
            report = skill_gate.review_host_config(root)
            if report["decision"] not in {"PASS", "REVIEW_REQUIRED", "BLOCKED"}:
                raise AssertionError("Unclassified host result")
            return report["decision"] != "PASS", [r["rule"] for r in report["findings"]]
        if surface == "skill_candidate":
            candidate = root / "candidate"
            candidate.mkdir()
            skill_file = candidate / "SKILL.md"
            skill_file.write_bytes(case["skill"].encode("utf-8"))
            if case.get("symlink_file"):
                external = root / "synthetic-linked-file.md"
                external.write_bytes(case["skill"].encode("utf-8"))
                skill_file.unlink()
                try:
                    skill_file.symlink_to(external)
                except (OSError, NotImplementedError):
                    raise unittest.SkipTest("symlink creation unavailable on this CI OS")
            digest = hashlib.sha256(case["skill"].encode("utf-8")).hexdigest()
            files = {"SKILL.md": "0" * 64 if case.get("tamper_sha") else digest}
            if case.get("manifest_traversal"):
                files["../synthetic-escape"] = "0" * 64
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps({
                "schema_version": 1, "candidate_id": "sample-skill",
                "source_url": "https://github.com/example/synthetic",
                "source_revision": "a" * 40, "license": "MIT",
                "files": files,
            }), encoding="utf-8")
            report = skill_gate.review(candidate, manifest)
            if report["decision"] not in {"ALLOW_FOR_REVIEW", "NEEDS_MANUAL_REVIEW", "REJECT"}:
                raise AssertionError("Unclassified skill verdict")
            if report["adoption_dossier"]["publication_gate"] != (
                "BLOCKED_PENDING_INDEPENDENT_PROVENANCE_AND_OWNER_APPROVAL"
            ):
                raise AssertionError("Unsafe adoption authorization")
            return report["decision"] != "ALLOW_FOR_REVIEW", [
                r["code"] for r in report["issues"]
            ]
        raise AssertionError("Unknown independent fixture surface")


def measure(cohort: str) -> dict:
    if cohort not in {"baseline", "holdout"}:
        raise ValueError("Explicit cohort required")
    cases, digest = load_cases()
    tally = defaultdict(lambda: {"tp": 0, "fp": 0, "tn": 0, "fn": 0})
    all_counts = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    errors = {"fp": [], "fn": []}
    skipped = []
    for case in cases:
        if case["cohort"] != cohort:
            continue
        try:
            detected, rules = scan_case(case)
        except unittest.SkipTest:
            skipped.append(case["id"])
            continue
        event = ("tp" if detected else "fn") if case["attack"] else (
            "fp" if detected else "tn"
        )
        all_counts[event] += 1
        tally[case["category"]][event] += 1
        if event in errors:
            errors[event].append({"id": case["id"], "category": case["category"], "rules": rules})
    tp, fp, tn, fn = (all_counts[name] for name in ("tp", "fp", "tn", "fn"))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision and recall else 0.0
    return {
        "baseline_sha": BASE_SHA,
        "corpus_sha256": digest,
        "cohort": cohort,
        "counts": all_counts,
        "precision": round(precision, 6) if precision is not None else None,
        "recall": round(recall, 6) if recall is not None else None,
        "f1": round(f1, 6),
        "fpr": round(fp / (fp + tn), 6) if fp + tn else None,
        "fnr": round(fn / (fn + tp), 6) if fn + tp else None,
        "per_category": dict(sorted(tally.items())),
        "errors": errors,
        "skipped": skipped,
        "safety": "SYNTHETIC_STATIC_ADVISORY_ONLY",
        "host_enforcement": "NOT_VERIFIED",
        "client_e2e": "NOT_RUN",
        "representative_attack_accuracy": "NOT_MEASURED",
    }


class IndependentSecurity432Tests(unittest.TestCase):
    def test_frozen_corpus_design(self) -> None:
        cases, digest = load_cases()
        self.assertEqual(digest, CORPUS_SHA256)
        self.assertEqual(sum(c["attack"] for c in cases), 30)
        self.assertEqual(sum(not c["attack"] for c in cases), 30)
        self.assertEqual(sum(c["cohort"] == "baseline" for c in cases), 40)
        self.assertEqual(sum(c["cohort"] == "holdout" for c in cases), 20)
        self.assertEqual(len({c["category"] for c in cases}) >= 10, True)

    def test_independent_baseline_diagnostic_not_a_release_gate(self) -> None:
        report = measure("baseline")
        self.assertEqual(sum(report["counts"].values()) + len(report["skipped"]), 40)
        self.assertEqual(report["host_enforcement"], "NOT_VERIFIED")
        print("INDEPENDENT_432_BASELINE=" + json.dumps(report, sort_keys=True), flush=True)

    def test_clean_skill_fixture_uses_identical_utf8_bytes_on_all_platforms(self) -> None:
        # Ensures CRLF text-mode conversion cannot create fake checksum failures.
        cases, _ = load_cases()
        benign = next(case for case in cases if case["id"] == "N53")
        detected, rules = scan_case(benign)
        self.assertFalse(detected, rules)

    def test_host_sarif_source_rules_unique_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory(prefix="adt432-redacted-") as directory:
            root = Path(directory)
            (root / ".mcp.json").write_text(json.dumps({
                "mcpServers": {"synthetic": {
                    "command": "python", "args": ["-m", "tool.server"],
                    "env": {"API_KEY": "SYNTHETIC_SENTINEL_NEVER_LOG_THIS"}
                }}
            }), encoding="utf-8")
            report = skill_gate.review_host_config(root)
            self.assertEqual(report["decision"], "BLOCKED")
            sarif = skill_gate.host_report_sarif(report)
            self.assertEqual(sarif["version"], "2.1.0")
            runs = sarif["runs"]
            self.assertEqual(len(runs), 1)
            entries = runs[0]["results"]
            self.assertEqual(len(entries), len(report["findings"]))
            ids = {rule["id"] for rule in runs[0]["tool"]["driver"]["rules"]}
            self.assertEqual(ids, {finding["rule"] for finding in report["findings"]})
            keys = set()
            for entry in entries:
                key = (entry["ruleId"], entry["locations"][0]["physicalLocation"]["artifactLocation"]["uri"])
                self.assertNotIn(key, keys)
                keys.add(key)
                self.assertIn(entry["ruleId"], ids)
                self.assertIn(key[1], skill_gate.HOST_FILES)
            serialized = json.dumps({"sarif": sarif, "report": report}, ensure_ascii=False)
            self.assertNotIn("SYNTHETIC_SENTINEL_NEVER_LOG_THIS", serialized)
            self.assertNotIn(str(root), serialized)
            self.assertEqual(report["evidence"]["runtime_enforcement"], "NOT_VERIFIED")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=("baseline", "holdout"), required=True)
    opts = parser.parse_args()
    print(json.dumps(measure(opts.cohort), indent=2, sort_keys=True))
