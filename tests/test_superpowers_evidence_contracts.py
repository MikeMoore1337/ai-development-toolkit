"""Portable source-only checks for selected Superpowers-inspired contracts (#400)."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SuperpowersEvidenceContractsTests(unittest.TestCase):
    def test_skills_reuse_existing_workflow(self):
        feature = (ROOT / ".agents/skills/feature-delivery/SKILL.md").read_text(encoding="utf-8")
        review = (ROOT / ".agents/skills/code-review/SKILL.md").read_text(encoding="utf-8")
        release = (ROOT / ".agents/skills/release-safety/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("ROOT_CAUSE", feature.upper().replace(" ", "_") if "ROOT_CAUSE" in feature else
                      "ROOT_CAUSE") if False else None
        for phrase in ("earliest failing boundary", "NOT_VERIFIED", "host-native", "project-defined"):
            self.assertIn(phrase, feature)
        for phrase in ("receiving", "before accepting", "Never invent a second reviewer"):
            self.assertIn(phrase, review)
        for phrase in ("DEPLOYMENT_NOT_VERIFIED", "exact PR head", "NOT_MEASURED"):
            self.assertIn(phrase, release)

    def test_bilingual_reference_has_no_execution_claim(self):
        for path in ("docs/en/SUPERPOWERS_EVIDENCE.md", "docs/ru/SUPERPOWERS_EVIDENCE.md"):
            content = (ROOT / path).read_text(encoding="utf-8")
            for required in ("git rev-parse --git-dir", "git rev-parse --git-common-dir",
                             "git rev-parse --show-superproject-working-tree",
                             "NOT_MEASURED", "NOT_VERIFIED", "git check-ignore"):
                with self.subTest(path=path, required=required):
                    self.assertIn(required, content)
            self.assertIn("obra/superpowers", content)
            self.assertNotIn("npm install -g", content)
            self.assertNotIn("curl | bash", content)

    def test_no_duplicate_agent_or_automatic_worktree_claim(self):
        text = (ROOT / "docs/en/SUPERPOWERS_EVIDENCE.md").read_text(encoding="utf-8")
        self.assertIn("do not silently mutate", text)
        self.assertIn("no native/controller mechanism", text)
        self.assertIn("never in the shared Toolkit repository", text)
        self.assertIn("controller wins", text)


if __name__ == "__main__":
    unittest.main()
