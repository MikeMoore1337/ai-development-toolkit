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
                self.assertIn("(docs/visuals/hero-evidence.svg)", text)
                self.assertIn(f"({beginner})", text)
                self.assertIn(f"({agent})", text)
                self.assertIn("releases/latest", text)
                candidate = ("Next release candidate" in text or
                             "Кандидат следующего релиза" in text)
                if candidate:
                    major, minor, patch = (int(p) for p in version.split("."))
                    self.assertGreater(patch, 0)
                    prior = f"{major}.{minor}.{patch - 1}"
                    self.assertIn(f"/releases/tag/v{prior}", text)
                    self.assertIn(f"`v{version}`", text)
                    self.assertIn("NOT PUBLISHED" if name == "README.md"
                                  else "НЕ ОПУБЛИКОВАН", text)
                    self.assertNotIn(f"/releases/tag/v{version}", text)
                else:
                    self.assertIn(f"/releases/tag/v{version}", text)
                    self.assertNotRegex(
                        text, r"(?:NOT PUBLISHED|НЕ ОПУБЛИКОВАН|Next release candidate|"
                        r"Кандидат следующего релиза)"
                    )
                self.assertIn("README.ru.md" if name == "README.md" else "README.md", text)

    def test_release_documents_match_published_manifest(self) -> None:
        """Offline current-release copy contract, not live GitHub evidence."""
        version = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))["version"]
        is_candidate = "**Next release candidate:**" in (
            ROOT / "README.md").read_text(encoding="utf-8")
        if is_candidate:
            major, minor, patch = (int(p) for p in version.split("."))
            self.assertGreater(patch, 0)
            published_version = f"{major}.{minor}.{patch - 1}"
        else:
            published_version = version
        sources = (
            ("README.md", "**Latest published release:**"),
            ("README.ru.md", "**Последний опубликованный релиз:**"),
            ("docs/RELEASE_PROCESS.md", "Last published tag:"),
            ("docs/ru/RELEASE_PROCESS.md", "Последний публичный тег:"),
        )
        for path, prefix in sources:
            with self.subTest(path=path):
                lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
                status = [line for line in lines if line.startswith(prefix)]
                self.assertEqual(len(status), 1, "Missing or duplicate latest-release marker")
                self.assertIn(f"[v{published_version}]", status[0])
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"## {version} ({'candidate' if is_candidate else 'released'},", changelog)
        if not is_candidate:
            self.assertIn(f"v{version} publication confirmed", changelog)

    def test_release_status_negative_fixture_detects_stale_version(self) -> None:
        """A stale current-release declaration cannot pass the same exact match."""
        expected = "[v5.5.4]"
        stale = "Last published tag: [v5.5.3]"
        self.assertNotIn(expected, stale)
        self.assertIn(expected, "Last published tag: [v5.5.4]")

    def test_vector_assets_are_local_and_without_dynamic_counts(self) -> None:
        for name, dimensions in (
            ("docs/visuals/hero-evidence.svg", ("1440", "690")),
            ("docs/visuals/social-preview-proposal.svg", ("1280", "640")),
        ):
            with self.subTest(name=name):
                path = ROOT / name
                text = path.read_text(encoding="utf-8")
                root = ET.fromstring(text)
                self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
                self.assertEqual((root.attrib["width"], root.attrib["height"]), dimensions)
                self.assertNotIn("<script", text.lower())
                self.assertNotRegex(text, r"(?i)\b(?:\d+\s+skills|\d+\s+profiles)\b")

    def test_documented_local_links_exist(self) -> None:
        for name in ("README.md", "README.ru.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            for link in re.findall(r"(?<!!)\[[^\]\n]+\]\(([^)]+)\)", text):
                path = link.split("#", 1)[0]
                if not path or path.startswith(("https://", "http://")):
                    continue
                with self.subTest(name=name, link=link):
                    self.assertTrue((ROOT / path).is_file(), path)


if __name__ == "__main__":
    unittest.main()
