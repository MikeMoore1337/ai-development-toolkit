"""QA Orchestra truthfulness: synthetic declarations, not live subagent tests."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate_qa_orchestration as qa


class QAOrchestraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads((ROOT / "fixtures/qa_orchestra_valid.json").read_text(encoding="utf-8"))

    def case(self):
        return copy.deepcopy(self.example)

    def reject(self, text, case):
        self.assertTrue(any(text in problem for problem in qa.validate_report(case)),
                        qa.validate_report(case))

    def test_valid_bounded_sequential_audit(self):
        self.assertEqual([], qa.validate_report(self.case()))

    def test_audit_cannot_write(self):
        case = self.case()
        case["changed_code"] = True
        self.reject("code changes", case)

    def test_sequential_not_parallel(self):
        case = self.case()
        case["execution"]["peak"] = 3
        self.reject("peak 1", case)

    def test_no_imaginary_workers(self):
        case = self.case()
        case["streams"][0]["execution"] = "ACTUAL_SUBAGENT"
        self.reject("sequential plan", case)
        self.reject("missing actual trace", case)

    def test_subagent_trace_is_mandatory(self):
        case = self.case()
        case["execution"] = {"mode": "SUBAGENTS", "peak": 2}
        for stream in case["streams"]:
            stream["execution"] = "GENERIC_SUBAGENT"
        self.reject("missing actual trace", case)

    def test_subagent_trace_declaration_is_valid_not_independently_proven(self):
        case = self.case()
        case["execution"] = {"mode": "SUBAGENTS", "peak": 2}
        for i, stream in enumerate(case["streams"]):
            stream["execution"] = "GENERIC_SUBAGENT"
            stream["trace"] = f"tool-call-record-{i}"
        self.assertEqual([], qa.validate_report(case))

    def test_pass_without_executed_test_rejected(self):
        case = self.case()
        case["checks"][0]["status"] = "PASS"
        self.reject("requires execution evidence", case)

    def test_fake_green_gate_rejected(self):
        case = self.case()
        case["gate"] = "READY_FOR_REVIEW"
        self.reject("false ready", case)

    def test_missing_required_check_rejected(self):
        case = self.case()
        case["required_check_ids"].append("not-listed")
        self.reject("missing required", case)

    def test_mismatched_revision_rejected(self):
        case = self.case()
        case["evidence"][0]["revision"] = "f" * 40
        self.reject("mismatched", case)

    def test_duplicate_stream_rejected(self):
        case = self.case()
        case["streams"][1]["id"] = "api"
        self.reject("duplicate", case)

    def test_unknown_evidence_rejected(self):
        case = self.case()
        case["checks"][0]["evidence_ids"] = ["imaginary"]
        self.reject("unknown evidence", case)

    def test_fail_cannot_be_downgraded_to_unknown(self):
        case = self.case()
        case["checks"][0]["status"] = "FAIL"
        self.reject("cannot be hidden", case)

    def test_true_recorded_pass_can_be_ready_for_review(self):
        case = self.case()
        case["evidence"][0]["kind"] = "TEST_RUN"
        case["evidence"][0]["reference"] = "CI run #12345 - example; not actual evidence"
        for check in case["checks"]:
            check["status"] = "PASS"
            check["evidence_ids"] = ["source1"]
        case["gate"] = "READY_FOR_REVIEW"
        self.assertEqual([], qa.validate_report(case))


if __name__ == "__main__":
    unittest.main()
