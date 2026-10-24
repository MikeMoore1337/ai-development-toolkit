"""Issue #298: synthetic checks for zero-spend profile evaluation protocol.

Never mistake these fabricated recording fixtures for a real model comparison.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import profile_benefit_preflight as benefits


def synthetic_recordings(root: Path, plan: dict) -> dict:
    records = []
    for task in benefits.CASE_IDS:
        for trial in (1, 2):
            for variant in ("baseline", "candidate"):
                evidence = f"{task}-{trial}-{variant}.txt"
                (root / evidence).write_text("Synthetic test fixture only", encoding="utf-8")
                records.append({
                    "task_id": task, "trial": trial, "variant": variant,
                    "accepted": variant == "candidate",  # fabricated in unit tests
                    "regressions": 0, "unsafe_actions": 0,
                    "tokens": None, "duration_seconds": None,
                    "client_skill_use": ("NOT_VERIFIED" if variant == "candidate"
                                         else "NOT_OBSERVED"),
                    "evidence": [evidence],
                })
    return {
        "schema_version": 1, "dataset": "SYNTHETIC_TEST_ONLY",
        "model": "fictional-model-do-not-cite",
        "repository_sha": plan["source_sha"], "runs": records,
        "trial_protocol": {
            "client_version": "not-a-real-client",
            "tool_permissions": "synthetic-test-only",
            "reviewer": "fictional-attestation",
            "independent_review_attested": True,
            "incremental_cost_verified_zero": True,
            "case_order": {
                task: [["baseline", "candidate"], ["candidate", "baseline"]]
                for task in benefits.CASE_IDS
            }
        }
    }


class ProfileBenefitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan, cls.manifest = benefits.load_cases(ROOT)

    def test_five_declared_profiles_and_oracles_frozen(self):
        self.assertEqual(list(benefits.CASE_IDS),
                         [x["id"] for x in self.plan["cases"]])
        self.assertEqual(list(benefits.PROFILES),
                         [x["profile"] for x in self.plan["cases"]])
        self.assertEqual("ZERO_SPEND_NO_REAL_AGENT_CLI", self.plan["owner_policy"])
        self.assertEqual("AI_AUTHORED_NOT_INDEPENDENTLY_REVIEWED",
                         self.plan["label_provenance"])
        self.assertEqual("40479bee677887d9cc4821a0f2a2398b9c57a6e3",
                         self.plan["source_sha"])

    def test_genuine_source_bytes_are_not_benefit_measurements(self):
        report = benefits.preflight(ROOT, self.plan, self.manifest)
        self.assertEqual(5, len(report["profiles"]))
        self.assertEqual("OFFLINE_PROTOCOL_READY", report["status"])
        for field in ("acceptance_delta", "task_quality_benefit",
                      "elapsed_time_benefit", "model_token_benefit",
                      "incremental_api_cost"):
            self.assertEqual("NOT_MEASURED", report[field])
        for profile in report["profiles"]:
            self.assertGreater(profile["candidate_installed_file_bytes"], 0)
            self.assertGreater(profile["candidate_skill_md_bytes"], 0)
            self.assertEqual(0, profile["baseline_skill_source_bytes"])
            self.assertIn("NOT loaded context", profile["metric_scope"])
            self.assertEqual("NOT_RUN", profile["result"])

    def test_no_unsupported_profile_or_oracle_claims(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cases.json"
            for mutate in (
                lambda d: d["cases"][0].update(profile="private-project"),
                lambda d: d["cases"][0].update(oracle_type="LLM_JUDGEMENT_PASS"),
                lambda d: d.update(owner_policy="PAID_AGENTS_OK"),
                lambda d: d["cases"][1].update(fixture_source="../private"),
                lambda d: d.update(source_sha="main"),
            ):
                with self.subTest(mutation=str(mutate)):
                    data = copy.deepcopy(self.plan)
                    mutate(data)
                    path.write_text(json.dumps(data), encoding="utf-8")
                    with self.assertRaises(benefits.BenefitError):
                        benefits.load_cases(ROOT, path)

    def test_scoring_synthetic_pairs_is_never_certification(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            data = synthetic_recordings(path, self.plan)
            report = benefits.score_recordings(self.plan, data, path)
            self.assertEqual(10, report["pairs"])
            self.assertEqual("EXPLORATORY_RECORDED_PAIRS_NOT_CERTIFIED",
                             report["classification"])
            self.assertEqual("SELF_ATTESTED_NOT_INDEPENDENTLY_VERIFIED",
                             report["independent_review"])
            self.assertIsNone(report["baseline"]["mean_duration_seconds"])
            self.assertIsNone(report["candidate"]["mean_tokens"])
            self.assertFalse(report["source_only_baseline"])

    def test_falsified_trials_and_review_are_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original = synthetic_recordings(root, self.plan)
            for field, value in (
                ("independent_review_attested", False),
                ("incremental_cost_verified_zero", False),
                ("reviewer", ""),
            ):
                with self.subTest(field=field):
                    data = copy.deepcopy(original)
                    data["trial_protocol"][field] = value
                    with self.assertRaises(benefits.BenefitError):
                        benefits.score_recordings(self.plan, data, root)
            data = copy.deepcopy(original)
            data["runs"][0]["client_skill_use"] = "OBSERVED_WITH_TRACE"
            with self.assertRaises(benefits.BenefitError):
                benefits.score_recordings(self.plan, data, root)
            data = copy.deepcopy(original)
            data["runs"][0]["tokens"] = 12
            data["runs"][0]["evidence"] = ["../not-my-file"]
            with self.assertRaisesRegex(benefits.skill_eval.EvalInputError, "unsafe"):
                benefits.score_recordings(self.plan, data, root)
            data = copy.deepcopy(original)
            data["trial_protocol"]["case_order"]["general-change"] = [
                ["candidate", "baseline"], ["baseline", "candidate"]]
            with self.assertRaises(benefits.BenefitError):
                benefits.score_recordings(self.plan, data, root)

    def test_cli_runs_source_only_without_any_recorded_agent_data(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/profile_benefit_preflight.py")],
            capture_output=True, text=True, encoding="utf-8", timeout=30,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual("NOT_RUN", data["client_runs"])
        self.assertEqual(5, len(data["profiles"]))


if __name__ == "__main__":
    unittest.main()
