"""Offline contract for universal URL-based agent onboarding (#95).

This checks actual managed CLI behavior in disposable target folders, not a live
Codex/Claude session, URL retrieval or empirical model effectiveness.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EN = ROOT / "AGENT_START.md"
RU = ROOT / "AGENT_START.ru.md"
MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts/adt.py"), "--json", *arguments],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=40,
        check=False,
    )


class UniversalAgentEntryTests(unittest.TestCase):
    def test_source_and_target_are_explicit_for_both_languages(self):
        for guide in (EN, RU):
            text = guide.read_text(encoding="utf-8")
            self.assertIn("https://github.com/MikeMoore1337/ai-development-toolkit", text)
            self.assertIn("https://github.com/OWNER/PROJECT", text)
            self.assertIn("AGENTS.md", text)
            self.assertIn("CLAUDE.md", text)
            self.assertIn("MANIFEST.json", text)
            self.assertIn("docs/INSTALLATION.md", text)
            self.assertIn("AGENT_START", text)

    def test_one_entry_link_in_each_main_readme(self):
        self.assertIn("(AGENT_START.md)", (ROOT / "README.md").read_text(encoding="utf-8"))
        self.assertIn("(AGENT_START.ru.md)", (ROOT / "README.ru.md").read_text(encoding="utf-8"))
        self.assertIn("(AGENT_START.ru.md)", EN.read_text(encoding="utf-8"))
        self.assertIn("(AGENT_START.md)", RU.read_text(encoding="utf-8"))

    def test_existing_profile_and_client_layout_contract(self):
        for name in ("general", "codex-feature", "qa-security", "ui-fix", "frontend",
                     "backend", "fullstack", "qa-core", "make-feature"):
            self.assertIn(name, MANIFEST["profiles"])
        for guide in (EN, RU):
            text = guide.read_text(encoding="utf-8")
            for token in ("--task feature", "--apply", "--layout claude",
                          "feature-delivery", "make-feature", "qa-all",
                          "NOT_TESTED", "NOT_RUN", "BLOCKED"):
                self.assertIn(token, text)

    def test_profile_preview_is_read_only_and_task_driven(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            before = list(target.rglob("*"))
            result = run_cli("profile", "plan", "--target", directory, "--task", "feature")
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["selection"]["profile"], "codex-feature")
            self.assertFalse(report["applied"])
            self.assertIn(report["result"], ("PREVIEW", "REVIEW_REQUIRED"))
            self.assertEqual(before, list(target.rglob("*")))

    def test_unmanaged_skill_is_not_overwritten_even_on_apply(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / ".agents" / "skills" / "task-scoping"
            folder.mkdir(parents=True)
            original = folder / "SKILL.md"
            original.write_text("user-owned; do not overwrite", encoding="utf-8")
            result = run_cli("init", "--target", directory, "--task", "feature", "--apply")
            self.assertEqual(result.returncode, 2, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["result"], "BLOCKED")
            self.assertFalse(report["applied"])
            self.assertEqual(original.read_text(encoding="utf-8"), "user-owned; do not overwrite")

    def test_repeat_install_is_idempotent_in_disposable_target(self):
        with tempfile.TemporaryDirectory() as directory:
            first = run_cli("init", "--target", directory, "--task", "feature", "--apply")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertTrue(json.loads(first.stdout)["applied"])
            second = run_cli("init", "--target", directory, "--task", "feature", "--apply")
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(json.loads(second.stdout)["result"], "ALREADY_INSTALLED")
            status = run_cli("status", "--target", directory)
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertTrue((Path(directory) / ".agents" / "skills" / "task-scoping" / "SKILL.md").is_file())

    def test_does_not_claim_runtime_activation(self):
        for guide in (EN, RU):
            text = guide.read_text(encoding="utf-8")
            self.assertIn("NOT_TESTED", text)
            self.assertIn("NOT_VERIFIED", text)
            self.assertIn("Python 3.12+", text)
            self.assertIn("ChatGPT", text)
            self.assertIn("Claude Code", text)


if __name__ == "__main__":
    unittest.main()
