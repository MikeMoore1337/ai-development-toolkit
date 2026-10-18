import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_pack import inspect
from install import install
class NewExtensionTests(unittest.TestCase):
    def test_manifest_and_all_skills(self):
        self.assertEqual([], inspect())
        m=json.loads((ROOT/'MANIFEST.json').read_text())
        self.assertEqual(14,len(m['extension_skills']))
        self.assertEqual(23,len(m['core_skills']+m['extension_skills']))
    def test_profile_selective_dry_run(self):
        m=json.loads((ROOT/'MANIFEST.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            install(d,m['profiles']['ui-fix'],False)
            self.assertFalse((Path(d)/'.agents').exists())
    def test_profile_real_install_preserves_instructions(self):
        m=json.loads((ROOT/'MANIFEST.json').read_text())
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/'AGENTS.md'
            original.write_text('local release gate\n')
            install(d,m['profiles']['agent-architecture'],True)
            self.assertEqual(original.read_text(),'local release gate\n')
            self.assertTrue((Path(d)/'.agents/skills/agent-framework-fit/SKILL.md').exists())
    def test_no_external_executable_added(self):
        self.assertFalse(list((ROOT/'.agents/skills').rglob('*.exe')))
        self.assertFalse(list((ROOT/'.agents/skills').rglob('*.dll')))
if __name__=='__main__':unittest.main()
