import sys, unittest, tempfile, os, subprocess
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from validate_pack import inspect
from install import install
class Tests(unittest.TestCase):
    def test_core_manifest_and_frontmatter(self):
        self.assertEqual([],inspect())
    def test_install_dry_run(self):
        with tempfile.TemporaryDirectory() as d:
            install(d,['implementation','qa-strategy'],False)
            self.assertFalse((Path(d)/'.agents').exists())
    def test_install_selected_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            install(d,['implementation'],True)
            self.assertTrue((Path(d)/'.agents/skills/implementation/SKILL.md').exists())
            with self.assertRaises(FileExistsError):install(d,['implementation'],True)
    def test_existing_agents_md_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            original=Path(d)/'AGENTS.md'
            original.write_text('PRIVATE PROJECT RULE\n',encoding='utf-8')
            install(d,['task-scoping'],True)
            self.assertEqual(original.read_text(encoding='utf-8'),'PRIVATE PROJECT RULE\n')
    def test_unknown_skills_not_auto_installed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):install(d,['ru-legal-risk'],True)
    def test_symlink_destination_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'elsewhere'
            out.mkdir()
            dst = Path(d) / '.agents'
            try:
                dst.symlink_to(out, target_is_directory=True)
            except OSError as exc:
                # Windows often requires Developer Mode / SeCreateSymbolicLinkPrivilege
                # for symlinks. Ordinary users can still create directory junctions.
                if os.name != 'nt' or getattr(exc, 'winerror', None) != 1314:
                    raise
                result = subprocess.run(
                    ['cmd.exe', '/c', 'mklink', '/J', str(dst), str(out)],
                    capture_output=True, text=True,
                )
                self.assertEqual(
                    0, result.returncode,
                    f'Cannot create junction for security test: {result.stdout} {result.stderr}',
                )
                self.assertTrue(dst.is_junction())
            with self.assertRaises(ValueError):
                install(d, ['implementation'], True)
            self.assertFalse((out / 'skills' / 'implementation').exists())

    def test_windows_junction_detection_even_without_real_junction(self):
        # Explicitly exercise junction detection on every CI platform.
        with tempfile.TemporaryDirectory() as d:
            junction = Path(d) / '.agents'
            original_is_junction = Path.is_junction

            def pretend_junction(path):
                return path == junction or original_is_junction(path)

            with patch.object(Path, 'is_junction', new=pretend_junction):
                with self.assertRaises(ValueError):
                    install(d, ['implementation'], True)
            self.assertFalse(junction.exists())
if __name__=='__main__':unittest.main()
