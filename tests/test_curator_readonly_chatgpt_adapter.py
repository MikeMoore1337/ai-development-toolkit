"""Offline contract: QA Curator adapter is opt-in, source-pinned and read-only.

These are static negative/positive checks, NOT an agent/client activation.
"""
from __future__ import annotations

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "integrations/chatgpt-plugin/ai-development-toolkit/skills/toolkit-qa-review/SKILL.md"
EXPECTED_SHA = "947953f2a0664ac95996a4c7b35794a7cc8fc93a"


class ReadOnlyCuratorAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.content = SKILL.read_text(encoding="utf-8")

    def test_existing_entrypoint_preserved(self) -> None:
        self.assertIn("name: toolkit-qa-review", self.content)
        self.assertIn("toolkit-task-router", self.content)
        self.assertIn("quality-gate-assessment", self.content)

    def test_pins_real_upstream_and_license_boundaries(self) -> None:
        self.assertIn(EXPECTED_SHA, self.content)
        self.assertIn("skills/curate/SKILL.md", self.content)
        self.assertIn("agents/curator.md", self.content)
        self.assertIn("MIT license", self.content)
        self.assertIn("Eoghan Henn", self.content)
        self.assertIn("CC BY 4.0", self.content)

    def test_no_paid_or_codex_cli_invocations(self) -> None:
        self.assertIn("Never use Codex CLI", self.content)
        self.assertIn("paid model providers", self.content)
        self.assertIn("not an installation or execution", self.content)

    def test_factual_evidence_verdicts_are_fail_closed(self) -> None:
        for token in ("VERIFIED", "CONTRADICTED", "UNVERIFIED", "PRODUCTION_DEPLOYED"):
            with self.subTest(token=token):
                self.assertIn(token, self.content)
        self.assertIn("read-only", self.content)
        self.assertIn("No auto-merge", self.content)

    def test_observer_keeps_privacy_and_manual_review(self) -> None:
        for token in ("skill_observation_review.py", "MANUAL_REVIEW_REQUIRED",
                      "NO_AUTO_INSTALL", "no raw transcript", "auto-schedule"):
            with self.subTest(token=token):
                self.assertIn(token.lower(), self.content.lower())

    def test_no_unverified_compatibility_claim(self) -> None:
        self.assertIn("client activation needs direct evidence", self.content)
        self.assertIn("REFERENCE_ONLY", self.content)


if __name__ == "__main__":
    unittest.main()
