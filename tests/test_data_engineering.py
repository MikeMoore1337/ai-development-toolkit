"""Offline contract, recovery and independent negative-oracle regressions for Issue #65."""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_data_engineering import (PipelineError, aggregate, audit, build,
                                       empty_state, ingest, load, mutate, partition_batch, validate)


class DataEngineeringTests(unittest.TestCase):
    def test_correct_reference_and_separate_metric_oracle(self):
        sample = build()
        expected = load("events.json")["expected"]
        self.assertEqual([], audit(sample))
        self.assertEqual(expected["totals"], sample["report"]["totals"])
        self.assertEqual(expected["purchase_fraction"], sample["report"]["purchase_fraction"])
        self.assertEqual(3, sample["state"]["checkpoint"])
        self.assertEqual(6, len(sample["state"]["lineage"]))

    def test_incremental_failure_and_replay(self):
        source, contract = load("events.json"), load("contracts.json")
        state = empty_state()
        for batch in source["batches"]:
            unchanged = copy.deepcopy(state)
            with self.assertRaisesRegex(PipelineError, "INJECTED_INTERRUPTION"):
                ingest(state, batch, source, contract, interrupt=True)
            self.assertEqual(unchanged, state)
            state = ingest(state, batch, source, contract)
            self.assertEqual(state, ingest(state, batch, source, contract))
        self.assertEqual("2026-10-20T12:00:00+00:00", state["watermark"])
        self.assertEqual(source["expected"]["totals"], aggregate(state)["totals"])

    def test_conflicting_replay_is_rejected(self):
        source, contract = load("events.json"), load("contracts.json")
        first = source["batches"][0]
        state = ingest(empty_state(), first, source, contract)
        changed = copy.deepcopy(first)
        changed["records"][0]["amount"] += 1
        with self.assertRaisesRegex(PipelineError, "CONFLICTING_REPLAY"):
            ingest(state, changed, source, contract)

    def test_gap_and_invalid_range_cannot_change_checkpoint(self):
        source, contract = load("events.json"), load("contracts.json")
        with self.assertRaisesRegex(PipelineError, "MISSING_BATCH"):
            ingest(empty_state(), source["batches"][1], source, contract)
        batch = copy.deepcopy(source["batches"][0])
        batch["records"][0]["amount"] = -9
        state = empty_state()
        with self.assertRaisesRegex(PipelineError, "RANGE"):
            ingest(state, batch, source, contract)
        self.assertEqual(empty_state(), state)

    def test_all_25_broken_cases_detected_by_same_oracle(self):
        sample = build()
        self.assertEqual([], audit(sample))
        cases = load("broken_cases.json")["cases"]
        self.assertEqual(25, len(cases))
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertIn(case["expected_error"],
                              audit(mutate(sample, case["path"], case["value"])))

    def test_reject_invalid_rows_before_aggregate_and_require_external_accuracy(self):
        source, contract = load("events.json"), load("contracts.json")
        batch = copy.deepcopy(source["batches"][0])
        bad = copy.deepcopy(batch["records"][0])
        bad["event_id"] = "invalid-new-event"
        bad["amount"] = -99
        batch["records"].append(bad)
        accepted, rejected = partition_batch(batch, contract)
        self.assertEqual(2, len(accepted["records"]))
        self.assertEqual(1, len(rejected))
        self.assertIn("RANGE", rejected[0]["issues"])
        state = ingest(empty_state(), accepted, source, contract)
        self.assertEqual({"view": 1, "purchase": 5}, aggregate(state)["totals"])
        self.assertEqual("NOT_VERIFIED", aggregate(state)["accuracy"])
        self.assertFalse(aggregate(state)["oracle_verified"])
        self.assertEqual("PASS", build()["report"]["accuracy"])

    def test_zero_denominator_does_not_divide(self):
        self.assertEqual(0, aggregate(empty_state())["denominator"])
        self.assertIsNone(aggregate(empty_state())["purchase_fraction"])

    def test_full_validation_entry(self):
        self.assertEqual((1, 25), validate())


if __name__ == "__main__":
    unittest.main()
