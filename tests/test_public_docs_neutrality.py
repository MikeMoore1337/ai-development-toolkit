"""Offline regressions for public Markdown neutrality (#259)."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.validate_public_docs_neutrality import audit


class PublicDocsNeutralityTests(unittest.TestCase):
    def test_allows_real_upstream_clients_and_toolkit_repository(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "README.md").write_text(
                "Hermes Agent (NousResearch/hermes-agent); Codex; Claude Code; "
                "MikeMoore1337/ai-development-toolkit; generic agent service\n",
                encoding="utf-8",
            )
            self.assertEqual(audit(root), [])

    def test_detects_names_urls_across_nested_docs(self) -> None:
        samples = (
            "YFC", "your-fitness-coach", "Hermes Control Center",
            "Hermes BRC", "hermes-agent-owner", "MikeMoore1337/hermes",
            "Ops Watch", "Research Scout", "second-brain", "Second Brain",
            "Night Shift", "mcp.mikemoore.top",
        )
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "docs").mkdir()
            (root / "docs" / "example.md").write_text(
                "\n".join(samples) + "\n", encoding="utf-8",
            )
            findings = audit(root)
            self.assertEqual(len(findings), len(samples))
            self.assertEqual([x["line"] for x in findings], list(range(1, len(samples) + 1)))

    def test_does_not_match_inside_unrelated_identifiers(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "a.md").write_text(
                "MYFCONTRACTS second_brainstorming hermes-agent external tool\n",
                encoding="utf-8",
            )
            self.assertEqual(audit(root), [])

    def test_ignores_only_disposable_directories(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / ".git").mkdir()
            (root / ".git" / "old.md").write_text("YFC", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "a.md").write_text("YFC", encoding="utf-8")
            findings = audit(root)
            self.assertEqual(len(findings), 1)
            self.assertEqual(findings[0]["file"], "docs/a.md")

    def test_links_and_code_blocks_are_not_blind_spots(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "README.md").write_text(
                "See [private](https://github.com/MikeMoore1337/hermes)\n"
                "~~~text\nSecond Brain\n~~~\n",
                encoding="utf-8",
            )
            self.assertEqual(len(audit(root)), 2)

    def test_unreadable_utf8_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "bad.md").write_bytes(b"\xff\xfe")
            self.assertEqual(audit(root)[0]["token"], "UNREADABLE")


if __name__ == "__main__":
    unittest.main()
