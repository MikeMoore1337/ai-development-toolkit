"""Issue #103: source-vs-target boundary contract for third-party Toolkit use.

These tests validate documented routing, not real autonomous Codex behavior.
Toolkit is read-only guidance for user work; generated results belong to the user's project.
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
            "AGENTS.md": ("read-only sources", "reports", "user\'s project"),
            "AGENT_START.md": ("**Toolkit is a read-only source", "reports", "commits",
                               "**The user\'s project is the work target", "`reports/`"),
            "AGENT_START.ru.md": ("**Toolkit - источник", "отчёты", "коммиты",
                                  "**Проект пользователя - рабочая область", "`reports/`"),
        }
        for name, markers in policies.items():
            content = (ROOT / name).read_text(encoding="utf-8")
            for marker in markers:
                with self.subTest(name=name, marker=marker):
                    self.assertIn(marker, content)
        self.assertIn("must never be placed in the Toolkit repository",
                      (ROOT / "AGENT_START.md").read_text(encoding="utf-8"))
        self.assertIn("никогда не должны попадать в репозиторий Toolkit",
                      (ROOT / "AGENT_START.ru.md").read_text(encoding="utf-8"))

    def test_outputs_belong_to_users_project_not_toolkit(self):
        en = (ROOT / "AGENT_START.md").read_text(encoding="utf-8")
        ru = (ROOT / "AGENT_START.ru.md").read_text(encoding="utf-8")
        self.assertIn("If a report file is requested inside the user\'s project", en)
        self.assertIn("Если пользователь просит файл **в своём проекте**", ru)
        for content in (en, ru):
            self.assertIn("GUIDANCE_ONLY", content)
            self.assertIn("NOT_VERIFIED", content)
            self.assertIn("READ_ONLY", content)

    def test_public_guides_do_not_use_example_project_name_as_user_requirement(self):
        import re

        public_guides = (
            "AGENT_START.ru.md", "AGENT_START.md", "README.ru.md", "README.md",
            "docs/ru/BEGINNER_START.md", "docs/BEGINNER_START.md",
            "docs/ru/README.md",
        )
        for relpath in public_guides:
            text = (ROOT / relpath).read_text(encoding="utf-8")
            with self.subTest(path=relpath):
                self.assertIsNone(re.search(r"\b[Pp]roject A\b|проект[аеуом]* [AА]\b", text))
                self.assertIn("Toolkit", text)
        en = (ROOT / "AGENT_START.md").read_text(encoding="utf-8")
        ru = (ROOT / "AGENT_START.ru.md").read_text(encoding="utf-8")
        for content in (en, ru):
            self.assertIn("https://github.com/MikeMoore1337/ai-development-toolkit", content)
            self.assertIn("GUIDANCE_ONLY", content)
            self.assertIn("NOT_VERIFIED", content)

    def test_optional_install_targets_separate_disposable_project_not_toolkit(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sample-project"
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
