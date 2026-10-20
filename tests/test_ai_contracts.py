"""Issue #57 offline AI engineering contracts: deliberate mutation and safety checks."""
from __future__ import annotations
import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_ai_contracts import (
    check_citations, check_prompt_regression, check_tool_call, digest_cases,
    retrieval_metrics, validate_dataset, validate_evaluation, validate_fixture,
)
from install import skill_sources
from skill_manager import operate, read_state

F = {name: json.loads((ROOT / "fixtures/ai" / (name + ".json")).read_text(encoding="utf-8"))
     for name in ("feature", "rag", "tool")}


class AIContractsTests(unittest.TestCase):
    def test_all_three_synthetic_fixture_oracles(self):
        for name, example in F.items():
            with self.subTest(name=name):
                self.assertEqual([], validate_fixture(example))

    def test_sha256_stable_and_dataset_versioned(self):
        d = copy.deepcopy(F["feature"]["dataset"])
        self.assertEqual(d["sha256"], digest_cases(d["cases"]))
        d["cases"][0]["input"] += " tampered"
        self.assertIn("dataset SHA256 mismatch", validate_dataset(d))

    def test_duplicate_case_and_invalid_version(self):
        d = copy.deepcopy(F["feature"]["dataset"])
        d["cases"][1]["id"] = d["cases"][0]["id"]
        d["version"] = "new"
        errors = validate_dataset(d)
        self.assertTrue(any("duplicate Case ID" in x for x in errors))
        self.assertIn("invalid dataset version", errors)

    def test_independent_oracle_missing(self):
        d = copy.deepcopy(F["feature"]["dataset"])
        d["cases"][0]["oracle"] = {"type": "model_self_grade", "assertion": "I feel good"}
        self.assertTrue(any("independent oracle" in x for x in validate_dataset(d)))

    def test_offline_cannot_claim_real_execution(self):
        d = F["feature"]["dataset"]
        record = copy.deepcopy(F["feature"]["evaluations"][0])
        record["lifecycle"]["execution_completed"] = "PASS"
        self.assertTrue(any("offline PASS" in x for x in validate_evaluation(record, d)))
        record = copy.deepcopy(F["feature"]["evaluations"][0])
        record["lifecycle"]["acceptance_verified"] = "PASS"
        self.assertTrue(any("acceptance without execution" in x for x in validate_evaluation(record, d)))
        record = copy.deepcopy(F["feature"]["evaluations"][0])
        record["lifecycle"]["effectiveness_measured"] = "PASS"
        self.assertTrue(any("effectiveness without acceptance" in x for x in validate_evaluation(record, d)))

    def test_tokens_and_cost_not_invented(self):
        d = F["feature"]["dataset"]
        record = copy.deepcopy(F["feature"]["evaluations"][0])
        record["metrics"]["tokens"] = {"status": "PASS", "value": 400, "source": None}
        self.assertIn("invented tokens measurement", validate_evaluation(record, d))
        record = copy.deepcopy(F["feature"]["evaluations"][0])
        record["metrics"]["estimated_cost"] = 0.0
        self.assertIn("invented metric field", validate_evaluation(record, d))

    def test_prompt_schema_negative_oracles_detect_fail(self):
        sample = F["feature"]["checks"]
        self.assertEqual([], check_prompt_regression(sample[0]["contract"], sample[0]["observation"]))
        for item in sample[1:5]:
            self.assertTrue(check_prompt_regression(item["contract"], item["observation"]), item["id"])
        f = copy.deepcopy(F["feature"])
        f["checks"][1]["expected_verdict"] = "PASS"
        self.assertTrue(any("oracle missed synthetic defect" in x for x in validate_fixture(f)))

    def test_retrieval_math_and_zero_gold(self):
        m = retrieval_metrics(["doc_b", "doc_a"], {"doc_a": 3}, 2)
        self.assertEqual(0.5, m["precision_at_k"])
        self.assertEqual(1.0, m["recall_at_k"])
        self.assertEqual(0.5, m["mrr"])
        self.assertLess(m["ndcg_at_k"], 1)
        self.assertEqual("NOT_MEASURED", retrieval_metrics([], {}, 2)["status"])
        with self.assertRaises(ValueError):
            retrieval_metrics(["doc_a", "doc_a"], {"doc_a": 1}, 2)

    def test_citation_membership_not_semantics(self):
        self.assertEqual([], check_citations(["A"], ["A"], [{"citations": ["A"]}]))
        self.assertTrue(check_citations(["A"], ["A"], [{"citations": ["fake"]}]))
        self.assertTrue(check_citations([], ["A"], [{"citations": ["A"]}]))
        self.assertTrue(check_citations(["X"], ["A"], []))

    def test_tool_authorization_and_ambiguity(self):
        f = F["tool"]
        for item in f["checks"]:
            findings = check_tool_call(f["tool_spec"], item["call"], item["grant"], set(item["seen"]))
            self.assertEqual(not findings, item["expected_verdict"] == "PASS", item["id"])
        call = copy.deepcopy(f["checks"][1]["call"])
        call["retry"] = True
        call["prior_outcome"] = "unknown"
        self.assertTrue(any("unsafe retry" in x for x in check_tool_call(
            f["tool_spec"], call, f["checks"][1]["grant"], set())))

    def test_integrity_of_zero_spend_lock(self):
        source = (ROOT / "scripts/agent_eval_runner.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        assigns = [node.value.value for node in tree.body if isinstance(node, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "OWNER_REAL_AGENT_EXECUTION_LOCKED"
                           for t in node.targets) if isinstance(node.value, ast.Constant)]
        self.assertEqual([True], assigns)
        offline = ast.parse((ROOT / "scripts/validate_ai_contracts.py").read_text(encoding="utf-8"))
        modules = {n.module.split(".")[0] for n in ast.walk(offline) if isinstance(n, ast.ImportFrom) and n.module}
        modules.update(alias.name.split(".")[0] for n in ast.walk(offline) if isinstance(n, ast.Import) for alias in n.names)
        self.assertFalse(modules & {"requests", "urllib", "socket", "http", "subprocess", "openai", "anthropic"})

    def test_manifest_profile_and_install_preview(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(["ai-engineering-qa"], manifest["extension_packs"]["ai"]["skills"])
        self.assertEqual(ROOT / "extensions/ai/skills/ai-engineering-qa", skill_sources(manifest)["ai-engineering-qa"])
        profile = manifest["profiles"]["ai-engineering-qa"]
        self.assertIn("ai-engineering-qa", profile)
        self.assertNotIn("ai-engineering-qa", manifest["profiles"]["general"])
        self.assertFalse({"feature-delivery", "make-feature", "adaptive-delivery", "qa-all"} & set(profile))
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder)
            before = list(target.iterdir())
            preview = operate("install", target, names=["ai-engineering-qa"], layout="codex", apply=False)
            self.assertFalse(preview["applied"])
            self.assertEqual(before, list(target.iterdir()))
            applied = operate("install", target, names=["ai-engineering-qa"], layout="codex", apply=True)
            self.assertTrue(applied["applied"])
            self.assertIn("ai-engineering-qa", read_state(target, "codex")["skills"])


if __name__ == "__main__":
    unittest.main()
