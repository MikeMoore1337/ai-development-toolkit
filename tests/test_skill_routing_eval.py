"""Deterministic lexical-routing checks: no model calls or external dependencies."""
from __future__ import annotations

import json
import re
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

    def test_cyrillic_description_tokens(self):
        self.assertIn("естественные", routing.terms("Нужны естественные русские тексты"))

    def test_positive_and_negative_separation(self):
        report = routing.evaluate(self.catalog, self.cases, top_k=1)
        self.assertEqual(2, report["prompt_count"])
        self.assertEqual(0, report["failed"], report["observations"])
        self.assertEqual("NOT_MEASURED", report["actual_skill_activation"])
        self.assertEqual("NOT_MEASURED", report["model_effectiveness"])

    def test_ru_aliases_route_without_client_claims(self):
        catalog = {
            "contract-testing": "Contract compatibility validation.",
            "seo-audit": "Search engine optimization review.",
            "code-review": "Review source code regressions.",
        }
        cases = [{
            "id": "russian-api",
            "target": "contract-testing",
            "positive": ["Контрактные тесты совместимости схемы API."],
            "negative": ["SEO аудит сайта: индексация, метатеги."],
        }]
        aliases = {
            "contract-testing": ["контрактные тесты совместимости схемы api"],
            "seo-audit": ["seo аудит сайта индексация метатеги"],
        }
        report = routing.evaluate(catalog, cases, top_k=1, aliases=aliases)
        self.assertEqual(0, report["failed"], report["observations"])
        self.assertEqual(1, report["coverage"]["languages"]["ru"]["tested_target_count"])
        self.assertEqual(2, len(report["coverage"]["uncovered_targets"]))
        self.assertEqual("NOT_OBSERVED", report["client_skill_selection"])
        self.assertEqual("NOT_TESTED", report["client_effectiveness"])

    def test_aliases_unknown_skill_and_duplicates_blocked(self):
        (self.root / "aliases.json").write_text(json.dumps({
            "schema_version": 1, "aliases": {"invented": ["проверка схем"]}
        }), encoding="utf-8")
        with self.assertRaisesRegex(routing.RoutingInputError, "Unknown skill alias"):
            routing.read_aliases(self.root / "aliases.json", self.catalog)
        (self.root / "aliases.json").write_text(json.dumps({
            "schema_version": 1,
            "aliases": {"code-review": ["проверка кода", "проверка кода"]}
        }), encoding="utf-8")
        with self.assertRaisesRegex(routing.RoutingInputError, "duplicate alias"):
            routing.read_aliases(self.root / "aliases.json", self.catalog)

    def test_coverage_does_not_overstate_uncovered_skills(self):
        report = routing.evaluate(self.catalog, self.cases)
        self.assertEqual(3, report["coverage"]["catalog_total"])
        self.assertEqual(1, report["coverage"]["curated_targets"])
        self.assertEqual(["api-testing", "clear-voice"],
                         report["coverage"]["uncovered_targets"])
        self.assertEqual(0, report["coverage"]["languages"]["ru"]["tested_target_count"])
        self.assertEqual(1, report["coverage"]["languages"]["en"]["tested_target_count"])

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
        self.assertEqual(82, len(from_manifest))
        self.assertIn("feature-delivery", from_manifest)
        self.assertIn("make-feature", from_manifest)
        self.assertIn("performance-load-testing", from_manifest)

    def test_real_fixture_is_valid_and_read_only(self):
        catalog = routing.read_catalog(ROOT)
        cases = routing.load_cases(ROOT / "fixtures/skill_routing_cases.json", catalog)
        aliases = routing.read_aliases(ROOT / "fixtures/skill_routing_aliases.json", catalog)
        report = routing.evaluate(catalog, cases, aliases=aliases)
        self.assertGreaterEqual(len(cases), 12)
        self.assertEqual(82, report["coverage"]["catalog_total"])
        self.assertEqual(8, report["coverage"]["languages"]["ru"]["tested_target_count"])
        self.assertGreater(len(report["coverage"]["uncovered_targets"]), 0)
        self.assertTrue({"qa-failure-triage-versus-generic-tests",
                         "qa-test-oracle-review-versus-code-review"} <=
                        {case["id"] for case in cases})
        self.assertEqual(len(cases) * 4, report["prompt_count"])
        self.assertEqual("offline_source_diagnostic", report["classification"])

    def test_bilingual_qa_behavior_check_ids(self):
        """Manual cases are parallel in EN/RU; do not mistake them for executed trials."""
        expected_routes = {f"QA-R{i:02d}" for i in range(1, 15)}
        expected_negative = {f"QA-N{i:02d}" for i in range(1, 8)}
        ids = []
        for path in ("docs/SKILL_ROUTING_EVALS.md",
                     "docs/ru/SKILL_ROUTING_EVALS.md"):
            content = (ROOT / path).read_text(encoding="utf-8")
            route_ids = re.findall(r"^\| (QA-R\d{2}) \|", content, re.MULTILINE)
            negative_ids = re.findall(r"^\| (QA-N\d{2}) \|", content, re.MULTILINE)
            self.assertEqual(expected_routes, set(route_ids), path)
            self.assertEqual(expected_negative, set(negative_ids), path)
            self.assertEqual(len(route_ids), len(expected_routes), path)
            self.assertEqual(len(negative_ids), len(expected_negative), path)
            ids.append((route_ids, negative_ids))
        self.assertEqual(ids[0], ids[1])

    def test_qa_advanced_methods_have_bilingual_guidance(self):
        for path in ("docs/CURATED_SKILL_PACKS.md",
                     "docs/ru/CURATED_SKILL_PACKS.md"):
            content = (ROOT / path).read_text(encoding="utf-8")
            for technique in ("Property-based", "Metamorphic",
                              "Model-based", "Mutation"):
                self.assertIn(technique, content, path)
            self.assertIn("ROLLBACK", content, path)
            self.assertIn("test-management", content, path)

    def test_cli_strict_in_synced_checkout(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "skill_routing_eval.py"), "--strict"],
            check=False, capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(0, proc.returncode, proc.stderr + proc.stdout[-4000:])


if __name__ == "__main__":
    unittest.main()
