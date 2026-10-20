"""Integration, source-mapping and security regression tests for the QA pack."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from install import install, skill_sources
from validate_pack import inspect


class QAExtensionTests(unittest.TestCase):
    def setUp(self):
        self.m = json.loads((ROOT / 'MANIFEST.json').read_text(encoding='utf-8'))
        self.qa = self.m['extension_packs']['qa']

    def test_all_27_skills_and_11_roles(self):
        self.assertEqual(27, len(self.qa['skills']))
        self.assertEqual(11, len(self.qa['roles']))
        self.assertEqual(27, len(list((ROOT / 'extensions/qa/skills').glob('*/SKILL.md'))))
        self.assertEqual(11, len(list((ROOT / 'extensions/qa/roles').glob('*.md'))))
        self.assertEqual([], inspect())

    def test_source_map_all_27(self):
        text = (ROOT / 'extensions/qa/SOURCE_MAPPING.md').read_text(encoding='utf-8')
        mappings = [line for line in text.splitlines() if line.startswith('| `')]
        self.assertEqual(27, len(mappings))
        for line in mappings:
            mapped = line.split('`')[3]
            self.assertIn(mapped, self.qa['skills'])

    def test_profile_catalog_resolves(self):
        sources = skill_sources(self.m)
        self.assertEqual(67, len(sources))
        for profile, names in self.m['profiles'].items():
            with self.subTest(profile=profile):
                self.assertTrue(names)
                self.assertEqual(len(names), len(set(names)))
                self.assertTrue(all(name in sources for name in names))

    def test_qa_profile_dry_run_and_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / 'AGENTS.md').write_text('project-owned, do not modify\n', encoding='utf-8')
            chosen = self.m['profiles']['qa-fullstack']
            install(repo, chosen, False)
            self.assertFalse((repo / '.agents').exists())
            install(repo, chosen, True)
            self.assertEqual('project-owned, do not modify\n', (repo / 'AGENTS.md').read_text())
            self.assertTrue((repo / '.agents/skills/test-analysis-design/SKILL.md').exists())
            with self.assertRaises(FileExistsError):
                install(repo, chosen, True)

    def test_mixed_profile_across_core_and_qa(self):
        with tempfile.TemporaryDirectory() as tmp:
            names = ['task-scoping', 'test-review', 'feature-delivery']
            install(tmp, names, True, layout='claude')
            for name in names:
                self.assertTrue((Path(tmp) / '.claude' / 'skills' / name / 'SKILL.md').is_file())

    def test_qa_all_is_opt_in(self):
        self.assertEqual(27, len(self.m['profiles']['qa-all']))
        self.assertFalse(self.qa['auto_install'])
        self.assertFalse(any(x in self.m['profiles']['general'] for x in self.qa['skills']))

    def test_reject_duplicate_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                install(tmp, ['test-review', 'test-review'], True)
            self.assertFalse((Path(tmp) / '.agents').exists())

    def test_qa_skill_is_not_global_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            install(tmp, self.m['profiles']['general'], True)
            self.assertFalse((Path(tmp) / '.agents' / 'skills' / 'test-review').exists())

    def test_private_make_feature_absent_from_public_tree(self):
        self.assertFalse(list(ROOT.glob('**/LICENSE.personal.txt')))
        self.assertFalse(list(ROOT.rglob('make-feature-0.3.0*.gz')))

    def test_qa_archive_project_instructions_not_bundled(self):
        self.assertFalse((ROOT/'extensions/qa/AGENTS.md').exists())
        self.assertFalse((ROOT/'extensions/qa/ai/onboarding.md').exists())
        self.assertFalse((ROOT/'extensions/qa/ai/workflows.md').exists())

if __name__ == '__main__':
    unittest.main()
