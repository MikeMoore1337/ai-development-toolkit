"""Offline evaluator tests. Synthetic examples are not real agent performance data."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("skill_eval", ROOT / "scripts" / "skill_eval.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture() -> dict:
    runs = []
    for trial, task in ((1, "api"), (1, "docs")):
        for variant in ("baseline", "candidate"):
            runs.append({
                "task_id": task, "trial": trial, "variant": variant,
                "accepted": variant == "candidate", "regressions": 0,
                "unsafe_actions": 0, "tokens": 100,
                "duration_seconds": 20.5,
                "evidence": [f"{task}-{variant}.txt"],
            })
    return {
        "schema_version": 1, "dataset": "synthetic-only",
        "repository_sha": "0123456789abcdef", "model": "hypothetical-model",
        "runs": runs,
    }


class SkillEvalsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = fixture()
        for item in self.data["runs"]:
            (self.root / item["evidence"][0]).write_text("synthetic evidence", encoding="utf-8")

    def test_paired_score_is_reproducible_and_not_certified(self):
        result = module.evaluate(self.data, self.root)
        self.assertEqual(2, result["pairs"])
        self.assertEqual(100.0, result["acceptance_delta_percentage_points"])
        self.assertEqual("exploratory", result["classification"])
        self.assertTrue(result["independent_review_required"])

    def test_missing_pair_is_rejected(self):
        self.data["runs"].pop()
        with self.assertRaisesRegex(module.EvalInputError, "Unpaired"):
            module.evaluate(self.data, self.root)

    def test_duplicate_variant_is_rejected(self):
        self.data["runs"].append(self.data["runs"][0].copy())
        with self.assertRaisesRegex(module.EvalInputError, "duplicate"):
            module.evaluate(self.data, self.root)

    def test_unsafe_or_missing_evidence_is_rejected(self):
        self.data["runs"][0]["evidence"] = ["../outside.txt"]
        with self.assertRaisesRegex(module.EvalInputError, "unsafe"):
            module.evaluate(self.data, self.root)
        self.data["runs"][0]["evidence"] = ["not-found.txt"]
        with self.assertRaisesRegex(module.EvalInputError, "missing"):
            module.evaluate(self.data, self.root)

    def test_invalid_measurements_are_rejected(self):
        self.data["runs"][0]["accepted"] = 1
        with self.assertRaisesRegex(module.EvalInputError, "boolean"):
            module.evaluate(self.data, self.root)
        self.data["runs"][0]["accepted"] = True
        self.data["runs"][0]["tokens"] = True
        with self.assertRaisesRegex(module.EvalInputError, "non-negative"):
            module.evaluate(self.data, self.root)

    def test_missing_safety_metrics_are_rejected(self):
        self.data["runs"][0].pop("unsafe_actions")
        with self.assertRaisesRegex(module.EvalInputError, "missing required unsafe_actions"):
            module.evaluate(self.data, self.root)

    def test_optional_telemetry_must_not_be_invented(self):
        self.data["runs"][0].pop("tokens")
        summary = module.evaluate(self.data, self.root)
        self.assertIsNone(summary["baseline"]["mean_tokens"])

    def test_cli_json_output(self):
        source = self.root / "runs.json"
        source.write_text(json.dumps(self.data), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "skill_eval.py"), str(source)],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual(2, json.loads(proc.stdout)["pairs"])

    def test_missing_pin_is_rejected(self):
        del self.data["repository_sha"]
        with self.assertRaisesRegex(module.EvalInputError, "repository_sha"):
            module.evaluate(self.data, self.root)


if __name__ == "__main__":
    unittest.main()
