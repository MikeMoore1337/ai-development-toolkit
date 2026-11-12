"""Source-only, opt-in issue-slice and retro contract checks."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import issue_orchestrator as orchestrator  # noqa: E402


class IssueExecutionDisciplineTests(unittest.TestCase):
    def test_native_orchestrator_already_handles_blocking_edges(self):
        issue = {"body": "## Dependencies\nBlocked by: #20, #34\n\n## Outcome\nWorking notes"}
        self.assertEqual(orchestrator.dependencies(issue), {20, 34})
        self.assertEqual(orchestrator.dependencies({"body": "No blockers"}), set())
        self.assertTrue(orchestrator.is_cyclic(20, {20: {34}, 34: {20}}))
        self.assertTrue(orchestrator.is_cyclic(20, {20: {20}}))
        self.assertFalse(orchestrator.is_cyclic(20, {20: {34}, 34: set()}))

    def test_existing_single_controller_and_optional_activation(self):
        source = (ROOT / ".agents/skills/feature-delivery/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ISSUE_EXECUTION_DISCIPLINE.md", source)
        self.assertIn("Only when the owner asks", source)
        self.assertIn("no hooks", source.lower())
        self.assertIn("WIP=1", source)
        manifest = (ROOT / "MANIFEST.json").read_text(encoding="utf-8")
        self.assertIn('"native_parallel_orchestration"', manifest)
        self.assertIn('"execution_backend": "NONE"', manifest)

    def test_bilingual_guidance_and_no_unverified_telemetry_claim(self):
        english = (ROOT / "docs/ISSUE_EXECUTION_DISCIPLINE.md").read_text(encoding="utf-8")
        russian = (ROOT / "docs/ru/ISSUE_EXECUTION_DISCIPLINE.md").read_text(encoding="utf-8")
        for document in (english, russian):
            with self.subTest(language=document[:20]):
                self.assertIn("mattpocock/skills", document)
                self.assertIn("5863806dd4e15c63174bee4e7515a4256792ecfa", document)
                self.assertIn("Blocked by: #N", document)
                self.assertIn("NOT_MEASURED", document)
                self.assertIn("WIP=1", document)
                self.assertIn("retro", document)
        self.assertIn("source-only", english.lower())
        self.assertIn("не", russian)

    def test_issue_orchestrator_guide_links_without_new_executor(self):
        guide = (ROOT / "docs/ISSUE_ORCHESTRATOR.md").read_text(encoding="utf-8")
        self.assertIn("ISSUE_EXECUTION_DISCIPLINE.md", guide)
        self.assertIn("WIP=1", guide)
        self.assertIn("не изменяет очередь", guide)


if __name__ == "__main__":
    unittest.main()
