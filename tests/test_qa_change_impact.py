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

    def test_every_check_has_safe_catalog_backed_scenario(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(set(qa.CHECKS), set(qa.CHECK_GUIDANCE))
        for check_id, (profile, skill, scenario) in qa.CHECK_GUIDANCE.items():
            with self.subTest(check=check_id):
                self.assertIn(profile, manifest["profiles"])
                self.assertIn(skill, manifest["profiles"][profile])
                self.assertGreater(len(scenario), 22)

        for paths in (
            ["backend/auth/session.py", "frontend/components/LoginForm.tsx"],
            ["backend/api/routes.py", "db/migrations/002.sql"],
            ["src/queue/worker.py", "src/security/pii.py"],
            [".github/workflows/release.yml", "misc/unknown.extension"],
            ["docs/README.md"],
        ):
            for item in qa.plan(paths)["recommendations"]:
                with self.subTest(paths=paths, check=item["id"]):
                    hint = item["guidance"]
                    self.assertIn(hint["profile_hint"], manifest["profiles"])
                    self.assertIn(hint["skill_hint"],
                                  manifest["profiles"][hint["profile_hint"]])
                    self.assertEqual("STATIC_MANIFEST_CATALOG_HINT", hint["source"])
                    self.assertEqual("NOT_VERIFIED", hint["client_skill_activation"])
                    self.assertEqual("NOT_RUN", hint["test_execution"])
                    self.assertEqual("NOT_RUN", item["status"])
                    self.assertIsNone(item["test_command"])
                    self.assertIsNone(item["execution_receipt"])

    def test_content_enrichment_adds_hints_without_execution_claim(self):
        path = "src/misc/feature.py"
        report = qa.plan([path])
        inspected = {
            "files": {path: {"signals": ["AUTH", "API"],
                             "binary_or_unparsed": False}},
            "requires_manual_review": False,
        }
        enriched = qa.add_content_evidence(report, inspected)
        by_id = {item["id"]: item for item in enriched["recommendations"]}
        for check_id in ("auth-boundary", "api-contract", "privacy-boundary"):
            self.assertEqual("CONTENT_TOKEN_HINT_ONLY", by_id[check_id]["evidence"])
            self.assertEqual("NOT_RUN", by_id[check_id]["guidance"]["test_execution"])
            self.assertIsNone(by_id[check_id]["test_command"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", enriched["gate"])
        self.assertEqual(0, enriched["executed_tests"])

    def test_path_inventory_deduplicated_deterministically(self):
        a = qa.plan(["backend/db/schema.sql", "frontend/components/SetForm.tsx",
                     "backend/db/schema.sql"])
        b = qa.plan(["frontend/components/SetForm.tsx", "backend/db/schema.sql"])
        self.assertEqual(a, b)
        self.assertEqual(2, len(a["changed_paths"]))
        self.assertIn("cross-layer", {r["id"] for r in a["recommendations"]})

    def test_docs_only_requires_review_without_runtime_test_claims(self):
        p = qa.plan([".agents/README.md", "ai/README.md"])
        checks = {x["id"] for x in p["recommendations"]}
        self.assertEqual({"change-review", "documentation-review"}, checks)
        self.assertEqual([], p["unmapped_paths"])
        self.assertEqual([], p["surfaces"] if isinstance(p["surfaces"], list) else list(p["surfaces"]))
        self.assertEqual([], p["required_critical_check_ids"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", p["gate"])

    def test_unknown_source_still_requires_human_inspection(self):
        p = qa.plan(["misc/custom_extension.xyz"])
        self.assertIn("unmapped-impact", {x["id"] for x in p["recommendations"]})
        self.assertEqual(["misc/custom_extension.xyz"], p["unmapped_paths"])

    def test_docs_mixed_with_source_never_create_false_runtime_paths(self):
        p = qa.plan(["docs/API.md", "backend/api/routes.py"])
        rec = {r["id"]: r for r in p["recommendations"]}
        self.assertEqual(["docs/API.md"], rec["documentation-review"]["changed_paths"])
        self.assertEqual(["backend/api/routes.py"], rec["targeted-unit"]["changed_paths"])
        self.assertEqual(["backend/api/routes.py"], rec["api-contract"]["changed_paths"])
        self.assertNotIn("docs/API.md", p["unmapped_paths"])

    def test_changed_tests_are_reviewed_without_unknown_file_alarm(self):
        p = qa.plan(["backend/tests/test_workout_noop_patch.py"])
        rec = {r["id"]: r for r in p["recommendations"]}
        self.assertIn("test-review", rec)
        self.assertIn("targeted-unit", rec)
        self.assertNotIn("unmapped-impact", rec)
        self.assertEqual([], p["unmapped_paths"])
        self.assertTrue(all(r["status"] == "NOT_RUN" for r in rec.values()))

    def test_hermes_server_and_legacy_web_are_path_hints_only(self):
        p = qa.plan(["control_center/server.py", "control_center/web/app.js",
                     ".github/workflows/control-center-ui.yml"])
        rec = {r["id"]: r for r in p["recommendations"]}
        self.assertIn("api-contract", rec)
        self.assertIn("api-negative", rec)
        self.assertIn("ui-state", rec)
        self.assertIn("cross-layer", rec)
        self.assertIn("deployment-safety", p["required_critical_check_ids"])
        self.assertTrue(all(r["evidence"] == "PATH_HEURISTIC_ONLY" for r in rec.values()))
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


    def test_declared_mapping_keeps_every_test_not_run(self):
        mapping = qa.load_test_map(ROOT / "fixtures/qa_change_impact_test_map.json")
        result = qa.plan(["frontend/views/workout.tsx", "backend/api/schema.py"],
                         test_map=mapping)
        chosen = result["declared_test_candidates"]
        self.assertTrue(chosen)
        self.assertEqual("OWNER_DECLARED_NOT_VERIFIED", result["test_mapping_source"])
        self.assertIn("targeted-unit", result["unmapped_check_ids"])
        self.assertTrue(all(item["status"] == "NOT_RUN" for item in chosen))
        self.assertTrue(all(item["source"] == "OWNER_DECLARED_NOT_VERIFIED" for item in chosen))
        self.assertTrue(all(item["execution_receipt"] is None for item in chosen))
        self.assertIn("tests/e2e/workout.spec.ts::restore_after_unlock",
                      {item["test_id"] for item in chosen})
        self.assertEqual("INSUFFICIENT_EVIDENCE", result["gate"])
        self.assertEqual(0, result["executed_tests"])

    def test_mapping_matches_whole_prefix_not_similar_directory(self):
        example = {"schema_version": 1, "entries": [{
            "id": "auth", "prefix": "backend/auth/", "check_ids": ["auth-boundary"],
            "test_ids": ["tests/security/test_auth.py::deny"],
            "requirement_ids": ["FIXTURE-DENY"],
        }]}
        result = qa.plan(["backend/authors/permissions.py"], test_map=example)
        self.assertEqual([], result["declared_test_candidates"])
        self.assertEqual("INSUFFICIENT_EVIDENCE", result["gate"])

    def test_mapping_strict_schema_rejects_commands_and_injection(self):
        fixture = qa.load_test_map(ROOT / "fixtures/qa_change_impact_test_map.json")
        mutants = [
            lambda x: x["entries"][0].update(run="curl https://evil.invalid"),
            lambda x: x["entries"][0].update(prefix="../"),
            lambda x: x["entries"][0].update(check_ids=["made-up"]),
            lambda x: x["entries"][0].update(test_ids=["; rm -rf /"]),
            lambda x: x["entries"][0].update(test_ids=["../secret"]),
            lambda x: x["entries"][0].update(requirement_ids=["secret token"]),
            lambda x: x["entries"][0].update(id=x["entries"][1]["id"]),
            lambda x: x["entries"][0].update(test_ids=[]),
            lambda x: x.update(schema_version=True),
        ]
        for mutation in mutants:
            with self.subTest(mutation=str(mutation)):
                data = copy.deepcopy(fixture)
                mutation(data)
                with self.assertRaises(qa.ImpactInputError):
                    qa.plan(["frontend/views/workout.tsx"], test_map=data)

    def test_file_size_and_bad_json_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "owner-test-map.json"
            path.write_text("x" * (qa.MAPPING_MAX_BYTES + 1), encoding="utf-8")
            with self.assertRaisesRegex(qa.ImpactInputError, "too large"):
                qa.load_test_map(path)
            path.write_text("{invalid", encoding="utf-8")
            with self.assertRaisesRegex(qa.ImpactInputError, "invalid JSON"):
                qa.load_test_map(path)

    def test_cli_test_map_never_executes_or_overwrites_report(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "report.json"
            args = ["--paths", "backend/auth/permissions.py", "--test-map",
                    str(ROOT / "fixtures/qa_change_impact_test_map.json"),
                    "--output", str(output)]
            self.assertEqual(0, qa.main(args))
            report = json.loads(output.read_text(encoding="utf-8"))
            self.assertTrue(report["declared_test_candidates"])
            self.assertEqual("NOT_RUN", report["declared_test_candidates"][0]["status"])
            self.assertEqual(0, report["executed_tests"])
            original = output.read_bytes()
            self.assertEqual(2, qa.main(args))
            self.assertEqual(original, output.read_bytes())


if __name__ == "__main__":
    unittest.main()
