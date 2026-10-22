"""Static portable-skill contracts, not live agent/SEO execution."""
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from install import skill_sources
from validate_pack import validate_skill

class PromptSeoSkillTests(unittest.TestCase):
    def test_profiles_and_file_refs(self):
        m=json.loads((ROOT/"MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(["prompt-refinement"],m["profiles"]["prompt-refinement"])
        self.assertEqual(["seo-audit","research-verification"],m["profiles"]["seo-audit"])
        self.assertIn("prompt-refinement",m["extension_packs"]["ai"]["skills"])
        self.assertEqual(["seo-audit"],m["extension_packs"]["seo"]["skills"])
        sources=skill_sources(m)
        for skill in ("prompt-refinement","seo-audit"):
            self.assertEqual([],validate_skill(sources[skill]))
            self.assertTrue((sources[skill]/"references").is_dir())
            for path in m["chatgpt_personal_live"]["source_sets"][skill]:
                self.assertTrue((ROOT/path).is_file(),path)
    def test_prompt_boundary(self):
        content=(ROOT/"extensions/ai/skills/prompt-refinement/SKILL.md").read_text(encoding="utf-8")
        for word in ("copy-ready","clarification","do not execute","Codex","NOT_RUN","clear-voice"):
            self.assertIn(word.lower(),content.lower())
    def test_seo_evidence_boundary(self):
        content=(ROOT/"extensions/seo/skills/seo-audit/SKILL.md").read_text(encoding="utf-8")
        for word in ("CONFIRMED","NOT_VERIFIED","robots.txt","noindex","Search Console","does not guarantee"):
            self.assertIn(word.lower(),content.lower())

if __name__=="__main__":unittest.main()
