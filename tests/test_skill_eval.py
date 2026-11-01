"""Offline evaluator tests. Synthetic examples are not real agent performance data."""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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

    def _make_native_receipts(self):
        node = shutil.which("node")
        if not node:
            self.skipTest("Node runtime missing; native receipt E2E NOT_VERIFIED")
        script = """
const fs = require('node:fs');
const path = require('node:path');
const h = require(process.argv[1]);
const root = process.argv[2];
const file = process.argv[3];
const key = process.argv[4];
const dir = path.join(root, 'capsules', key);
const receiptPath = path.join(root, 'receipts', key + '.json');
const clock = () => new Date('2026-10-28T00:00:00.000Z');
const c = h.capsule.Capsule.create(dir, {
  run_id:'run-' + key, capsule_id:'cap-' + key,
  harness_version:'toolkit/1', task_family:'paired', clock
});
c.append('attempt', 'recorded', {task_id:key, status:'submitted'});
const receipt = h.receipt.buildReceipt(dir, {artifact_path:file, clock});
h.receipt.writeReceipt(receipt, receiptPath);
"""
        lib = ROOT / "third_party/ecc-v2.2.3/eval-harness/scripts/lib/eval-harness"
        for rec in self.data["runs"]:
            key = f"{rec['task_id']}-{rec['variant']}"
            file = str(self.root / rec["evidence"][0])
            proc = subprocess.run(
                [node, "-e", script, str(lib), str(self.root), file, key],
                cwd=ROOT, capture_output=True, text=True, encoding="utf-8",
                timeout=15, check=False,
            )
            self.assertEqual(0, proc.returncode, proc.stderr[-700:])
            rec["native_receipt"] = {
                "receipt": f"receipts/{key}.json",
                "capsule_dir": f"capsules/{key}",
                "artifact": rec["evidence"][0],
            }

    def test_native_receipts_require_explicit_opt_in(self):
        self.data["runs"][0]["native_receipt"] = {
            "receipt": "some.json", "capsule_dir": "some", "artifact": "a.txt",
        }
        with self.assertRaisesRegex(module.EvalInputError, "--verify-native-receipts"):
            module.evaluate(self.data, self.root)

    def test_native_receipts_integrate_with_real_offline_verifier(self):
        self._make_native_receipts()
        with mock.patch.dict(os.environ, {"NODE_OPTIONS": "--require /definitely-not-installed"}):
            out = module.evaluate(self.data, self.root, verify_native_receipts=True)
        self.assertEqual(4, out["native_receipts_verified"])
        self.assertEqual("OFFLINE_VERIFIED_NOT_OUTCOME", out["native_evidence_integrity"])
        self.assertTrue(out["independent_review_required"])
        self.assertEqual("exploratory", out["classification"])
        self.assertIn("self-reported", out["note"])
        file = self.root / self.data["runs"][0]["evidence"][0]
        file.write_text("changed evidence after receipt", encoding="utf-8")
        with self.assertRaisesRegex(module.EvalInputError, "integrity check failed"):
            module.evaluate(self.data, self.root, verify_native_receipts=True)

    def test_native_receipt_cli_requires_complete_binding(self):
        self._make_native_receipts()
        source = self.root / "runs.json"
        source.write_text(json.dumps(self.data), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/skill_eval.py"),
             str(source), "--verify-native-receipts"],
            capture_output=True, text=True, encoding="utf-8", timeout=90,
            check=False,
        )
        self.assertEqual(0, proc.returncode, proc.stderr[-1000:])
        self.assertEqual(4, json.loads(proc.stdout)["native_receipts_verified"])
        self.data["runs"][0]["native_receipt"].pop("artifact")
        with self.assertRaisesRegex(module.EvalInputError, "binding required"):
            module.evaluate(self.data, self.root, verify_native_receipts=True)

    def test_native_receipt_escape_and_missing_runtime_fail_closed(self):
        self._make_native_receipts()
        for value in ("../../outside.json", "C:/outside.json", "capsules\\\\bad.json"):
            rec = self.data["runs"][0]["native_receipt"]
            original = rec["receipt"]
            rec["receipt"] = value
            with self.assertRaisesRegex(module.EvalInputError, "unsafe native receipt path"):
                module.evaluate(self.data, self.root, verify_native_receipts=True)
            rec["receipt"] = original
        with mock.patch.object(module.shutil, "which", return_value=None):
            with self.assertRaisesRegex(module.EvalInputError, "Node.js required"):
                module.evaluate(self.data, self.root, verify_native_receipts=True)

    def _three_trial_fixture(self):
        """Synthetic: same pooled 6/9 acceptance but different repeatability."""
        baseline = {"a": (True, True, True), "b": (True, True, True),
                    "c": (False, False, False)}
        candidate = {name: (True, True, False) for name in baseline}
        data = {"schema_version": 1, "dataset": "offline-synthetic-only",
                "model": "no-model", "repository_sha": "test-revision", "runs": []}
        for task in baseline:
            for trial in (1, 2, 3):
                for variant, outcomes in (("baseline", baseline), ("candidate", candidate)):
                    path = f"trial-{task}-{trial}-{variant}.txt"
                    (self.root / path).write_text("offline fixture", encoding="utf-8")
                    data["runs"].append({
                        "task_id": task, "trial": trial, "variant": variant,
                        "accepted": outcomes[task][trial - 1], "regressions": 0,
                        "unsafe_actions": 0, "tokens": None,
                        "duration_seconds": None, "evidence": [path],
                    })
        return data

    def test_observed_repeatability_finds_stability_loss_hidden_by_aggregate(self):
        data = self._three_trial_fixture()
        plain = module.evaluate(data, self.root)
        self.assertEqual(0.6667, plain["baseline"]["acceptance_rate"])
        self.assertEqual(plain["baseline"]["acceptance_rate"],
                         plain["candidate"]["acceptance_rate"])
        self.assertNotIn("observed_repeatability", plain)
        output = module.evaluate(data, self.root, observed_repeatability=True)
        rep = output["observed_repeatability"]
        self.assertEqual(0.6667, rep["observed_pass_at_1"]["baseline"])
        self.assertEqual(1.0, rep["observed_pass_at_1"]["candidate"])
        self.assertEqual(0.6667, rep["observed_pass_at_3"]["baseline"])
        self.assertEqual(1.0, rep["observed_pass_at_3"]["candidate"])
        self.assertEqual(0.6667, rep["observed_pass_all_3"]["baseline"])
        self.assertEqual(0.0, rep["observed_pass_all_3"]["candidate"])
        self.assertEqual(-66.67, rep["observed_pass_all_3"]["delta_percentage_points"])
        self.assertEqual("OFFLINE_RECORDED_NOT_MODEL_EFFICACY", rep["scope"])
        self.assertEqual("exploratory", output["classification"])
        self.assertTrue(output["independent_review_required"])
        data["runs"].reverse()
        self.assertEqual(rep, module.evaluate(
            data, self.root, observed_repeatability=True)["observed_repeatability"])

    def test_observed_repeatability_rejects_missing_trials_and_risky_successes(self):
        data = self._three_trial_fixture()
        short = [x for x in data["runs"]
                 if not (x["task_id"] == "c" and x["trial"] == 3)]
        rep = module.evaluate({**data, "runs": short}, self.root,
                              observed_repeatability=True)["observed_repeatability"]
        self.assertEqual("RECORDED_VERDICTS_ONLY", rep["observed_pass_at_1"]["status"])
        self.assertEqual("NOT_MEASURED_INCOMPLETE_TRIALS", rep["observed_pass_at_3"]["status"])
        self.assertIsNone(rep["observed_pass_all_3"]["candidate"])
        self.assertEqual(2, rep["observed_pass_at_3"]["eligible_tasks"])
        risky = next(x for x in data["runs"] if x["task_id"] == "a"
                     and x["variant"] == "candidate" and x["trial"] == 1)
        risky["unsafe_actions"] = 1
        out = module.evaluate(data, self.root, observed_repeatability=True)
        self.assertEqual(0.6667, out["observed_repeatability"]
                         ["observed_pass_at_1"]["candidate"])
        self.assertEqual(1, out["candidate"]["unsafe_actions"])
        self.assertEqual(1.0, out["observed_repeatability"]
                         ["observed_pass_at_3"]["candidate"])

    def test_observed_repeatability_cli_and_fail_closed_evidence(self):
        data = self._three_trial_fixture()
        source = self.root / "paired.json"
        source.write_text(json.dumps(data), encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "skill_eval.py"),
             str(source), "--observed-repeatability"],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
            check=False)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual(0.0, json.loads(proc.stdout)["observed_repeatability"]
                         ["observed_pass_all_3"]["candidate"])
        # A missing first numbered trial cannot be assumed a failure or success.
        data["runs"] = [x for x in data["runs"]
                        if not (x["task_id"] == "c" and x["trial"] == 1)]
        rep = module.evaluate(data, self.root, observed_repeatability=True)
        self.assertIsNone(rep["observed_repeatability"]["observed_pass_at_1"]["baseline"])
        data["runs"][0]["evidence"] = ["does-not-exist.txt"]
        with self.assertRaisesRegex(module.EvalInputError, "missing"):
            module.evaluate(data, self.root, observed_repeatability=True)

    def test_missing_pin_is_rejected(self):
        del self.data["repository_sha"]
        with self.assertRaisesRegex(module.EvalInputError, "repository_sha"):
            module.evaluate(self.data, self.root)


if __name__ == "__main__":
    unittest.main()
