"""QA test-selection contract: synthetic risk oracles, not executed project tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import qa_change_impact as qa


class ChangeImpactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(
            (ROOT / "fixtures/qa_change_impact_cases.json").read_text(encoding="utf-8")
        )["cases"]

    def test_critical_check_oracles_never_omitted(self):
        for case in self.fixture:
            with self.subTest(case=case["id"]):
                result = qa.plan(case["changed_paths"])
                actual = {c["id"] for c in result["recommendations"]}
                self.assertTrue(set(case["required_checks"]) <= actual,
                                (case["id"], actual))
                self.assertEqual("INSUFFICIENT_EVIDENCE", result["gate"])
                self.assertEqual(0, result["executed_tests"])
                for item in result["recommendations"]:
                    self.assertEqual("NOT_RUN", item["status"])
                    self.assertEqual("PATH_HEURISTIC_ONLY", item["evidence"])
                    self.assertIsNone(item["execution_receipt"])
                    self.assertIsNone(item["test_command"])

    def test_path_inventory_deduplicated_deterministically(self):
        a = qa.plan(["backend/db/schema.sql", "frontend/components/SetForm.tsx",
                     "backend/db/schema.sql"])
        b = qa.plan(["frontend/components/SetForm.tsx", "backend/db/schema.sql"])
        self.assertEqual(a, b)
        self.assertEqual(2, len(a["changed_paths"]))
        self.assertIn("cross-layer", {r["id"] for r in a["recommendations"]})

    def test_unknown_only_requires_inspection_not_green_gate(self):
        p = qa.plan(["docs/README.md"])
        checks = {x["id"] for x in p["recommendations"]}
        self.assertEqual({"change-review", "targeted-unit", "unmapped-impact"}, checks)
        self.assertEqual(["docs/README.md"], p["unmapped_paths"])
        self.assertEqual([], p["required_critical_check_ids"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", p["gate"])

    def test_high_risk_never_dropped_from_critical_set(self):
        p = qa.plan(["backend/auth/permissions.py",
                     "db/migrations/2025_account.sql",
                     ".github/workflows/deploy.yml"])
        self.assertEqual(
            {"auth-boundary", "privacy-boundary", "db-migration",
             "db-rollback", "deployment-safety"},
            set(p["required_critical_check_ids"]),
        )
        self.assertFalse(any(r["status"] == "PASS" for r in p["recommendations"]))

    def test_untrusted_paths_rejected_instead_of_normalized_away(self):
        bad = [
            ["../passwd"], ["/tmp/secret"], ["C:\\Windows\\secret"],
            ["frontend//component.py"], [".hidden/../file"], [""],
            ["--output"], ["https://evil.test/p.py"],
            ["repo/\x00secret"], ["space\nname"], ["a" * 301],
        ]
        for paths in bad:
            with self.subTest(paths=paths):
                with self.assertRaises(qa.ImpactInputError):
                    qa.plan(paths)
        with self.assertRaises(qa.ImpactInputError):
            qa.plan([])
        with self.assertRaises(qa.ImpactInputError):
            qa.plan(["file" + str(i) for i in range(201)])

    def test_revision_labels_are_not_automatically_git_evidence(self):
        shas = ("a" * 40, "b" * 40)
        report = qa.plan(["backend/api/routes.py"], base=shas[0], head=shas[1])
        self.assertEqual("SUPPLIED_PATH_LIST", report["source_verification"])
        with self.assertRaisesRegex(qa.ImpactInputError, "requires exact SHA"):
            qa.plan(["backend/api/routes.py"], source="LOCAL_GIT_DIFF")

    def test_local_git_diff_uses_only_exact_sha_and_checked_result(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            (root / ".git").mkdir()
            payload = b"backend/api/auth/session.py\x00frontend/views/workout.py\x00"
            with patch.object(qa.subprocess, "run", return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout=payload, stderr=b""
            )) as call:
                result = qa.changed_paths_by_git(root, "a" * 40, "b" * 40)
            self.assertEqual(2, len(result))
            argv = call.call_args.args[0]
            self.assertIn("--no-ext-diff", argv)
            self.assertEqual(["a" * 40, "b" * 40, "--"], argv[-3:])
            with self.assertRaises(qa.ImpactInputError):
                qa.changed_paths_by_git(root, "HEAD~1", "b" * 40)
            with patch.object(qa.subprocess, "run", return_value=subprocess.CompletedProcess(
                args=[], returncode=128, stdout=b"", stderr=b"error"
            )):
                with self.assertRaisesRegex(qa.ImpactInputError, "Cannot verify"):
                    qa.changed_paths_by_git(root, "a" * 40, "b" * 40)

    def test_cli_never_overwrites_existing_report(self):
        with tempfile.TemporaryDirectory() as dirname:
            path = Path(dirname) / "impact.json"
            args = ["--paths", "backend/api/routes.py", "--output", str(path)]
            self.assertEqual(0, qa.main(args))
            original = path.read_bytes()
            self.assertEqual(2, qa.main(args))
            self.assertEqual(original, path.read_bytes())
            report = json.loads(original)
            self.assertEqual("SUPPLIED_PATH_LIST", report["source_verification"])
            self.assertEqual("NOT_TESTED", report["client_effectiveness"])

    def test_scope_conflicts_fail_closed(self):
        with tempfile.TemporaryDirectory() as dirname:
            with patch.object(sys, "argv", ["qa_change_impact.py", "--paths",
                                            "backend/api/routes.py", "--git-head", "a" * 40]):
                self.assertEqual(2, qa.main(sys.argv[1:]))
        with self.assertRaises(qa.ImpactInputError):
            qa.plan(["x"], source="INFERRED_AGENT_OUTPUT")

    def test_source_diff_is_heuristic_not_a_call_graph(self):
        result = qa.plan(["frontend/views/login.py", "backend/db/migrations/100.sql"])
        self.assertIn("cross-layer", {x["id"] for x in result["recommendations"]})
        self.assertTrue(any("not inspected" in x.lower() for x in result["limitations"]))
        self.assertTrue(all(x["changed_paths"] for x in result["recommendations"]))


if __name__ == "__main__":
    unittest.main()
