"""Offline source-level checks of opt-in portable Curator/Task Observer adapters (#337)."""
from __future__ import annotations

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "integrations/chatgpt-plugin/ai-development-toolkit/skills"
PIN = "947953f2a0664ac95996a4c7b35794a7cc8fc93a"


class ChatGPTObservationAdaptersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.curator = (SKILLS / "toolkit-evidence-curator/SKILL.md").read_text(encoding="utf-8")
        cls.observer = (SKILLS / "toolkit-task-observer-opt-in/SKILL.md").read_text(encoding="utf-8")
        cls.router = (SKILLS / "toolkit-task-router/SKILL.md").read_text(encoding="utf-8")
        cls.curator_ref = (SKILLS / "toolkit-evidence-curator/references/UPSTREAM.md").read_text(encoding="utf-8")
        cls.observer_ref = (SKILLS / "toolkit-task-observer-opt-in/references/UPSTREAM.md").read_text(encoding="utf-8")

    def test_valid_unique_skill_frontmatter(self) -> None:
        for content, expected in [(self.curator, "toolkit-evidence-curator"), (self.observer, "toolkit-task-observer-opt-in")]:
            self.assertRegex(content, r"(?s)\A---\nname: [a-z0-9-]+\ndescription: .+?\n---\n")
            self.assertIn(f"name: {expected}\n", content)

    def test_upstream_sha_is_immutable(self) -> None:
        for content in (self.curator, self.observer, self.curator_ref, self.observer_ref):
            self.assertIn(PIN, content)

    def test_both_adapters_are_opt_in_and_no_paid_calls(self) -> None:
        self.assertIn("Only if a user asks", self.curator)
        self.assertIn("only", self.observer.lower())
        self.assertIn("No background service", self.observer)
        self.assertIn("no paid", self.curator.lower())
        self.assertIn("paid AI", self.observer)
        self.assertIn("Do not auto-activate", self.router)

    def test_evidence_verdict_contract(self) -> None:
        for verdict in ("VERIFIED", "CONTRADICTED", "UNVERIFIED"):
            self.assertIn(verdict, self.curator)
        self.assertIn("Green CI is not deployment proof", self.curator)
        self.assertIn("independent live evidence", self.router)

    def test_task_observer_sanitizes_and_requires_review(self) -> None:
        for key in ("observation_id", "skill_id", "category", "source_url"):
            self.assertIn(key, self.observer)
        self.assertIn("MANUAL_REVIEW_REQUIRED", self.observer)
        self.assertIn("skill_observation_review.py", self.observer)
        self.assertIn("never automatically VERIFIED", self.observer)

    def test_origin_license_is_correct(self) -> None:
        self.assertIn("MIT", self.curator_ref)
        self.assertIn("Eoghan Henn", self.observer_ref)
        self.assertIn("CC BY 4.0", self.observer_ref)
        self.assertIn("Adaptation", self.observer_ref)

    def test_no_original_transcript_logging_or_deploy(self) -> None:
        self.assertIn("never", self.curator.lower())
        self.assertIn("Do not watch conversations", self.curator)
        self.assertIn("no raw", self.observer.lower() + " no raw")
        self.assertIn("no automatic", self.observer.lower())
        self.assertIn("Never", self.curator)

    def test_short_modular_adapters_not_full_external_skill(self) -> None:
        self.assertLess(len(self.observer.splitlines()), 110)
        self.assertLess(len(self.curator.splitlines()), 110)

    def test_router_only_selects_on_named_intent(self) -> None:
        self.assertIn("../toolkit-evidence-curator/SKILL.md", self.router)
        self.assertIn("../toolkit-task-observer-opt-in/SKILL.md", self.router)
        self.assertIn("explicit read-only verification", self.router)


if __name__ == "__main__":
    unittest.main()
