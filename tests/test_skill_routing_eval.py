"""Deterministic lexical-routing checks: no model calls or external dependencies."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import skill_routing_eval as routing


class SkillRoutingTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.catalog = {
            "code-review": "Review proposed code changes for correctness and regressions.",
            "api-testing": "Test API HTTP behavior, responses and failure cases.",
            "clear-voice": "Rewrite writing and editorial copy in a natural voice.",
        }
        self.cases = [{
            "id": "review",
            "target": "code-review",
            "positive": ["Review a code diff for correctness and regressions."],
            "negative": ["Rewrite editorial copy with a natural voice."],
        }]
        self.path = self.root / "cases.json"
        self.save()

    def save(self):
        self.path.write_text(json.dumps({"schema_version": 1, "cases": self.cases}),
                             encoding="utf-8")

    def test_positive_and_negative_separation(self):
        report = routing.evaluate(self.catalog, self.cases, top_k=1)
        self.assertEqual(2, report["prompt_count"])
        self.assertEqual(0, report["failed"], report["observations"])
        self.assertEqual("NOT_MEASURED", report["actual_skill_activation"])
        self.assertEqual("NOT_MEASURED", report["model_effectiveness"])

    def test_deterministic_results(self):
        first = routing.evaluate(self.catalog, self.cases)
        self.assertEqual(first, routing.evaluate(self.catalog, self.cases))

    def test_wrong_routing_is_detected(self):
        self.cases[0]["positive"] = ["Rewrite editorial copy in a natural voice."]
        report = routing.evaluate(self.catalog, self.cases, top_k=1)
        self.assertEqual(1, report["failed"])
        self.assertEqual(False, report["observations"][0]["pass"])

    def test_unknown_skill_fails_closed(self):
        self.cases[0]["target"] = "invented-skill"
        self.save()
        with self.assertRaisesRegex(routing.RoutingInputError, "Unlisted skill"):
            routing.load_cases(self.path, self.catalog)

    def test_duplicate_case_id_fails_closed(self):
        self.cases.append(self.cases[0].copy())
        self.save()
        with self.assertRaisesRegex(routing.RoutingInputError, "duplicated"):
            routing.load_cases(self.path, self.catalog)

    def test_invalid_prompt_rejected(self):
        self.cases[0]["negative"] = [""]
        self.save()
        with self.assertRaisesRegex(routing.RoutingInputError, "Invalid prompt"):
            routing.load_cases(self.path, self.catalog)

    def test_catalog_is_manifest_driven(self):
        from_manifest = routing.read_catalog(ROOT)
        self.assertEqual(65, len(from_manifest))
        self.assertIn("feature-delivery", from_manifest)
        self.assertIn("make-feature", from_manifest)

    def test_real_fixture_is_valid_and_read_only(self):
        catalog = routing.read_catalog(ROOT)
        cases = routing.load_cases(ROOT / "fixtures/skill_routing_cases.json", catalog)
        report = routing.evaluate(catalog, cases)
        self.assertEqual(18, report["prompt_count"] * 0 + len(cases) * 2)
        self.assertEqual(len(cases) * 4, report["prompt_count"])
        self.assertEqual("offline_source_diagnostic", report["classification"])

    def test_cli_strict_in_synced_checkout(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "skill_routing_eval.py"), "--strict"],
            check=False, capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(0, proc.returncode, proc.stderr + proc.stdout[-4000:])


if __name__ == "__main__":
    unittest.main()
