"""Offline checks for the optional Agentation-compatible UI evidence handoff (#404).

Source-only gates do not claim Agentation installation, browser execution, or visual quality.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class UIAnnotationHandoffTests(unittest.TestCase):
    def test_bilingual_handoff_requires_privacy_and_exact_evidence(self):
        en = (ROOT / "docs/en/UI_ANNOTATION_HANDOFF.md").read_text(encoding="utf-8")
        ru = (ROOT / "docs/ru/UI_ANNOTATION_HANDOFF.md").read_text(encoding="utf-8")
        fields = ("baseline_sha", "viewport", "theme", "selector", "evidence_refs",
                  "owner_gate", "NOT_OBSERVED", "NOT_EXECUTED", "SOURCE_ONLY",
                  "PolyForm Shield 1.0.0", "SYNTHETIC")
        for text in (en, ru):
            for field in fields:
                with self.subTest(document=text[:48], field=field):
                    self.assertIn(field, text)
            self.assertIn("https://github.com/benjitaylor/agentation", text)
        self.assertIn("MCP", en)
        self.assertIn("MCP", ru)

    def test_source_skills_link_existing_optional_protocol(self):
        screenshot = (ROOT / ".agents/skills/screenshot-fidelity/SKILL.md").read_text(encoding="utf-8")
        orchestra = (ROOT / ".agents/skills/ux-ui-design-orchestra/references/HANDOFF.md").read_text(encoding="utf-8")
        self.assertIn("UI_ANNOTATION_HANDOFF.md", screenshot)
        self.assertIn("UI_ANNOTATION_HANDOFF.md", orchestra)
        self.assertIn("no visual approval", screenshot.lower())
        self.assertIn("untrusted", orchestra.lower())

    def test_no_auto_install_or_run_claim_in_reference(self):
        en = (ROOT / "docs/en/UI_ANNOTATION_HANDOFF.md").read_text(encoding="utf-8")
        for forbidden in ("npm install -g", "curl | bash", "agentation-mcp server", "auto-send"):
            self.assertNotIn(forbidden, en)
        self.assertIn("does not", en.lower())
        self.assertIn("shared Toolkit repository", en)

if __name__ == "__main__":
    unittest.main()
