"""Read-only exact-SHA diff inspection: no source excerpts or invented QA PASS."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import qa_change_impact as qa
import qa_diff_signals as hints

PATCH = (
    b"diff --git a/src/custom/view.py b/src/custom/view.py\n"
    b"index 1111111..2222222 100644\n"
    b"--- a/src/custom/view.py\n"
    b"+++ b/src/custom/view.py\n"
    b"@@ -3 +3,2 @@\n"
    b"-# removed\n"
    b"+@router.post('/api')\n"
    b"+def create(): useEffect()\n"
    b"diff --git a/src/custom/schema.py b/src/custom/schema.py\n"
    b"index 1111111..2222222 100644\n"
    b"--- a/src/custom/schema.py\n"
    b"+++ b/src/custom/schema.py\n"
    b"@@ -1 +1 @@\n"
    b"-old = True\n"
    b"+ALTER TABLE accounts DROP COLUMN role\n"
)
PATHS = ["src/custom/view.py", "src/custom/schema.py"]


class ContentDiffTests(unittest.TestCase):
    def test_unknown_paths_now_surface_relevant_contract_checks(self):
        inspection = hints.inspect_patch(PATCH, PATHS)
        self.assertEqual(2, inspection["file_count"])
        self.assertEqual(2, inspection["text_files_with_hunks"])
        self.assertEqual([], inspection["requires_manual_review"])
        self.assertIn("API", inspection["files"]["src/custom/view.py"]["signals"])
        self.assertIn("UI", inspection["files"]["src/custom/view.py"]["signals"])
        self.assertIn("DB", inspection["files"]["src/custom/schema.py"]["signals"])
        self.assertFalse(inspection["raw_source_lines_returned"])
        self.assertNotIn("ALTER TABLE", str(inspection))
        output = qa.add_content_evidence(qa.plan(PATHS), inspection)
        checks = {r["id"]: r for r in output["recommendations"]}
        for must in ("api-contract", "api-negative", "ui-state", "browser-flow",
                     "db-migration", "db-rollback"):
            self.assertIn(must, checks)
            self.assertEqual("NOT_RUN", checks[must]["status"])
            self.assertIn(checks[must]["evidence"],
                          {"PATH_HEURISTIC_ONLY", "CONTENT_TOKEN_HINT_ONLY"})
            self.assertIsNone(checks[must]["execution_receipt"])
        # Some checks were already required by the filename heuristic and
        # must retain their original evidence provenance.
        self.assertEqual("PATH_HEURISTIC_ONLY", checks["api-contract"]["evidence"])
        self.assertEqual("CONTENT_TOKEN_HINT_ONLY", checks["db-rollback"]["evidence"])
        self.assertEqual("CONTENT_TOKEN_HINT_ONLY", checks["ui-state"]["evidence"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", output["gate"])
        self.assertEqual(0, output["executed_tests"])
        self.assertIn("db-rollback", output["required_critical_check_ids"])


    def test_yfc_like_state_change_adds_replay_integrity_and_consumer_review(self):
        path = "backend/fitminiapp_api/services/workout_sync.py"
        patch = (
            b"diff --git a/backend/fitminiapp_api/services/workout_sync.py "
            b"b/backend/fitminiapp_api/services/workout_sync.py\n"
            b"--- a/backend/fitminiapp_api/services/workout_sync.py\n"
            b"+++ b/backend/fitminiapp_api/services/workout_sync.py\n"
            b"@@ -1 +1,3 @@\n"
            b"-set_row.version += 1\n"
            b"+if not applied: raise WorkoutSetSyncError(422, 'empty')\n"
            b"+set_row.version += 1\n"
            b"+mutation_id = request_fingerprint\n"
        )
        inspection = hints.inspect_patch(patch, [path])
        self.assertIn("PERSISTED_STATE", inspection["files"][path]["signals"])
        enriched = qa.add_content_evidence(qa.plan([path]), inspection)
        checks = {row["id"]: row for row in enriched["recommendations"]}
        for cid in ("state-integrity", "async-replay", "consumer-review"):
            self.assertIn(cid, checks)
            self.assertEqual("NOT_RUN", checks[cid]["status"])
            expected_source = ("PATH_HEURISTIC_ONLY" if cid == "consumer-review"
                               else "CONTENT_TOKEN_HINT_ONLY")
            self.assertEqual(expected_source, checks[cid]["evidence"])
            self.assertEqual([path], checks[cid]["changed_paths"])
            self.assertIsNone(checks[cid]["execution_receipt"])
        self.assertNotIn("db-migration", checks)
        self.assertNotIn("db-rollback", checks)
        self.assertEqual(0, enriched["executed_tests"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", enriched["gate"])

    def test_state_hints_do_not_invent_test_maps_or_known_consumers(self):
        path = "services/custom/mutation.py"
        patch = (
            b"diff --git a/services/custom/mutation.py b/services/custom/mutation.py\n"
            b"--- a/services/custom/mutation.py\n"
            b"+++ b/services/custom/mutation.py\n"
            b"@@ -1 +1 @@\n-old = 1\n+expected_version = request.version\n"
        )
        report = qa.add_content_evidence(
            qa.plan([path]), hints.inspect_patch(patch, [path])
        )
        self.assertIn("consumer-review", report["unmapped_check_ids"])
        self.assertEqual([], report["declared_test_candidates"])
        self.assertEqual("NONE", report["test_mapping_source"])
        self.assertEqual(0, report["executed_tests"])

    def test_api_change_adds_consumer_review_without_claiming_call_graph(self):
        report = qa.add_content_evidence(qa.plan(PATHS), hints.inspect_patch(PATCH, PATHS))
        checks = {x["id"]: x for x in report["recommendations"]}
        self.assertIn("consumer-review", checks)
        self.assertIn("src/custom/view.py", checks["consumer-review"]["changed_paths"])
        self.assertEqual("NOT_RUN", checks["consumer-review"]["status"])

    def test_non_state_docs_diff_remains_without_mutation_hints(self):
        path = "docs/overview.md"
        patch = (
            b"diff --git a/docs/overview.md b/docs/overview.md\n"
            b"--- a/docs/overview.md\n+++ b/docs/overview.md\n"
            b"@@ -1 +1 @@\n-Old description\n+New description\n"
        )
        report = qa.add_content_evidence(
            qa.plan([path]), hints.inspect_patch(patch, [path])
        )
        ids = {x["id"] for x in report["recommendations"]}
        self.assertNotIn("state-integrity", ids)
        self.assertNotIn("consumer-review", ids)
        self.assertEqual("INSUFFICIENT_EVIDENCE", report["gate"])

    def test_existing_high_risk_checks_are_not_removed(self):
        original = qa.plan(["src/auth/permissions.py", "src/custom/view.py"])
        evidence = hints.inspect_patch(
            PATCH.split(b"diff --git a/src/custom/schema.py")[0],
            ["src/custom/view.py", "src/auth/permissions.py"],
        )
        augmented = qa.add_content_evidence(original, evidence)
        before = {x["id"] for x in original["recommendations"]}
        after = {x["id"] for x in augmented["recommendations"]}
        self.assertTrue(before <= after)
        self.assertIn("auth-boundary", after)
        self.assertIn("src/auth/permissions.py", evidence["requires_manual_review"])
        self.assertEqual("TOKEN_HINTS_WITH_GAPS", augmented["content_evidence_status"])

    def test_secret_like_content_never_returns_original_lines(self):
        raw = (b"diff --git a/src/private.py b/src/private.py\n"
               b"--- a/src/private.py\n+++ b/src/private.py\n"
               b"@@ -0,0 +1 @@\n+api_key = 'sensitive-value-must-not-appear'\n")
        report = hints.inspect_patch(raw, ["src/private.py"])
        self.assertEqual(1, report["files"]["src/private.py"]["signals"]["PRIVACY"])
        self.assertNotIn("sensitive-value-must-not-appear", str(report))

    def test_binary_and_missing_hunks_are_manual_not_safe(self):
        evidence = hints.inspect_patch(b"", ["docs/manual.pdf"])
        self.assertEqual(["docs/manual.pdf"], evidence["requires_manual_review"])
        summary = qa.add_content_evidence(qa.plan(["docs/manual.pdf"]), evidence)
        self.assertIn("unmapped-impact", {c["id"] for c in summary["recommendations"]})
        self.assertEqual("INSUFFICIENT_EVIDENCE", summary["gate"])

    def test_oversized_non_utf8_and_unverified_patch_paths_blocked(self):
        bad = [
            (b"x" * (hints.MAX_PATCH_BYTES + 1), ["src/code.py"]),
            (b"\xff", ["src/code.py"]),
            (PATCH, ["src/other.py"]),
        ]
        for raw, names in bad:
            with self.subTest(raw_len=len(raw)):
                with self.assertRaises(hints.DiffEvidenceError):
                    hints.inspect_patch(raw, names)

    def test_git_patch_arguments_pinned_and_no_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            with patch.object(hints.subprocess, "run",
                              return_value=subprocess.CompletedProcess(
                                  args=[], returncode=0, stdout=PATCH, stderr=b""
                              )) as call:
                result = hints.inspect_git(root, "a" * 40, "b" * 40, PATHS)
            self.assertEqual(2, result["text_files_with_hunks"])
            args = call.call_args.args[0]
            self.assertIn("--no-textconv", args)
            self.assertIn("--no-ext-diff", args)
            self.assertEqual(["a" * 40, "b" * 40, "--"], args[-3:])
            self.assertFalse(call.call_args.kwargs.get("shell", False))
            with self.assertRaisesRegex(hints.DiffEvidenceError, "Exact full"):
                hints.inspect_git(root, "HEAD~1", "b" * 40, PATHS)
            with patch.object(hints.subprocess, "run",
                              return_value=subprocess.CompletedProcess(
                                  args=[], returncode=1, stdout=b"", stderr=b"private"
                              )):
                with self.assertRaises(hints.DiffEvidenceError):
                    hints.inspect_git(root, "a" * 40, "b" * 40, PATHS)

    def test_declared_map_not_implicitly_proven_by_patch_hints(self):
        mapping = qa.load_test_map(ROOT / "fixtures/qa_change_impact_test_map.json")
        result = qa.plan(["src/custom/view.py"], test_map=mapping)
        augmented = qa.add_content_evidence(
            result,
            hints.inspect_patch(PATCH.split(b"diff --git a/src/custom/schema.py")[0],
                                ["src/custom/view.py"]),
            mapping,
        )
        self.assertEqual("OWNER_DECLARED_NOT_VERIFIED", augmented["test_mapping_source"])
        self.assertIn("api-contract", augmented["unmapped_check_ids"])
        self.assertEqual(0, augmented["executed_tests"])

    def test_cli_rejects_content_analysis_without_exact_git_pair(self):
        self.assertEqual(2, qa.main([
            "--paths", "src/custom/view.py", "--inspect-diff",
        ]))


if __name__ == "__main__":
    unittest.main()
