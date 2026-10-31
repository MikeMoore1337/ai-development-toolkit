"""Static assertions for the Windows installer (not a PowerShell runtime test)."""
import pathlib
import unittest

SCRIPT = pathlib.Path(__file__).resolve().parents[1] / 'Install-ADT-Personal.ps1'

class TestInstallerContract(unittest.TestCase):
    def test_codex_uses_successful_json_list_not_negative_probe(self):
        content = SCRIPT.read_text(encoding='utf-8')
        self.assertIn('mcp list --json | Out-String', content)
        self.assertIn('if (Test-CodexMcpExists $codexCommand.Source)', content)
        self.assertIn('if (-not (Test-CodexMcpExists $codexCommand.Source))', content)
        self.assertNotIn('& $codexCommand.Source mcp get ai-development-toolkit', content)

    def test_installs_stable_launcher_and_preserves_config(self):
        content = SCRIPT.read_text(encoding='utf-8')
        self.assertIn("'ADT-Personal\\mcp'", content)
        self.assertIn('mcp add ai-development-toolkit -- $python.Source @pyArgs $installedServer', content)
        self.assertIn('Backup-IfExists (Join-Path $codexHome \'config.toml\')', content)
        self.assertIn('Global instructions already up to date:', content)
        self.assertIn('toolkit_prepare_task', content)
        self.assertIn('Malformed ADT block', content)
        self.assertIn('Backup-IfExists $File', content)

    def test_installed_windows_pair_has_staged_check_and_rollback(self):
        content = SCRIPT.read_text(encoding='utf-8')
        self.assertIn("'mcp\\adt_discovery.py'", content)
        self.assertIn("'adt_discovery.py'", content)
        self.assertIn("Install verified MCP module pair", content)
        self.assertIn("Staged MCP module pair self-check failed", content)
        self.assertIn("Installed MCP module pair self-check failed", content)
        self.assertIn("Copy-Item -LiteralPath $stageDiscovery -Destination $installedDiscovery", content)
        self.assertIn("Copy-Item -LiteralPath (Join-Path $stage 'old_discovery.py')", content)
        self.assertIn("Backup-IfExists $installedDiscovery", content)

    def test_claude_missing_server_probe_nonterminating(self):
        content = SCRIPT.read_text(encoding='utf-8')
        self.assertIn('function Test-ClaudeMcpExists', content)
        self.assertIn("$ErrorActionPreference = 'Continue'", content)
        self.assertIn('if (Test-ClaudeMcpExists $claude.Source)', content)

    def test_required_setup_instructions_reach_both_platform_installers(self):
        for script in (SCRIPT, SCRIPT.with_suffix('.sh')):
            with self.subTest(script=script.name):
                content = script.read_text(encoding='utf-8')
                self.assertIn('installing missing task-required skills and tools', content)
                self.assertIn('Skill Manager `ensure` preview', content)
                self.assertIn('explicit reference-only/no-install requests', content)
                self.assertIn('never overwrite or adopt unmanaged files', content)
                self.assertIn('Verify files, client discovery and invocation separately', content)

if __name__ == '__main__': unittest.main()
