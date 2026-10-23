"""Offline Linux install smoke test; no writes to actual home or Codex settings."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1] / 'personal-mcp' / 'adt-personal'


@unittest.skipUnless(os.name == 'posix' and os.uname().sysname == 'Linux', 'Linux-only local smoke fixture')
class TestLinuxInstaller(unittest.TestCase):
    def test_install_preserves_global_rules_and_is_idempotent(self):
        with tempfile.TemporaryDirectory(prefix='adt-unix-test-') as temp:
            root = Path(temp)
            fake_home = root / 'home'
            fake_home.mkdir()
            source = root / 'sample-toolkit'
            source.mkdir()
            manifest = {
                'package': 'ai-development-toolkit', 'version': '5.4.0',
                'core_skills': ['implementation'], 'core_roles': ['orchestrator'],
                'profiles': {'general': ['implementation']}, 'extension_packs': {}
            }
            (source/'MANIFEST.json').write_text(json.dumps(manifest), encoding='utf-8')
            file = source/'.agents/skills/implementation/SKILL.md'
            file.parent.mkdir(parents=True)
            file.write_text('---\nname: implementation\ndescription: Checks\n---\n', encoding='utf-8')
            file = source/'.agents/roles/orchestrator.md'
            file.parent.mkdir(parents=True)
            file.write_text('Role guidance.\n', encoding='utf-8')
            git = shutil.which('git')
            assert git
            subprocess.run([git, 'init', '-q', str(source)], check=True)
            tools = root/'bin'; tools.mkdir()
            cli = tools/'codex'
            cli.write_text('''#!/bin/sh
if [ "$1" = mcp ] && [ "$2" = list ] && [ "$3" = --json ]; then
  printf '%s\\n' '[]'
elif [ "$1" = mcp ] && [ "$2" = add ]; then
  printf '%s\\n' "$*" >> "$FAKE_CODEX_CALLS"
else
  exit 2
fi
''')
            cli.chmod(0o700)
            global_agents = fake_home/'.codex/AGENTS.md'
            global_agents.parent.mkdir()
            global_agents.write_text('## Original organization rules\n', encoding='utf-8')
            log = root/'codex_calls'
            env = {**os.environ, 'HOME': str(fake_home), 'XDG_DATA_HOME': str(fake_home/'.local/share'),
                   'CODEX_HOME': str(fake_home/'.codex'), 'FAKE_CODEX_CALLS': str(log),
                   'PATH': str(tools) + os.pathsep + os.environ['PATH']}
            cmd = ['sh', str(BASE/'Install-ADT-Personal.sh'), '--source', str(source)]
            first = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
            self.assertEqual(first.returncode, 0, first.stderr + '\n' + first.stdout)
            self.assertIn('toolkit_prepare_task', global_agents.read_text(encoding='utf-8'))
            self.assertIn('Original organization rules', global_agents.read_text(encoding='utf-8'))
            before = global_agents.read_text(encoding='utf-8')
            second = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
            self.assertEqual(second.returncode, 0, second.stderr + '\n' + second.stdout)
            self.assertEqual(global_agents.read_text(encoding='utf-8'), before)
            self.assertEqual(len(log.read_text().splitlines()), 2)
            self.assertIn('--source', log.read_text())
            installed = fake_home/'.local/share/adt-personal/mcp'
            self.assertTrue((installed/'adt_mcp.py').is_file())
            self.assertTrue((installed/'adt_discovery.py').is_file())
            # Real process import from installed user directory, not source ZIP.
            direct = subprocess.run([
                'python3', str(installed/'adt_mcp.py'), '--source', str(source), '--check'
            ], capture_output=True, text=True, timeout=8)
            self.assertEqual(0, direct.returncode, direct.stderr)
            self.assertFalse((source/'.adt').exists())

            # A corrupt/missing support module gets repaired with backup, without
            # re-registering the MCP or changing organization instructions.
            (installed/'adt_discovery.py').write_text('not valid python syntax\n', encoding='utf-8')
            repaired = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=25)
            self.assertEqual(0, repaired.returncode, repaired.stderr)
            self.assertEqual((BASE/'mcp'/'adt_discovery.py').read_bytes(),
                             (installed/'adt_discovery.py').read_bytes())
            self.assertEqual(global_agents.read_text(encoding='utf-8'), before)
            self.assertEqual(len(log.read_text().splitlines()), 3)
            self.assertTrue(list(installed.glob('adt_discovery.py.adt-backup-*')))
            previous_server = (installed/'adt_mcp.py').read_bytes()
            previous_discovery = (installed/'adt_discovery.py').read_bytes()
            # A truncated candidate must not change an existing installation.
            invalid = root/'invalid-package'
            (invalid/'mcp').mkdir(parents=True)
            shutil.copy2(BASE/'Install-ADT-Personal.sh', invalid/'Install-ADT-Personal.sh')
            shutil.copy2(BASE/'mcp'/'adt_mcp.py', invalid/'mcp'/'adt_mcp.py')
            broken = subprocess.run([
                'sh', str(invalid/'Install-ADT-Personal.sh'), '--source', str(source)
            ], env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(2, broken.returncode)
            self.assertIn('Incomplete MCP source bundle', broken.stderr)
            self.assertEqual(previous_server, (installed/'adt_mcp.py').read_bytes())
            self.assertEqual(previous_discovery, (installed/'adt_discovery.py').read_bytes())
            self.assertEqual(len(log.read_text().splitlines()), 3)
