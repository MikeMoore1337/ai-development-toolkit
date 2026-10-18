import json,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from install import install
from validate_pack import validate_skill

class OptionalSkillsTests(unittest.TestCase):
    def test_clear_voice_complete(self):
        m=json.loads((ROOT/'MANIFEST.json').read_text('utf8'))
        self.assertEqual(['clear-voice'],m['profiles']['editorial'])
        cv=ROOT/'.agents/skills/clear-voice'
        self.assertEqual([],validate_skill(cv))
        for rel in ['LICENSE','SOURCES.md','THIRD_PARTY_NOTICES.md','evals/cases.json','evals/validate_package.py','profiles/general.md','profiles/product-ui.md','profiles/knowledge-base.md','profiles/research-digest.md','adapters/editorial-worker/EDITORIAL_STYLE_PROMPT.txt']:
            self.assertTrue((cv/rel).is_file(),rel)
        result=subprocess.run([sys.executable,'evals/validate_package.py'],cwd=cv,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('61',result.stdout)
    def test_make_feature_bundled_without_personal_issuance(self):
        m=json.loads((ROOT/'MANIFEST.json').read_text('utf8'))
        self.assertTrue(m['make_feature_source_bundled'])
        self.assertEqual(['make-feature'],m['profiles']['make-feature'])
        mf=ROOT/'extensions/make-feature/skills/make-feature'
        self.assertEqual([],validate_skill(mf))
        for path in ['SKILL.md','LICENSE','README.md','scripts/state.py','tests/test_state.py','templates/spec.json']:
            self.assertTrue((mf/path).exists(),path)
        self.assertFalse((mf/'LICENSE.txt').exists())
    def test_optin_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            install(tmp,['make-feature','clear-voice'],True)
            for name in ('make-feature','clear-voice'):
                self.assertTrue((Path(tmp)/'.agents/skills'/name/'SKILL.md').exists())

if __name__=='__main__':unittest.main()
