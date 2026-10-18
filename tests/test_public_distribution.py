import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_pack import inspect

class DistributionTests(unittest.TestCase):
    def test_pack_validation(self):
        self.assertEqual([],inspect())
    def test_no_original_copies(self):
        self.assertEqual([],list((ROOT/'optional-original-skills').glob('*/SKILL.md')))
    def test_public_manifest(self):
        m=json.loads((ROOT/'MANIFEST.json').read_text(encoding='utf-8'))
        self.assertTrue(m['make_feature_source_bundled'])
        self.assertEqual(0,m['original_skills_bundled_as_opt_in'])
    def test_private_archive_absent(self):
        self.assertFalse(list(ROOT.rglob('make-feature-0.3.0*.gz')))
        self.assertFalse((ROOT/'make-feature').exists())

if __name__=='__main__':unittest.main()
