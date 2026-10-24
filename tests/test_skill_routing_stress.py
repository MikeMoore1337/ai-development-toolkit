"""Issue #296: offline, untuned RU/EN lexical routing stress diagnostics."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import skill_routing_eval as router
import skill_routing_stress as stress

PATH = ROOT / "fixtures" / "skill_routing_stress_20261024.json"


class FrozenRoutingStressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = router.read_catalog(ROOT)
        cls.fixture = stress.load_stress(PATH, cls.catalog)
        cls.aliases = router.read_aliases(ROOT / "fixtures/skill_routing_aliases.json", cls.catalog)
        cls.manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

    def test_dataset_frozen_after_original_v555_baseline(self):
        rows = self.fixture["cases"]
        self.assertEqual(48, len(rows))
        self.assertEqual(24, sum(x["id"].startswith("s296-ru-") for x in rows))
        self.assertEqual(24, sum(x["id"].startswith("s296-en-") for x in rows))
        self.assertEqual({
            "single": 12, "compound": 12, "negative": 12,
            "ambiguous": 6, "missing_skill": 6,
        }, {kind: sum(row["kind"] == kind for row in rows)
            for kind in stress.KINDS})
        self.assertEqual("c1bfe52d24fb6691a0ec7ed4f28dcd7bcd76225f",
                         self.fixture["baseline_sha"])
        self.assertEqual("AI_ASSISTANT", self.fixture["label_author"])
        self.assertEqual("NOT_VERIFIED", self.fixture["reviewer_independence"])
        self.assertEqual("DIAGNOSTIC_NON_GATING", self.fixture["scoring"])

    def test_report_separates_primary_auxiliary_abstention_and_forbidden(self):
        report = stress.evaluate_stress(self.catalog, self.aliases,
                                        self.manifest, self.fixture)
        self.assertEqual("offline_lexical_stress_diagnostic", report["classification"])
        self.assertEqual(48, report["count"])
        self.assertEqual("NOT_MEASURED", report["calibrated_semantic_accuracy"])
        self.assertEqual("NOT_OBSERVED", report["client_discovery"])
        self.assertEqual("NOT_TESTED", report["client_effectiveness"])
        self.assertFalse(report["ranker_modified_for_cases"])
        self.assertEqual(24, report["by_language"]["ru"]["cases"])
        self.assertEqual(24, report["by_language"]["en"]["cases"])
        self.assertEqual(48, sum(x["cases"] for x in report["by_kind"].values()))
        for row in report["observations"]:
            self.assertEqual(48, report["count"])
            self.assertEqual(set(), set(row["primary"]) & set(row["auxiliary"]))
            self.assertEqual(sorted(set(row["forbidden"]) &
                                    (set(row["primary"]) | set(row["auxiliary"]))),
                             row["forbidden_selected"])
        print("STRESS_DIAGNOSTIC_SUMMARY=" +
              json.dumps({"total": report["summary"],
                          "by_kind": report["by_kind"],
                          "by_language": report["by_language"]},
                         sort_keys=True), flush=True)

    def test_new_fixture_is_not_an_existing_benchmark_copy(self):
        current = {row["query"] for row in self.fixture["cases"]}
        for path in (
            "fixtures/skill_routing_holdout.json",
            "fixtures/skill_routing_exploratory_20261023.json",
            "fixtures/skill_routing_release_probes_20261023.json",
            "fixtures/skill_routing_untuned_20261024.json",
        ):
            old = json.loads((ROOT / path).read_text(encoding="utf-8"))
            with self.subTest(path=path):
                self.assertFalse(current & {r["query"] for r in old["cases"]})

    def test_unknown_label_and_falsified_independence_are_rejected(self):
        for mutation in (
            ("reviewer_independence", "INDEPENDENT"),
            ("label_author", "HUMAN"),
            ("cases", [dict(self.fixture["cases"][0], expected_primary=["invented"])]),
        ):
            with self.subTest(field=mutation[0]), tempfile.TemporaryDirectory() as tmp:
                altered = dict(self.fixture)
                altered[mutation[0]] = mutation[1]
                path = Path(tmp) / "bad.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(router.RoutingInputError):
                    stress.load_stress(path, self.catalog)

    def test_forbidden_exact_named_skill_never_reappears_as_auxiliary(self):
        catalog = {
            "seo-audit": "Analyze SEO crawlability search indexing and metadata.",
            "api-testing": "Test HTTP API status codes and error responses.",
        }
        result = router.recommend(
            "Skip seo-audit; Test HTTP API response status codes.",
            catalog, {}, {"profiles": {}, "core_roles": [], "extension_packs": {}},
            top_k=2,
        )
        selected = (result["routing_decision"]["primary_skills"] +
                    result["routing_decision"]["auxiliary_skills"])
        self.assertNotIn("seo-audit", selected)
        self.assertIn("api-testing", selected)
        self.assertEqual("NOT_OBSERVED", result["client_skill_selection"])

    def test_cli_summary_does_not_claim_accuracy_or_execution(self):
        output = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "skill_routing_stress.py"),
             "--summary-only"],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(0, output.returncode, output.stderr)
        report = json.loads(output.stdout)
        self.assertEqual(48, report["count"])
        self.assertNotIn("observations", report)
        self.assertEqual("DIAGNOSTIC_NON_GATING", report["scoring"])


if __name__ == "__main__":
    unittest.main()
