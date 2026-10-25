"""Offline acceptance tests; no Headroom installation, network, models or Codex."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

PATH = Path(__file__).resolve().parents[1] / "scripts/headroom_offline_adoption_gate.py"
SPEC = importlib.util.spec_from_file_location("headroom_gate", PATH)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def mocked(*, before: int = 1000, after: int = 900,
           lossless: bool | None = True,
           evidence: dict | None = None, raise_error: bool = False):
    def compress(messages):
        if raise_error:
            raise RuntimeError("sensitive-content-must-not-leak")
        result = deepcopy(messages)
        if evidence is not None:
            data = json.loads(result[2]["content"])
            data["evidence"] = evidence
            result[2]["content"] = json.dumps(data)
        return SimpleNamespace(messages=result, tokens_before=before,
                               tokens_after=after, lossless=lossless)
    return compress


class HeadroomOfflineAdoptionGateTests(unittest.TestCase):
    def test_synthetic_fixture_has_required_evidence(self):
        messages = gate.synthetic_messages()
        self.assertEqual(3, len(messages))
        self.assertEqual(gate.CRITICAL, json.loads(messages[2]["content"])["evidence"])
        self.assertNotIn("private", messages[2]["content"].lower())

    def test_positive_requires_both_lossless_and_savings(self):
        r = gate.evaluate(mocked())
        self.assertEqual("PILOT_ELIGIBLE", r["decision"])
        self.assertEqual(10, r["savings_pct"])
        self.assertTrue(r["critical_evidence_preserved"])
        self.assertFalse(r["user_runtime_verified"])
        self.assertEqual(0, r["model_api_calls"])
        self.assertEqual(0, r["codex_cli_calls"])

    def test_no_savings_is_no_go(self):
        r = gate.evaluate(mocked(after=1000))
        self.assertEqual("NO_GO", r["decision"])
        self.assertIn("insufficient_savings", r["reason"])

    def test_limited_savings_is_no_go(self):
        r = gate.evaluate(mocked(after=970))
        self.assertEqual("NO_GO", r["decision"])

    def test_lossy_is_no_go_even_when_evidence_remains(self):
        r = gate.evaluate(mocked(after=500, lossless=None))
        self.assertEqual("NO_GO", r["decision"])
        self.assertIn("lossless_not_proven", r["reason"])

    def test_false_lossless_is_no_go(self):
        self.assertEqual("NO_GO", gate.evaluate(mocked(lossless=False))["decision"])

    def test_denied_becomes_approved_is_no_go(self):
        bad = {**gate.CRITICAL, "approval": "APPROVED"}
        r = gate.evaluate(mocked(evidence=bad))
        self.assertEqual("NO_GO", r["decision"])
        self.assertIn("critical_evidence_not_preserved", r["reason"])

    def test_missing_sha_is_no_go(self):
        bad = {key: val for key, val in gate.CRITICAL.items() if key != "sha"}
        self.assertEqual("NO_GO", gate.evaluate(mocked(evidence=bad))["decision"])

    def test_no_input_tokens_is_no_go(self):
        self.assertEqual("invalid_measurement", gate.evaluate(mocked(before=0))["reason"])

    def test_inflation_is_no_go(self):
        self.assertEqual("invalid_measurement", gate.evaluate(mocked(after=2000))["reason"])

    def test_third_party_error_is_redacted(self):
        r = gate.evaluate(mocked(raise_error=True))
        self.assertEqual({"decision": "NO_GO", "reason": "compression_failed"}, r)
        self.assertNotIn("sensitive-content", json.dumps(r))

    def test_invalid_threshold_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_savings"):
            gate.evaluate(mocked(), minimum_savings_pct=-1)


if __name__ == "__main__":
    unittest.main()
