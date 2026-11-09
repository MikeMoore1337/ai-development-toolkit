"""Offline source/routing contract tests; no external skill execution is claimed."""
from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORCHESTRA = ROOT / ".agents" / "skills" / "ux-ui-design-orchestra"
PIN = "715c1807e08c497cfd1dc4feb450a2a3300ef2a9"
UPSTREAM = {
    "emil-design-eng", "animate", "animate-expo", "review-animations",
    "improve-animations", "find-animation-opportunities",
    "remove-animations", "choreograph", "animation-performance",
    "animation-vocabulary", "apple-design", "gestures", "write-swift",
    "pick-ui-library", "prototype", "mobile-native", "break-ui", "ask-sonner",
}
EXPLICIT_ONLY = {"review-animations", "prototype", "pick-ui-library"}


class EmilDesignOrchestraTests(unittest.TestCase):
    def test_pin_and_all_upstream_entrypoints(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(PIN, manifest["source_revision_pins"]["emilkowalski/skills"])
        self.assertRegex(PIN, r"^[a-f0-9]{40}$")
        guide = (ORCHESTRA / "references/EMIL_ORIGINAL_SKILLS.md").read_text(encoding="utf-8")
        self.assertIn(PIN, guide)
        self.assertIn("MIT", guide)
        for name in UPSTREAM:
            with self.subTest(name=name):
                self.assertIn("`" + name + "`", guide)

    def test_original_scope_and_approval_gates(self):
        guide = (ORCHESTRA / "references/EMIL_ORIGINAL_SKILLS.md").read_text(encoding="utf-8")
        for name in EXPLICIT_ONLY:
            self.assertRegex(guide, r"`" + re.escape(name) + r"`[^\n]*\*\*Explicit invocation only\*\*")
        for phrase in ("REFERENCE_ONLY", "FILES_PRESENT_UNATTESTED", "LOADED",
                       "INVOKED", "implement-approved", "ALL_THREE",
                       "disable-model-invocation: true",
                       "NATIVE_CLIENT_E2E_NOT_VERIFIED"):
            self.assertIn(phrase, guide)
        self.assertIn("without permission", guide)

    def test_existing_orchestra_routes_to_originals_not_new_controller(self):
        skill = (ORCHESTRA / "SKILL.md").read_text(encoding="utf-8")
        specialists = (ORCHESTRA / "references/SPECIALISTS.md").read_text(encoding="utf-8")
        workflow = (ORCHESTRA / "references/WORKFLOW.md").read_text(encoding="utf-8")
        for text in (skill, specialists, workflow):
            self.assertIn("EMIL_ORIGINAL_SKILLS.md", text)
        for path in ("docs/UX_UI_DESIGN.md", "docs/ru/UX_UI_DESIGN.md"):
            text = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("EMIL_ORIGINAL_SKILLS.md", text)
            self.assertIn(PIN, text)


if __name__ == "__main__":
    unittest.main()
