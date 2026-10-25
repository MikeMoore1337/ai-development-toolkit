"""Synthetic negative tests for the cross-repository orchestration pilot ledger."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_orchestration_pilot as pilot


class PilotLedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reference = json.loads((ROOT / "fixtures/orchestration_pilot_reference.json").read_text(encoding="utf-8"))

    def fresh(self):
        return copy.deepcopy(self.reference)

    def reject(self, expected, doc):
        self.assertIn(expected, pilot.validate(doc))

    def observed(self, doc, index=0):
        doc["policy"].update({
            "owner_runtime_approved": True,
            "verified_zero_incremental_cost": True,
            "verified_isolation": True,
            "approval_reference": "independently-confirmed-owner-record",
            "cost_reference": "independently-confirmed-no-overage-record",
            "isolation_reference": "isolated-runner-attestation",
        })
        row = doc["cases"][index]
        for arm, traces in (("baseline", ["real-cli-a"]), ("orchestra", ["real-cli-b", "real-cli-c"])):
            run = row[arm]
            run.update({
                "status": "OBSERVED", "client": "codex", "model": "fixed-model",
                "invocation_id": "run-" + arm,
                "worker_traces": traces, "evidence": ["trace-and-test-evidence-" + arm],
                "elapsed_seconds": 12.0, "tokens_used": None,
            })
        return doc

    def test_pilot_documentation_freshness_and_evidence_boundaries(self):
        import hashlib

        source = ROOT / "docs/ORCHESTRATION_PILOT.md"
        translation = ROOT / "docs/ru/ORCHESTRATION_PILOT.md"
        revisions = json.loads((ROOT / "docs/ru/SOURCE_REVISIONS.json").read_text(encoding="utf-8"))
        matches = [entry for entry in revisions["pairs"] if entry["source"] == "docs/ORCHESTRATION_PILOT.md"]
        self.assertEqual(1, len(matches))
        self.assertEqual("docs/ru/ORCHESTRATION_PILOT.md", matches[0]["translation"])
        digest = hashlib.sha256(source.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        self.assertEqual(digest, matches[0]["source_sha256"])
        for guide in (source, translation):
            content = guide.read_text(encoding="utf-8")
            self.assertIn("v5.5.2", content)
            self.assertIn("NOT_RUN", content)
            self.assertIn("NOT_MEASURED", content)
            self.assertIn("verified_zero_incremental_cost=false", content)
            self.assertIn("verified_isolation=false", content)

    def test_unrun_reference_is_consistent_not_evidence(self):
        self.assertEqual([], pilot.validate(self.fresh()))

    def test_duplicate_or_missing_case(self):
        doc = self.fresh()
        doc["cases"][2] = copy.deepcopy(doc["cases"][0])
        self.reject("CASE_REGISTRY", doc)

    def test_wrong_repository(self):
        doc = self.fresh()
        doc["cases"][0]["repository"] = "example/fake"
        self.reject("REPO_MISMATCH", doc)

    def test_invalid_sha(self):
        doc = self.fresh()
        doc["cases"][0]["revision"] = "main"
        self.reject("REVISION", doc)

    def test_missing_ac(self):
        doc = self.fresh()
        doc["cases"][0]["acceptance_ids"] = []
        self.reject("ACCEPTANCE", doc)

    def test_reference_uses_all_source_issue_acceptance_ids(self):
        doc = self.fresh()
        self.assertEqual([], pilot.validate(doc))
        for case in doc["cases"]:
            required = list(pilot.REQUIRED_ACCEPTANCE_IDS[case["id"]])
            self.assertEqual(case["acceptance_ids"], required)
            self.assertEqual(case["baseline"]["acceptance_ids"], required)
            self.assertEqual(case["orchestra"]["acceptance_ids"], required)

    def test_consistent_but_incomplete_pair_is_rejected(self):
        # Two shortened arms used to pass: equality is not issue coverage.
        doc = self.fresh()
        row = doc["cases"][0]
        shortened = ["WEB-A1", "WEB-A2"]
        for key in ("acceptance_ids",):
            row[key] = shortened
            row["baseline"][key] = shortened
            row["orchestra"][key] = shortened
        self.reject("ACCEPTANCE_REGISTRY", doc)
        self.assertNotIn("UNEQUAL_INPUTS", pilot.validate(doc))

    def test_incorrect_issue_id_is_rejected_even_if_arms_match(self):
        doc = self.fresh()
        row = doc["cases"][1]
        ids = ["AGENT-A1", "AGENT-A2", "AGENT-A3", "AGENT-A4", "MISSING_AC5"]
        row["acceptance_ids"] = ids
        row["baseline"]["acceptance_ids"] = ids
        row["orchestra"]["acceptance_ids"] = ids
        self.reject("ACCEPTANCE_REGISTRY", doc)

    def test_incorrect_issue_registry_rejected_for_all_projects(self):
        for index in range(3):
            doc = self.fresh()
            row = doc["cases"][index]
            reduced = row["acceptance_ids"][:-1]
            row["acceptance_ids"] = reduced
            row["baseline"]["acceptance_ids"] = reduced
            row["orchestra"]["acceptance_ids"] = reduced
            with self.subTest(project=row["id"]):
                self.reject("ACCEPTANCE_REGISTRY", doc)

    def test_unequal_baseline_source(self):
        doc = self.fresh()
        doc["cases"][0]["baseline"]["revision"] = "f" * 40
        self.reject("UNEQUAL_INPUTS", doc)

    def test_faked_agent_on_unrun_fixture(self):
        doc = self.fresh()
        doc["cases"][0]["orchestra"]["worker_traces"] = ["imaginary"]
        self.reject("FAKE_OBSERVATION", doc)

    def test_faked_token_savings(self):
        doc = self.fresh()
        doc["cases"][0]["orchestra"]["tokens_used"] = 1
        self.reject("FAKE_OBSERVATION", doc)

    def test_no_paid_api(self):
        doc = self.fresh()
        doc["policy"]["paid_api_allowed"] = True
        self.reject("NO_PAID_API", doc)

    def test_no_self_declared_missing_cost_reference(self):
        doc = self.fresh()
        doc["policy"]["verified_zero_incremental_cost"] = True
        self.reject("UNSUPPORTED_GATE", doc)

    def test_observed_without_runtime_approval_is_rejected(self):
        doc = self.observed(self.fresh())
        doc["policy"]["owner_runtime_approved"] = False
        doc["policy"]["approval_reference"] = None
        self.reject("LIVE_GATE", doc)

    def test_parallel_requires_distinct_real_traces(self):
        doc = self.observed(self.fresh())
        doc["cases"][0]["orchestra"]["worker_traces"] = ["same", "same"]
        self.reject("REAL_WORKERS_UNVERIFIED", doc)

    def test_two_roles_are_not_two_workers(self):
        doc = self.observed(self.fresh())
        doc["cases"][0]["orchestra"]["worker_traces"] = ["only-one"]
        self.reject("REAL_WORKERS_UNVERIFIED", doc)

    def test_no_observations_without_trace_references(self):
        doc = self.observed(self.fresh())
        doc["cases"][0]["orchestra"]["evidence"] = []
        self.reject("EXECUTION_EVIDENCE", doc)

    def test_wrong_model_comparison(self):
        doc = self.observed(self.fresh())
        doc["cases"][0]["orchestra"]["model"] = "other-model"
        self.reject("MODEL_CONFOUND", doc)

    def test_missing_elapsed_time(self):
        doc = self.observed(self.fresh())
        doc["cases"][0]["baseline"]["elapsed_seconds"] = None
        self.reject("INVALID_TIME", doc)

    def test_one_observed_case_does_not_mean_comparison_ready(self):
        doc = self.observed(self.fresh())
        doc["conclusion"] = "PENDING_INDEPENDENT_REVIEW"
        self.reject("PREMATURE_COMPARISON", doc)

    def test_all_three_real_pairs_only_pending_review(self):
        doc = self.fresh()
        for index in range(3):
            self.observed(doc, index)
        doc["conclusion"] = "PENDING_INDEPENDENT_REVIEW"
        self.assertEqual([], pilot.validate(doc))
        # This tests the declaration contract only, NOT real model execution.

    def test_invented_nested_worker_trace_fails_closed(self):
        doc = self.fresh()
        doc["cases"][0]["baseline"]["worker_traces"] = [{"unhashable": True}]
        self.reject("FAKE_OBSERVATION", doc)


if __name__ == "__main__":
    unittest.main()
