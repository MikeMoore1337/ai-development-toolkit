"""Issue #333: static first-use navigation regressions, not human usability tests."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BeginnerFirstUseDocsTests(unittest.TestCase):
    ROUTES = (
        ("README.ru.md", "docs/ru/BEGINNER_START.md",
         "docs/ru/EXISTING_PROJECT.md", "docs/ru/BEGINNER_CLIENT_DETAILS.md",
         "AGENT_START.ru.md", ("PASS", "FAIL", "NOT_RUN", "NOT_VERIFIED",
                               "GUIDANCE_ONLY", "BLOCKED")),
        ("README.md", "docs/BEGINNER_START.md",
         "docs/EXISTING_PROJECT.md", "docs/BEGINNER_CLIENT_DETAILS.md",
         "AGENT_START.md", ("PASS", "FAIL", "NOT_RUN", "NOT_VERIFIED",
                            "GUIDANCE_ONLY", "BLOCKED")),
    )

    def test_primary_readme_route_is_for_humans(self):
        for home, starter, guide, details, agent, _ in self.ROUTES:
            with self.subTest(home=home):
                text = (ROOT / home).read_text(encoding="utf-8")
                self.assertIn(f"({guide})", text)
                self.assertIn(f"({agent})", text)  # still linked as agent reference
                self.assertTrue((ROOT / guide).is_file())
                self.assertTrue((ROOT / starter).is_file())
                self.assertTrue((ROOT / details).is_file())
                release_line = next(line for line in text.splitlines()
                                    if line.startswith(("**Latest published release:**",
                                                        "**Последний опубликованный релиз:**")))
                self.assertNotIn("490cec222c4c2551a7bbe6f20bb0e9a316af13e1",
                                 release_line)
                self.assertIn("CHANGELOG.md", release_line)

    def test_beginner_page_is_short_and_preserves_critical_routes(self):
        for _, starter, guide, details, _, _ in self.ROUTES:
            with self.subTest(starter=starter):
                text = (ROOT / starter).read_text(encoding="utf-8")
                self.assertLess(len(text), 22000)
                self.assertIn(f"({Path(guide).name})", text)
                self.assertIn(f"({Path(details).name})", text)
                self.assertIn("NOT_RUN", text)
                self.assertIn("--apply", text)
                self.assertIn("## ", text)
                self.assertNotIn("## Choose your AI client\n\n| Client / mode", text)
                self.assertNotIn("## Выберите ИИ-клиент\n\n| Клиент и режим", text)

    def test_new_guides_are_safe_and_honest(self):
        for _, _, guide, details, agent, statuses in self.ROUTES:
            with self.subTest(guide=guide):
                text = (ROOT / guide).read_text(encoding="utf-8")
                reference = (ROOT / details).read_text(encoding="utf-8")
                for status in statuses:
                    self.assertIn(f"`{status}`", text)
                self.assertIn(f"({Path(agent).name})" if guide.startswith("nothing")
                              else "AGENT_START", text)
                self.assertIn("ZIP", text)
                self.assertIn("--apply", text)
                self.assertIn("NOT_RUN", reference)
                self.assertIn("### ChatGPT", reference)
                self.assertIn("### Claude Code", reference)
                self.assertIn("### OpenAI Codex", reference)


if __name__ == "__main__":
    unittest.main()
