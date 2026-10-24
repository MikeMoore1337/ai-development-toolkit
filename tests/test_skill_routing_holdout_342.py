"""Issue #342: second synthetic holdout; no trained judge or real AI client."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import skill_routing_eval as router
import skill_routing_stress as stress

FIXTURE = ROOT / "fixtures" / "skill_routing_holdout_342.json"


class SecondRoutingHoldoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = router.read_catalog(ROOT)
        cls.fixture = stress.load_stress(FIXTURE, cls.catalog)
        cls.aliases = router.read_aliases(ROOT / "fixtures/skill_routing_aliases.json",
                                          cls.catalog)
        cls.manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

    def test_second_holdout_frozen_and_provenance_not_falsified(self):
        rows = self.fixture["cases"]
        self.assertEqual(24, len(rows))
        self.assertEqual(12, sum(x["id"].startswith("s342-ru-") for x in rows))
        self.assertEqual(12, sum(x["id"].startswith("s342-en-") for x in rows))
        self.assertEqual({
            "single": 8, "compound": 4, "negative": 8,
            "ambiguous": 2, "missing_skill": 2,
        }, {kind: sum(x["kind"] == kind for x in rows) for kind in stress.KINDS})
        self.assertEqual("AI_ASSISTANT", self.fixture["label_author"])
        self.assertEqual("NOT_VERIFIED", self.fixture["reviewer_independence"])
        self.assertEqual("DIAGNOSTIC_NON_GATING", self.fixture["scoring"])
        self.assertEqual("71a5faaea542a4214b8fb9e0db0ae6909947a3b8",
                         self.fixture["baseline_sha"])
        self.assertTrue(all(x["id"].startswith("s342-") for x in rows))

    def test_no_exact_query_reuse_from_earlier_diagnostics(self):
        current = {r["query"] for r in self.fixture["cases"]}
        for filename in (
            "fixtures/skill_routing_holdout.json",
            "fixtures/skill_routing_exploratory_20261023.json",
            "fixtures/skill_routing_release_probes_20261023.json",
            "fixtures/skill_routing_untuned_20261024.json",
            "fixtures/skill_routing_stress_20261024.json",
        ):
            with self.subTest(source=filename):
                earlier = json.loads((ROOT / filename).read_text(encoding="utf-8"))
                self.assertFalse(current & {r["query"] for r in earlier["cases"]})

    def test_structural_security_oracle_and_diagnostic_metrics(self):
        report = stress.evaluate_stress(self.catalog, self.aliases,
                                        self.manifest, self.fixture)
        self.assertEqual(24, report["count"])
        self.assertEqual("NOT_MEASURED", report["calibrated_semantic_accuracy"])
        self.assertEqual("NOT_OBSERVED", report["client_discovery"])
        self.assertEqual("NOT_TESTED", report["client_effectiveness"])
        self.assertFalse(report["ranker_modified_for_cases"])
        self.assertEqual(12, report["by_language"]["ru"]["cases"])
        self.assertEqual(12, report["by_language"]["en"]["cases"])
        self.assertEqual(8, report["by_kind"]["negative"]["cases"])
        # An explicit exact-name prohibition is objectively testable. Positive
        # label overlap and ambiguous abstention remain NON-GATING diagnostics.
        for row in report["observations"]:
            with self.subTest(id=row["id"]):
                self.assertFalse(row["forbidden_selected"])
                self.assertFalse(set(row["primary"]) & set(row["auxiliary"]))
        print("HOLDOUT_342_DIAGNOSTIC=" + json.dumps({
            "summary": report["summary"], "ru": report["by_language"]["ru"],
            "en": report["by_language"]["en"],
        }, sort_keys=True), flush=True)

    def test_cli_is_offline_and_never_claims_validated_accuracy(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "skill_routing_stress.py"),
             "--cases", str(FIXTURE), "--summary-only"],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertEqual(24, report["count"])
        self.assertNotIn("observations", report)
        self.assertEqual("NOT_MEASURED", report["calibrated_semantic_accuracy"])
        self.assertEqual("NOT_VERIFIED", report["reviewer_independence"])
        self.assertEqual("DIAGNOSTIC_NON_GATING", report["scoring"])


if __name__ == "__main__":
    unittest.main()
