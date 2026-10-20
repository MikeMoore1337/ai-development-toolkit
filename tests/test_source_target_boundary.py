"""Issue #103: source-vs-target boundary contract for third-party Toolkit use.

These tests validate documented routing, not real autonomous Codex behavior.
Toolkit is a read-only source when assisting project A; A owns requested outputs.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SourceTargetBoundaryTests(unittest.TestCase):
    def test_single_natural_language_request_is_primary_ru_en(self):
        for guide, primary, optional in (
            ("AGENT_START.ru.md", "## Основной сценарий:",
             "## Дополнительный сценарий:"),
            ("AGENT_START.md", "## Primary path:",
             "## Optional path:"),
        ):
            content = (ROOT / guide).read_text(encoding="utf-8")
            self.assertIn(primary, content)
            text = content.split(primary, 1)[1].split(optional, 1)[0]
            self.assertIn("https://github.com/MikeMoore1337/ai-development-toolkit", text)
            self.assertIn("Codex", text)
            self.assertNotIn("https://github.com/OWNER/PROJECT", text)
            self.assertNotIn("adt.py init", text)
            self.assertNotIn("--apply", text)

    def test_upstream_source_must_not_receive_third_party_outputs(self):
        policies = {
            "AGENTS.md": ("read-only source", "reports", "project A"),
            "AGENT_START.md": ("**Toolkit source", "reports", "commits",
                               "**User's project A", "A's `reports/`"),
            "AGENT_START.ru.md": ("**Источник", "отчёты", "коммиты",
                                  "**Рабочая область", "`reports/`"),
        }
        for name, markers in policies.items():
            content = (ROOT / name).read_text(encoding="utf-8")
            for marker in markers:
                with self.subTest(name=name, marker=marker):
                    self.assertIn(marker, content)
        self.assertIn("**never be placed in AI Development Toolkit**",
                      (ROOT / "AGENT_START.md").read_text(encoding="utf-8"))
        self.assertIn("не должны попадать в AI Development Toolkit",
                      (ROOT / "AGENT_START.ru.md").read_text(encoding="utf-8"))

    def test_no_blanket_ban_on_outputs_in_project_a(self):
        en = (ROOT / "AGENT_START.md").read_text(encoding="utf-8")
        ru = (ROOT / "AGENT_START.ru.md").read_text(encoding="utf-8")
        self.assertIn("If the user requests a report inside project A", en)
        self.assertIn("Если пользователь просит файл в **проекте A**", ru)
        for content in (en, ru):
            self.assertIn("GUIDANCE_ONLY", content)
            self.assertIn("NOT_VERIFIED", content)
            self.assertIn("READ_ONLY", content)

    def test_optional_install_targets_separate_disposable_project_not_toolkit(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "project-a"
            target.mkdir()
            evidence_paths = [ROOT / "AGENTS.md", ROOT / "AGENT_START.md",
                              ROOT / "AGENT_START.ru.md", ROOT / "MANIFEST.json"]
            before = {p.name: p.read_bytes() for p in evidence_paths}
            command = [sys.executable, str(ROOT / "scripts/adt.py"),
                       "--json", "init", "--target", str(target),
                       "--profile", "general", "--apply"]
            run = subprocess.run(command, cwd=ROOT, text=True,
                                 capture_output=True, timeout=60, check=False)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(json.loads(run.stdout)["applied"])
            self.assertTrue((target / ".agents" / "skills").is_dir())
            self.assertEqual(before, {p.name: p.read_bytes() for p in evidence_paths})


if __name__ == "__main__":
    unittest.main()
