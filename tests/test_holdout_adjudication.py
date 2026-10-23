"""Offline, fail-closed evidence tests for holdout label review without a model."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import holdout_adjudication as review
from skill_routing_eval import RoutingInputError

HOLDOUT = ROOT / "fixtures/skill_routing_holdout.json"


class HoldoutAdjudicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = review.prepare(ROOT, HOLDOUT)

    def test_review_catalog_matches_packet_digest_without_reference_labels(self):
        data = review.catalog_for_reviewer(ROOT)
        packet = self.template
        self.assertEqual(packet["catalog_sha256"], data["catalog_sha256"])
        self.assertEqual("blinded_review_skill_catalog", data["purpose"])
        self.assertEqual(len(data["skills"]), data["skill_count"])
        self.assertEqual(len(review.read_catalog(ROOT)), data["skill_count"])
        self.assertEqual(sorted(row["name"] for row in data["skills"]),
                         [row["name"] for row in data["skills"]])
        self.assertTrue(all(row["description"] for row in data["skills"]))
        self.assertNotIn("cases", data)
        self.assertNotIn("expected", data)
        self.assertNotIn("predictions", data)
        self.assertNotIn("proposed_targets", data)
        self.assertEqual("NOT_VERIFIED", data["reviewer_independence"])
        self.assertEqual("NOT_TESTED", data["client_effectiveness"])
        self.assertEqual(data, review.catalog_for_reviewer(ROOT))

    def test_catalog_cli_is_read_only_and_refuses_to_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            where = Path(folder) / "skill-choices.json"
            self.assertEqual(0, review.main(["catalog", "--output", str(where)]))
            first = where.read_bytes()
            self.assertEqual(2, review.main(["catalog", "--output", str(where)]))
            self.assertEqual(first, where.read_bytes())
            choices = json.loads(where.read_text(encoding="utf-8"))
            self.assertEqual(self.template["catalog_sha256"], choices["catalog_sha256"])
            self.assertFalse(any("expected" in row or "query" in row
                                 for row in choices["skills"]))
            self.assertEqual(2, review.main(["catalog", "--packet", str(where)]))

    def test_blinded_packet_never_contains_original_expected_labels(self):
        packet = self.template
        self.assertEqual(38, len(packet["cases"]))
        self.assertEqual("PENDING_HUMAN_REVIEW", packet["review_status"])
        self.assertEqual("REVIEWER_DECLARATION_NOT_VERIFIED", packet["independence"])
        for row in packet["cases"]:
            self.assertEqual("PENDING", row["decision"])
            self.assertEqual([], row["proposed_targets"])
            self.assertEqual([], row["proposed_avoid_top1"])
            self.assertNotIn("expected", row)
            self.assertNotIn("avoid_top1", row)
            self.assertNotIn("candidates", row)
        self.assertNotIn("model", self.template["cases"][0]["query"].lower())

    def test_unchanged_review_template_is_not_false_approval(self):
        report = review.audit(ROOT, HOLDOUT, copy.deepcopy(self.template))
        self.assertEqual(38, report["pending"])
        self.assertEqual(0, report["accepted"])
        self.assertEqual(0, report["disagreement"])
        self.assertEqual("REVIEW_INCOMPLETE", report["status"])
        self.assertEqual("NOT_VERIFIED", report["reviewer_independence"])
        self.assertFalse(report["ready_for_independent_accuracy_claim"])

    def test_declared_review_reports_agreement_and_disagreement(self):
        packet = copy.deepcopy(self.template)
        first = packet["cases"][0]
        first["decision"] = "ACCEPT"
        first["reviewer_id"] = "human-reviewer-A"
        first["rationale"] = "State updates are a directly relevant technical concern."
        first["proposed_targets"] = ["state-management"]
        second = packet["cases"][1]
        second["decision"] = "ACCEPT"
        second["reviewer_id"] = "human-reviewer-B"
        second["rationale"] = "Keyboard accessibility is the direct request."
        second["proposed_targets"] = ["accessibility-testing"]
        report = review.audit(ROOT, HOLDOUT, packet)
        self.assertEqual(2, report["accepted"])
        self.assertEqual(1, report["agreement"])
        self.assertEqual(1, report["disagreement"])
        self.assertEqual("h01", report["disagreements"][0]["id"])
        self.assertEqual(36, report["pending"])
        self.assertFalse(report["ready_for_independent_accuracy_claim"])

    def test_pending_and_challenged_ids_are_visible_without_labels(self):
        packet = copy.deepcopy(self.template)
        # A declared challenge gives rationale, not replacement expected labels.
        row = packet["cases"][3]
        row.update({
            "decision": "CHALLENGE",
            "reviewer_id": "self-declared-reviewer",
            "rationale": "Several distinct security roles could reasonably apply.",
        })
        report = review.audit(ROOT, HOLDOUT, packet)
        self.assertEqual(37, report["pending"])
        self.assertEqual(1, report["challenged"])
        self.assertEqual(["h04"], report["challenged_case_ids"])
        self.assertEqual([item["id"] for item in packet["cases"] if item["id"] != "h04"],
                         report["pending_case_ids"])
        self.assertFalse(report["ready_for_independent_accuracy_claim"])
        self.assertNotIn("reference_targets", str(report["challenged_case_ids"]))
        self.assertNotIn("proposed_targets", str(report["pending_case_ids"]))
        # Review progress IDs must remain deterministic and never include gold labels.
        self.assertEqual(report["pending_case_ids"],
                         review.audit(ROOT, HOLDOUT, packet)["pending_case_ids"])

    def test_negative_review_requires_explicit_avoided_skill(self):
        packet = copy.deepcopy(self.template)
        row = next(item for item in packet["cases"] if item["kind"] == "negative")
        row.update({
            "decision": "ACCEPT",
            "reviewer_id": "declared-reviewer",
            "rationale": "An explicit negation excludes an unrelated task.",
            "proposed_targets": ["clear-voice"],
        })
        with self.assertRaisesRegex(RoutingInputError, "requires independent target"):
            review.audit(ROOT, HOLDOUT, packet)
        row["proposed_avoid_top1"] = ["seo-audit"]
        report = review.audit(ROOT, HOLDOUT, packet)
        self.assertEqual(1, report["accepted"])

    def test_rejects_tampering_duplicate_order_and_stale_sha(self):
        tampered = copy.deepcopy(self.template)
        tampered["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(RoutingInputError, "source digest"):
            review.audit(ROOT, HOLDOUT, tampered)
        swapped = copy.deepcopy(self.template)
        swapped["cases"][:2] = swapped["cases"][1::-1]
        with self.assertRaisesRegex(RoutingInputError, "reordered"):
            review.audit(ROOT, HOLDOUT, swapped)
        extra = copy.deepcopy(self.template)
        extra["cases"][0]["predicted_skill"] = "seo-audit"
        with self.assertRaisesRegex(RoutingInputError, "modified review case"):
            review.audit(ROOT, HOLDOUT, extra)

    def test_rejects_fabricated_review_without_rationale(self):
        packet = copy.deepcopy(self.template)
        row = packet["cases"][1]
        row.update({"decision": "ACCEPT", "reviewer_id": "claimed-person",
                    "proposed_targets": ["accessibility-testing"]})
        with self.assertRaisesRegex(RoutingInputError, "requires reviewer and rationale"):
            review.audit(ROOT, HOLDOUT, packet)
        row["rationale"] = "A detailed reason, but no clearance to claim independence."
        packet["review_status"] = "REVIEWER_DECLARED_COMPLETE"
        with self.assertRaisesRegex(RoutingInputError, "Incorrect review_status"):
            review.audit(ROOT, HOLDOUT, packet)

    def test_prepare_cli_never_overwrites_existing_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            destination = Path(folder) / "human-review.json"
            rc = review.main(["prepare", "--output", str(destination)])
            self.assertEqual(0, rc)
            before = destination.read_bytes()
            rc = review.main(["prepare", "--output", str(destination)])
            self.assertEqual(2, rc)
            self.assertEqual(before, destination.read_bytes())
            packet = json.loads(destination.read_text(encoding="utf-8"))
            audit_path = Path(folder) / "review-report.json"
            rc = review.main(["audit", "--packet", str(destination),
                              "--output", str(audit_path)])
            self.assertEqual(0, rc)
            result = json.loads(audit_path.read_text(encoding="utf-8"))
            self.assertEqual("REVIEW_INCOMPLETE", result["status"])


if __name__ == "__main__":
    unittest.main()
