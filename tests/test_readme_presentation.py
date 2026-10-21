"""Offline checks for README navigation and evidence-first artwork.

These tests validate repository files, not GitHub's live social-preview setting
or the effectiveness of an AI agent.
"""
from __future__ import annotations

import json
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReadmePresentationTests(unittest.TestCase):
    def test_both_readmes_link_to_artwork_and_guides(self) -> None:
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        version = manifest["version"]
        for name, beginner, agent in (
            ("README.md", "docs/BEGINNER_START.md", "AGENT_START.md"),
            ("README.ru.md", "docs/ru/BEGINNER_START.md", "AGENT_START.ru.md"),
        ):
            with self.subTest(name=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                self.assertIn("(assets/branding/hero-v2.svg)", text)
                self.assertIn(f"({beginner})", text)
                self.assertIn(f"({agent})", text)
                self.assertIn(f"/releases/tag/v{version}", text)
                self.assertIn("releases/latest", text)
                self.assertNotRegex(
                    text, r"(?:NOT PUBLISHED|НЕ ОПУБЛИКОВАН|Next release candidate|"
                    r"Кандидат следующего релиза)"
                )
                self.assertIn("README.ru.md" if name == "README.md" else "README.md", text)

    def test_vector_assets_are_local_and_without_dynamic_counts(self) -> None:
        for name, dimensions in (
            ("assets/branding/hero-v2.svg", ("1440", "690")),
            ("assets/branding/social-preview-v2.svg", ("1280", "640")),
        ):
            with self.subTest(name=name):
                path = ROOT / name
                text = path.read_text(encoding="utf-8")
                root = ET.fromstring(text)
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertEqual((root.attrib["width"], root.attrib["height"]), dimensions)
                self.assertNotIn("<script", text.lower())
                self.assertNotRegex(text, r"(?i)\\b(?:\\d+\\s+skills|\\d+\\s+profiles)\\b")
                self.assertNotIn("http://", text)
                self.assertNotIn("https://", text)

    def test_documented_local_links_exist(self) -> None:
        for name in ("README.md", "README.ru.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            for link in re.findall(r"(?<!!)\\[[^\\]\\n]+\\]\\(([^)]+)\\)", text):
                path = link.split("#", 1)[0]
                if not path or path.startswith(("https://", "http://")):
                    continue
                with self.subTest(name=name, link=link):
                    self.assertTrue((ROOT / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
