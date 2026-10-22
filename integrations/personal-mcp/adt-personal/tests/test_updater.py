"""Offline end-to-end updater checks using private synthetic Git remotes."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'updater' / 'update_toolkit.py'
spec = importlib.util.spec_from_file_location('adt_auto_updater', SCRIPT)
updater = importlib.util.module_from_spec(spec)
spec.loader.exec_module(updater)


def git(*args, cwd=None):
    cp = subprocess.run(['git', *map(str, args)], cwd=cwd, capture_output=True, text=True)
    if cp.returncode:
        raise RuntimeError((args, cp.stderr))
    return cp.stdout.strip()


class TestUpdater(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='adt-updater-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.remote = self.root/'remote.git'
        git('init', '--bare', self.remote)
        self.author = self.root/'author'
        git('clone', self.remote, self.author)
        git('checkout', '-b', 'main', cwd=self.author)
        git('config', 'user.name', 'Updater CI', cwd=self.author)
        git('config', 'user.email', 'updater-ci@example.invalid', cwd=self.author)
        self.source = self.root/'toolkit-source'
        self.state = self.root/'updater-state'
        self._save_toolkit('1.0.0')
        git('push', '-u', 'origin', 'main', cwd=self.author)
        git('symbolic-ref', 'HEAD', 'refs/heads/main', cwd=self.remote)
        git('clone', '--depth', '1', '--branch', 'main', self.remote, self.source)
        self.old_head = git('rev-parse', 'HEAD', cwd=self.source)

    def _save_toolkit(self, version, *, skill_desc='Implementation for bounded changes.', extra=False):
        manifest = {
            'package': 'ai-development-toolkit', 'version': version,
            'core_skills': ['implementation'], 'extension_skills': [],
            'core_roles': ['orchestrator'],
            'profiles': {'general': ['implementation']},
            'extension_packs': {}
        }
        (self.author/'.agents/skills/implementation').mkdir(parents=True, exist_ok=True)
        (self.author/'.agents/roles').mkdir(parents=True, exist_ok=True)
        (self.author/'MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')
        (self.author/'.agents/skills/implementation/SKILL.md').write_text(
            f'---\nname: implementation\ndescription: {skill_desc}\n---\n\nInstructions.\n', encoding='utf-8')
        (self.author/'.agents/roles/orchestrator.md').write_text('Review and coordinate.\n', encoding='utf-8')
        if extra:
            (self.author/'README.md').write_text('A revised project.\n', encoding='utf-8')
        git('add', '-A', cwd=self.author)
        git('commit', '-m', f'version {version}', cwd=self.author)

    def _push(self, version, **kwargs):
        self._save_toolkit(version, **kwargs)
        git('push', 'origin', 'main', cwd=self.author)

    def _check(self, **kwargs):
        return updater.update(self.source, self.state, expected_origin=str(self.remote), **kwargs)

    def test_up_to_date_then_skipped_same_day(self):
        first = self._check(today='2026-10-21')
        self.assertEqual(first['status'], 'UP_TO_DATE')
        second = self._check(today='2026-10-21')
        self.assertEqual(second['status'], 'SKIPPED_ALREADY_CHECKED_TODAY')
        self.assertEqual(git('rev-parse', 'HEAD', cwd=self.source), self.old_head)

    def test_valid_commit_fast_forwards_and_saves_previous_sha(self):
        self._push('1.1.0', extra=True)
        result = self._check(today='2026-10-21')
        self.assertEqual(result['status'], 'UPDATED')
        self.assertEqual(result['previous_revision'], self.old_head)
        self.assertEqual(result['skills'], 1)
        self.assertEqual(result['toolkit_version'], '1.1.0')
        self.assertNotEqual(result['active_revision'], self.old_head)
        self.assertEqual(git('rev-parse', 'refs/adt-personal/previous-good', cwd=self.source), self.old_head)
        state = updater.read_state(self.state/'state.json')
        self.assertEqual(state['active_revision'], result['active_revision'])
        self.assertEqual(state['previous_good_revision'], self.old_head)
        self.assertFalse((self.source/'updater-state').exists())

    def test_bad_skill_metadata_blocks_update_and_preserves_old(self):
        self._push('2.0.0', skill_desc='')
        with self.assertRaisesRegex(updater.UpdateError, 'candidate_skill_metadata_invalid'):
            self._check(today='2026-10-21')
        self.assertEqual(git('rev-parse', 'HEAD', cwd=self.source), self.old_head)
        self.assertEqual(updater.read_state(self.state/'state.json')['last_attempt_status'], 'FAIL')

    def test_local_changes_block_update_without_removing_files(self):
        (self.source/'LOCAL_NOTES.txt').write_text('Do not remove.\n', encoding='utf-8')
        self._push('1.1.0')
        with self.assertRaisesRegex(updater.UpdateError, 'local_changes_present'):
            self._check(today='2026-10-21')
        self.assertEqual((self.source/'LOCAL_NOTES.txt').read_text(), 'Do not remove.\n')
        self.assertEqual(git('rev-parse', 'HEAD', cwd=self.source), self.old_head)

    def test_unexpected_origin_blocked(self):
        with self.assertRaisesRegex(updater.UpdateError, 'unexpected_git_origin'):
            updater.update(self.source, self.state)
        self.assertEqual(git('rev-parse', 'HEAD', cwd=self.source), self.old_head)

    def test_lock_blocks_concurrent_check(self):
        self.state.mkdir()
        (self.state/'update.lock').write_text('locked', encoding='utf-8')
        with self.assertRaisesRegex(updater.UpdateError, 'another_update_is_in_progress'):
            self._check(today='2026-10-21')
        self.assertTrue((self.state/'update.lock').exists())

    def test_stale_lock_recovers_after_interrupted_run(self):
        import time
        self.state.mkdir()
        lock = self.state/'update.lock'
        lock.write_text('abandoned', encoding='utf-8')
        os.utime(lock, (time.time() - 3600, time.time() - 3600))
        self.assertEqual(self._check(today='2026-10-21')['status'], 'UP_TO_DATE')
        self.assertFalse(lock.exists())

    def test_missing_role_blocks_update(self):
        (self.author/'.agents/roles/orchestrator.md').unlink()
        git('add', '-A', cwd=self.author)
        git('commit', '-m', 'remove role', cwd=self.author)
        git('push', 'origin', 'main', cwd=self.author)
        with self.assertRaisesRegex(updater.UpdateError, 'candidate_missing_role'):
            self._check(today='2026-10-21')
        self.assertEqual(git('rev-parse', 'HEAD', cwd=self.source), self.old_head)

    def test_status_has_no_network_side_effect(self):
        result = subprocess.run([os.sys.executable, str(SCRIPT), '--state-dir', str(self.state), '--status'],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['status'], 'STATE')

    def test_does_not_execute_scripts_from_repository(self):
        # A suspicious repository script is treated as inert data.
        suspicious = self.author/'scripts'/'custom_script.py'
        suspicious.parent.mkdir()
        suspicious.write_text('raise RuntimeError("should never execute")\n')
        git('add', '-A', cwd=self.author)
        git('commit', '-m', 'script as data', cwd=self.author)
        git('push', 'origin', 'main', cwd=self.author)
        self.assertEqual(self._check(today='2026-10-21')['status'], 'UPDATED')


class TestPowerShellInstaller(unittest.TestCase):
    def test_scheduled_task_is_scoped_to_current_user(self):
        text = (SCRIPT.parents[1]/'Enable-ADT-AutoUpdate.ps1').read_text(encoding='utf-8')
        self.assertIn('New-ScheduledTaskTrigger -Daily', text)
        self.assertIn('New-ScheduledTaskTrigger -AtLogOn -User $identity', text)
        self.assertIn('-LogonType Interactive -RunLevel Limited', text)
        self.assertIn('Register-ScheduledTask', text)
        self.assertIn('Unregister-ScheduledTask', text)
        self.assertIn('Get-FileHash', text)
        self.assertNotIn('Set-ExecutionPolicy', text)
        self.assertNotIn('mcp remove', text)

if __name__ == '__main__':
    unittest.main()
