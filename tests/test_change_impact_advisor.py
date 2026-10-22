"""Offline change-impact risk and completeness tests."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("change_impact", ROOT / "scripts/change_impact_advisor.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ChangeImpactTests(unittest.TestCase):
    def checks(self, paths):
        result = module.analyze(paths)
        return result, {v["check"] for v in result["recommended_checks"]}

    def test_security_change_keeps_critical_negative_cases(self):
        report, checks = self.checks(["src/auth/session.py"])
        self.assertEqual("CRITICAL", report["risk"])
        self.assertTrue({"authorization-negative", "cross-user-denial", "session-expiry"} <= checks)
        self.assertEqual("NOT_RUN", report["execution"])
        self.assertTrue(all(c["execution"] == "NOT_RUN" for c in report["recommended_checks"]))

    def test_database_and_api_change_keeps_rollback_and_contract(self):
        report, checks = self.checks(["db/migrations/001.sql", "api/routes/users.py"])
        self.assertEqual("CRITICAL", report["risk"])
        self.assertTrue({"migration-rollback", "migration-forward", "data-integrity",
                         "api-contract-compatibility", "invalid-request-negative",
                         "integration-boundary"} <= checks)

    def test_frontend_and_worker_regressions(self):
        _, checks = self.checks(["frontend/screens/workout.tsx", "src/workers/retry.py"])
        self.assertTrue({"ui-state-regression", "keyboard-accessibility",
                         "duplicate-delivery", "retry-and-recovery",
                         "integration-boundary"} <= checks)

    def test_unknown_changes_require_review_not_fabricated_test_execution(self):
        report, checks = self.checks(["README.md"])
        self.assertEqual("LOW", report["risk"])
        self.assertEqual(["README.md"], report["unknown_scope"])
        self.assertEqual({"change-scope-review"}, checks)
        self.assertEqual("NOT_OBSERVED", report["ci_evidence"])

    def test_untrusted_paths_fail_closed(self):
        for paths in ([], ["../secret"], ["/etc/passwd"], [""], ["a\x00b"], [None]):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                module.analyze(paths)

    def test_input_is_deterministic_and_deduplicated(self):
        one, _ = self.checks(["src/auth/session.py", "src/auth/session.py"])
        two, _ = self.checks(["src/auth/session.py"])
        self.assertEqual(one, two)

    def test_cli_reads_only_input_json(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "changed.json"
            path.write_text(json.dumps(["src/auth/session.py"]), encoding="utf-8")
            self.assertEqual(0, module.main(["--paths-json", str(path)]))
            self.assertEqual(json.dumps(["src/auth/session.py"]), path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
