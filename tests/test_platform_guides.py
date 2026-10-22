"""Offline bilingual platform guide contracts; no real AI client or paid API."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OS = ("WINDOWS", "LINUX", "MACOS")


class PlatformGuidesTests(unittest.TestCase):
    def test_each_platform_has_both_languages_and_update_guides(self) -> None:
        for suffix in (*("INSTALL_" + item + ".md" for item in OS), "UPDATING.md"):
            with self.subTest(suffix=suffix):
                english = ROOT / "docs" / suffix
                russian = ROOT / "docs" / "ru" / suffix
                self.assertTrue(english.is_file())
                self.assertTrue(russian.is_file())
                self.assertIn(suffix, english.read_text(encoding="utf-8"))
                self.assertIn(suffix, russian.read_text(encoding="utf-8"))

    def test_safe_preview_before_apply_and_explicit_python(self) -> None:
        for platform in OS:
            for prefix in ("docs", "docs/ru"):
                with self.subTest(platform=platform, prefix=prefix):
                    body = (ROOT / prefix / ("INSTALL_" + platform + ".md")).read_text(encoding="utf-8")
                    command = "py -3.12" if platform == "WINDOWS" else "python3.12"
                    self.assertIn(command + " --version", body)
                    self.assertIn("--layout codex --profile general", body)
                    self.assertIn("--apply", body)
                    self.assertIn("UPDATING.md", body)
                    self.assertLess(body.index("--profile general\n"), body.index("--profile general --apply"))

    def test_readmes_and_ci_link_real_guides(self) -> None:
        en = (ROOT / "README.md").read_text(encoding="utf-8")
        ru = (ROOT / "README.ru.md").read_text(encoding="utf-8")
        workflow = (ROOT / ".github/workflows/validate.yml").read_text(encoding="utf-8")
        for suffix in (*("INSTALL_" + item + ".md" for item in OS), "UPDATING.md"):
            self.assertIn("docs/" + suffix, en)
            self.assertIn("docs/ru/" + suffix, ru)
        for label in ("macos-15", "macos-15-intel", "test_skill_manager.py", "test_adt_cli.py"):
            self.assertIn(label, workflow)
        self.assertNotIn("macos-15-large", workflow)

    def test_mcp_has_read_only_local_scope_not_unattended_update(self) -> None:
        self.assertIn("local MCP installer", (ROOT / "docs/UPDATING.md").read_text(encoding="utf-8"))
        self.assertIn("локальный установщик MCP", (ROOT / "docs/ru/UPDATING.md").read_text(encoding="utf-8"))
        self.assertIn("read-only", (ROOT / "docs/MCP_INSTALL.md").read_text(encoding="utf-8"))
        self.assertIn("только чтение", (ROOT / "docs/ru/MCP_INSTALL.md").read_text(encoding="utf-8"))
        for file in ("docs/UPDATING.md", "docs/ru/UPDATING.md"):
            body = (ROOT / file).read_text(encoding="utf-8")
            self.assertIn("chatgpt_personal_live", body)


if __name__ == "__main__":
    unittest.main()
