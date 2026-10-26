"""Offline end-to-end updater checks using private synthetic Git remotes."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
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
        # Synthetic remote must preserve canonical LF blobs on Windows.
        git('config', 'core.autocrlf', 'false', cwd=self.author)
        (self.author/'.gitattributes').write_bytes(b'*.md -text\n')
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
        # Git fixture blobs use canonical LF on Windows too; write_text()
        # otherwise converts '\n' to CRLF on some Windows runners.
        (self.author/'.agents/skills/implementation/SKILL.md').write_bytes(
            f'---\nname: implementation\ndescription: {skill_desc}\n---\n\nInstructions.\n'.encode('utf-8'))
        (self.author/'.agents/roles/orchestrator.md').write_text('Review and coordinate.\n', encoding='utf-8')
        if extra:
            (self.author/'README.md').write_text('A revised project.\n', encoding='utf-8')
        git('add', '-A', cwd=self.author)
        git('commit', '-m', f'version {version}', cwd=self.author)

    def _push(self, version, **kwargs):
        self._save_toolkit(version, **kwargs)
        git('push', 'origin', 'main', cwd=self.author)

    def _check(self, source=None, **kwargs):
        return updater.update(source or self.source, self.state,
                              expected_origin=str(self.remote), **kwargs)

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

    def test_origin_url_rewrite_is_blocked(self):
        git('config', 'url.https://mirror.invalid/toolkit.git.insteadOf',
            str(self.remote), cwd=self.source)
        with self.assertRaisesRegex(updater.UpdateError, 'unexpected_git_url_rewrite'):
            self._check(today='2026-10-21')
        self.assertEqual(self.old_head, git('rev-parse', 'HEAD', cwd=self.source))

    def test_lock_blocks_concurrent_check(self):
        with updater.exclusive_lock(self.state):
            with self.assertRaisesRegex(updater.UpdateError, 'another_update_is_in_progress'):
                self._check(today='2026-10-21')
        self.assertTrue((self.state/'update.lock').exists())

    def test_lock_blocks_separate_process_and_releases_after_termination(self):
        ready = self.state / 'holder-ready'
        child = (
            "import importlib.util, pathlib, sys, time\n"
            "spec = importlib.util.spec_from_file_location('adt_child', sys.argv[1])\n"
            "module = importlib.util.module_from_spec(spec)\n"
            "spec.loader.exec_module(module)\n"
            "with module.exclusive_lock(pathlib.Path(sys.argv[2])):\n"
            "    pathlib.Path(sys.argv[3]).write_text('ready', encoding='utf-8')\n"
            "    time.sleep(30)\n"
        )
        holder = subprocess.Popen(
            [os.sys.executable, '-c', child, str(SCRIPT), str(self.state), str(ready)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            deadline = time.monotonic() + 5
            while not ready.exists() and holder.poll() is None and time.monotonic() < deadline:
                time.sleep(0.05)
            if not ready.exists():
                detail = holder.stderr.read() if holder.poll() is not None else 'lock holder did not become ready'
                self.fail(detail)
            with self.assertRaisesRegex(updater.UpdateError, 'another_update_is_in_progress'):
                self._check(today='2026-10-21')
        finally:
            holder.terminate()
            try:
                holder.wait(timeout=5)
            except subprocess.TimeoutExpired:
                holder.kill()
                holder.wait(timeout=5)
            holder.stdout.close()
            holder.stderr.close()
        self.assertEqual('UP_TO_DATE', self._check(today='2026-10-21')['status'])
        self.assertTrue((self.state/'update.lock').exists())

    def test_stale_lock_recovers_after_interrupted_run(self):
        self.state.mkdir()
        lock = self.state/'update.lock'
        lock.write_text('abandoned', encoding='utf-8')
        self.assertEqual(self._check(today='2026-10-21')['status'], 'UP_TO_DATE')
        self.assertTrue(lock.exists())

    def test_corrupt_state_fails_closed_without_overwrite(self):
        self.state.mkdir()
        state_file = self.state / 'state.json'
        state_file.write_bytes(b'{broken')
        before = state_file.read_bytes()
        with self.assertRaisesRegex(updater.UpdateError, 'state_invalid'):
            self._check(today='2026-10-21')
        self.assertEqual(before, state_file.read_bytes())

    def test_state_checkout_mismatch_fails_closed(self):
        updater.write_state(self.state / 'state.json', {'active_revision': '0' * 40})
        with self.assertRaisesRegex(updater.UpdateError, 'state_checkout_mismatch'):
            self._check(today='2026-10-21')
        self.assertEqual(self.old_head, git('rev-parse', 'HEAD', cwd=self.source))

    def test_state_writer_does_not_reuse_predictable_temp_file(self):
        self.state.mkdir()
        collision = self.state / 'state.json.tmp'
        collision.write_bytes(b'keep this file')
        updater.write_state(self.state / 'state.json', {'active_revision': self.old_head})
        self.assertEqual(b'keep this file', collision.read_bytes())
        self.assertEqual(self.old_head,
                         updater.read_state(self.state / 'state.json')['active_revision'])

    def test_missing_role_blocks_update(self):
        (self.author/'.agents/roles/orchestrator.md').unlink()
        git('add', '-A', cwd=self.author)
        git('commit', '-m', 'remove role', cwd=self.author)
        git('push', 'origin', 'main', cwd=self.author)
        with self.assertRaisesRegex(updater.UpdateError, 'candidate_missing_role'):
            self._check(today='2026-10-21')
        self.assertEqual(git('rev-parse', 'HEAD', cwd=self.source), self.old_head)

    def test_malformed_extension_pack_blocks_update(self):
        self._save_toolkit('1.1.0')
        manifest = json.loads((self.author/'MANIFEST.json').read_text(encoding='utf-8'))
        manifest['extension_packs'] = {
            'broken': {'skill_root': '.agents/skills', 'skills': None, 'roles': []}
        }
        (self.author/'MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')
        git('add', '-A', cwd=self.author)
        git('commit', '-m', 'malformed extension pack', cwd=self.author)
        git('push', 'origin', 'main', cwd=self.author)
        with self.assertRaisesRegex(updater.UpdateError, 'candidate_pack_invalid'):
            self._check(today='2026-10-21')
        self.assertEqual(self.old_head, git('rev-parse', 'HEAD', cwd=self.source))
        manifest['extension_packs'] = {}
        manifest['profiles'] = {'general': [[]]}
        (self.author/'MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')
        git('add', '-A', cwd=self.author)
        git('commit', '-m', 'malformed profile', cwd=self.author)
        git('push', 'origin', 'main', cwd=self.author)
        with self.assertRaisesRegex(updater.UpdateError, 'candidate_profile_has_unknown_skill'):
            self._check(today='2026-10-21', force=True)
        self.assertEqual(self.old_head, git('rev-parse', 'HEAD', cwd=self.source))

    def test_offline_version_preflight_and_last_known(self):
        untouched = (self.source / 'MANIFEST.json').read_bytes()
        before = git('rev-parse', 'HEAD', cwd=self.source)
        first = updater.preflight(self.source, self.state, expected_origin=str(self.remote))
        self.assertEqual('PREFLIGHT', first['status'])
        self.assertEqual('1.0.0', first['toolkit_version'])
        self.assertEqual('NOT_VERIFIED', first['last_known_revision'])
        self.assertFalse(first['state_matches_checkout'])
        self.assertFalse(first['rollback_eligible'])
        self.assertFalse(first['network_used'])
        self.assertFalse(first['project_files_changed'])
        self.assertEqual('NOT_VERIFIED', first['mcp_adapter_version'])
        self.assertEqual('NOT_VERIFIED', first['chatgpt_plugin_version'])
        self.assertEqual('NOT_TESTED', first['client_runtime_compatibility'])
        self.assertFalse(self.state.exists())
        self.assertEqual(before, git('rev-parse', 'HEAD', cwd=self.source))
        self.assertEqual(untouched, (self.source / 'MANIFEST.json').read_bytes())
        self._check(today='2026-10-21')
        verified = updater.preflight(self.source, self.state, expected_origin=str(self.remote))
        self.assertTrue(verified['state_matches_checkout'])
        self.assertEqual(before, verified['last_known_revision'])
        self.assertEqual('1.0.0', verified['last_known_toolkit_version'])

    def test_clean_explicit_preview_and_rollback(self):
        target_project = self.root / 'unrelated-project'
        target_project.mkdir()
        original = b'UNMANAGED PROJECT MUST REMAIN UNCHANGED'
        (target_project / 'AGENTS.md').write_bytes(original)
        self._push('1.1.0')
        result = self._check(today='2026-10-21')
        current = result['active_revision']
        state_file = self.state/'state.json'
        state_bytes = state_file.read_bytes()
        preview = updater.rollback(self.source, self.state, expected_origin=str(self.remote))
        self.assertEqual('ROLLBACK_PREVIEW', preview['status'])
        self.assertEqual(self.old_head, preview['previous_good_revision'])
        self.assertEqual('1.0.0', preview['would_restore']['toolkit_version'])
        self.assertEqual(state_bytes, state_file.read_bytes())
        self.assertEqual(current, git('rev-parse', 'HEAD', cwd=self.source))
        actual = updater.rollback(self.source, self.state, apply=True,
                                  expected_origin=str(self.remote))
        self.assertEqual('ROLLED_BACK', actual['status'])
        self.assertEqual(self.old_head, git('rev-parse', 'HEAD', cwd=self.source))
        self.assertEqual('1.0.0', actual['toolkit_version'])
        self.assertEqual('ROLLED_BACK', updater.read_state(state_file)['last_attempt_status'])
        self.assertIsNone(updater.read_state(state_file)['previous_good_revision'])
        self.assertEqual(original, (target_project / 'AGENTS.md').read_bytes())
        self.assertFalse((self.source / 'updater-state').exists())
        with self.assertRaisesRegex(updater.UpdateError, 'rollback_unavailable'):
            updater.rollback(self.source, self.state, apply=True,
                             expected_origin=str(self.remote))

    def test_dirty_or_tampered_checkout_cannot_rollback(self):
        self._push('1.1.0')
        upgraded = self._check(today='2026-10-21')
        (self.source / 'OWNED_NOTES.txt').write_text('do not delete', encoding='utf-8')
        with self.assertRaisesRegex(updater.UpdateError, 'local_changes_present'):
            updater.rollback(self.source, self.state, apply=True,
                             expected_origin=str(self.remote))
        self.assertEqual('do not delete', (self.source / 'OWNED_NOTES.txt').read_text())
        (self.source / 'OWNED_NOTES.txt').unlink()
        state_file = self.state / 'state.json'
        state = updater.read_state(state_file)
        state['previous_good_revision'] = upgraded['active_revision']
        updater.write_state(state_file, state)
        with self.assertRaisesRegex(updater.UpdateError, 'rollback_unavailable'):
            updater.rollback(self.source, self.state, apply=True,
                             expected_origin=str(self.remote))
        self.assertEqual(upgraded['active_revision'], git('rev-parse', 'HEAD', cwd=self.source))

    def test_rollback_refuses_wrong_origin_and_invalid_version(self):
        with self.assertRaisesRegex(updater.UpdateError, 'unexpected_git_origin'):
            updater.preflight(self.source, self.state)
        self._push('0.9.0')
        with self.assertRaisesRegex(updater.UpdateError, 'candidate_toolkit_version_downgrade'):
            self._check(today='2026-10-21')
        self.assertEqual(self.old_head, git('rev-parse', 'HEAD', cwd=self.source))
        with self.assertRaisesRegex(updater.UpdateError, 'unsupported_toolkit_version_format'):
            updater.version_tuple('1.0.beta')

    def test_rollback_respects_active_update_lock(self):
        self._push('1.1.0')
        self._check(today='2026-10-21')
        with updater.exclusive_lock(self.state):
            with self.assertRaisesRegex(updater.UpdateError, 'another_update_is_in_progress'):
                updater.rollback(self.source, self.state, apply=True,
                                 expected_origin=str(self.remote))
        self.assertTrue((self.state / 'update.lock').exists())

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

    def test_git_post_merge_hook_is_not_executed(self):
        hook = self.source / '.git' / 'hooks' / 'post-merge'
        marker = self.root / 'hook-ran.txt'
        hook.write_text("#!/bin/sh\nprintf ran > '" + marker.as_posix() + "'\n", encoding='utf-8')
        try:
            os.chmod(hook, 0o700)
        except OSError:
            pass
        self._push('1.1.0')
        self.assertEqual('UPDATED', self._check(today='2026-10-21')['status'])
        self.assertFalse(marker.exists())

    def test_fetch_does_not_use_shared_fetch_head(self):
        fetch_head = self.source / '.git' / 'FETCH_HEAD'
        before = b'preserve this unrelated fetch metadata\n'
        fetch_head.write_bytes(before)
        self._push('1.1.0')
        self.assertEqual('UPDATED', self._check(today='2026-10-21')['status'])
        self.assertEqual(before, fetch_head.read_bytes())

    def test_interrupted_after_checkout_recovers_from_durable_journal(self):
        self._push('1.1.0')
        original_write_state = updater.write_state

        def interrupt_before_final_state(path, state):
            if state.get('last_attempt_status') == 'UPDATED':
                raise updater.UpdateError('simulated_interruption')
            return original_write_state(path, state)

        updater.write_state = interrupt_before_final_state
        try:
            with self.assertRaisesRegex(updater.UpdateError, 'simulated_interruption'):
                self._check(today='2026-10-21')
        finally:
            updater.write_state = original_write_state

        pending = updater.read_state(self.state / 'state.json')
        self.assertIsNotNone(pending['pending_update'])
        recovered = self._check(today='2026-10-22')
        self.assertEqual('RECOVERED_AFTER_INTERRUPTION', recovered['status'])
        final = updater.read_state(self.state / 'state.json')
        self.assertIsNone(final['pending_update'])
        self.assertEqual(recovered['active_revision'], final['active_revision'])
        self.assertEqual(self.old_head, final['previous_good_revision'])
        self.assertNotEqual(0, subprocess.run(
            ['git', '-C', str(self.source), 'show-ref', '--verify', '--quiet',
             updater.CANDIDATE_REF], check=False).returncode)

    def test_interrupted_rollback_recovers_from_durable_journal(self):
        self._push('1.1.0')
        self._check(today='2026-10-21')
        original_write_state = updater.write_state

        def interrupt_after_reset(path, state):
            if state.get('last_attempt_status') == 'ROLLED_BACK':
                raise updater.UpdateError('simulated_rollback_interruption')
            return original_write_state(path, state)

        updater.write_state = interrupt_after_reset
        try:
            with self.assertRaisesRegex(updater.UpdateError, 'simulated_rollback_interruption'):
                updater.rollback(self.source, self.state, apply=True,
                                 expected_origin=str(self.remote))
        finally:
            updater.write_state = original_write_state

        pending = updater.read_state(self.state / 'state.json')
        self.assertIsNotNone(pending['pending_rollback'])
        self.assertEqual(self.old_head, git('rev-parse', 'HEAD', cwd=self.source))
        recovered = self._check(today='2026-10-22')
        self.assertEqual('ROLLED_BACK_AFTER_INTERRUPTION', recovered['status'])
        final = updater.read_state(self.state / 'state.json')
        self.assertIsNone(final['pending_rollback'])
        self.assertIsNone(final['previous_good_revision'])
        self.assertEqual('ROLLED_BACK_AFTER_INTERRUPTION', final['last_attempt_status'])

    def test_rollback_rechecks_head_before_destructive_reset(self):
        self._push('1.1.0')
        upgraded = self._check(today='2026-10-21')
        original_write_state = updater.write_state
        injected = False

        def advance_after_journal(path, state):
            nonlocal injected
            original_write_state(path, state)
            if state.get('pending_rollback') is not None and not injected:
                injected = True
                self._push('1.2.0')
                git('fetch', 'origin', 'main', cwd=self.source)
                git('merge', '--ff-only', 'origin/main', cwd=self.source)

        updater.write_state = advance_after_journal
        try:
            with self.assertRaisesRegex(updater.UpdateError, 'source_changed_before_rollback'):
                updater.rollback(self.source, self.state, apply=True,
                                 expected_origin=str(self.remote))
        finally:
            updater.write_state = original_write_state

        self.assertEqual(git('rev-parse', 'origin/main', cwd=self.source),
                         git('rev-parse', 'HEAD', cwd=self.source))
        self.assertNotEqual(upgraded['active_revision'], git('rev-parse', 'HEAD', cwd=self.source))
        self.assertIsNotNone(updater.read_state(self.state / 'state.json')['pending_rollback'])

    def test_update_failure_rechecks_head_before_destructive_reset(self):
        self._push('1.1.0')
        original_check_origin = updater.check_origin
        original_run_git = updater.run_git
        check_count = 0
        injected = False
        failure_ready = False

        def fail_after_merge(source, expected_origin, require_clean=True):
            nonlocal check_count, failure_ready
            check_count += 1
            if check_count == 3:
                failure_ready = True
                raise updater.UpdateError('simulated_post_update_failure')
            return original_check_origin(source, expected_origin, require_clean=require_clean)

        def advance_during_rollback_check(source, *args, **kwargs):
            nonlocal injected
            if failure_ready and args[:2] == ('status', '--porcelain') and not injected:
                injected = True
                self._push('1.2.0')
                git('fetch', 'origin', 'main', cwd=self.source)
                git('merge', '--ff-only', 'origin/main', cwd=self.source)
            return original_run_git(source, *args, **kwargs)

        updater.check_origin = fail_after_merge
        updater.run_git = advance_during_rollback_check
        try:
            with self.assertRaisesRegex(
                    updater.UpdateError,
                    'post_update_validation_failed_manual_review_required'):
                self._check(today='2026-10-21')
        finally:
            updater.check_origin = original_check_origin
            updater.run_git = original_run_git

        self.assertTrue(injected)
        self.assertEqual(git('rev-parse', 'origin/main', cwd=self.source),
                         git('rev-parse', 'HEAD', cwd=self.source))

    def test_linked_source_path_is_rejected(self):
        alias = self.root / 'source-link'
        try:
            alias.symlink_to(self.source, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlinks are unavailable on this host')
        with self.assertRaisesRegex(updater.UpdateError, 'linked_path_not_allowed'):
            self._check(source=alias, today='2026-10-21', force=True)

    def test_candidate_symlink_is_rejected(self):
        blob = subprocess.run(
            ['git', 'hash-object', '-w', '--stdin'], cwd=self.author,
            input=b'outside.txt', capture_output=True, check=True,
        ).stdout.decode().strip()
        # Create a mode-120000 tree entry without requiring OS symlink privileges.
        git('update-index', '--add', '--cacheinfo', f'120000,{blob},linked.txt', cwd=self.author)
        git('commit', '-m', 'add linked candidate file', cwd=self.author)
        git('push', 'origin', 'main', cwd=self.author)
        with self.assertRaisesRegex(updater.UpdateError, 'candidate_contains_link_or_special_file'):
            self._check(today='2026-10-21')


class TestPowerShellInstaller(unittest.TestCase):
    def test_scheduled_task_is_scoped_to_current_user(self):
        text = (SCRIPT.parents[1]/'Enable-ADT-AutoUpdate.ps1').read_text(encoding='utf-8')
        self.assertIn('New-ScheduledTaskTrigger -Daily', text)
        self.assertIn('New-ScheduledTaskTrigger -AtLogOn -User $identity', text)
        self.assertIn('-LogonType Interactive -RunLevel Limited', text)
        self.assertIn('Register-ScheduledTask', text)
        self.assertIn('Unregister-ScheduledTask', text)
        self.assertIn('Get-FileHash', text)
        self.assertIn('Install-ADTUpdaterAtomically', text)
        self.assertIn('[IO.File]::Replace', text)
        self.assertIn('[IO.File]::Move', text)
        self.assertIn('Get-FileHash -LiteralPath $temporary', text)
        self.assertNotIn('Copy-Item -LiteralPath $bundledUpdater -Destination $installed -Force', text)
        self.assertIn('Assert-ADTNoReparseChain', text)
        self.assertIn('Assert-ADTNoReparseChain $bundledUpdater', text)
        self.assertIn('Assert-ADTNoReparseChain $targetDir', text)
        self.assertIn('Assert-ADTNoReparseChain $stateDir', text)
        self.assertNotIn('Set-ExecutionPolicy', text)
        self.assertNotIn('mcp remove', text)


class TestUnixInstaller(unittest.TestCase):
    def test_updater_install_and_initial_check_are_recovery_safe(self):
        text = (SCRIPT.parents[1] / 'Enable-ADT-AutoUpdate.sh').read_text(encoding='utf-8')
        self.assertIn('temporary=$(mktemp "$root/updater/.update_toolkit.py.tmp.XXXXXX")', text)
        self.assertIn('cp -p "$package/updater/update_toolkit.py" "$temporary"', text)
        self.assertIn('mv -f "$temporary" "$updater"', text)
        self.assertNotIn('cp "$package/updater/update_toolkit.py" "$updater"', text)
        self.assertIn('if ! python3 "$updater" --source "$source" --state-dir "$state" --force; then', text)
        self.assertIn('scheduler registration continues for the next run', text)

if __name__ == '__main__':
    unittest.main()
