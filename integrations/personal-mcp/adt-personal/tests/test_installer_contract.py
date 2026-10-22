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

    def test_claude_missing_server_probe_nonterminating(self):
        content = SCRIPT.read_text(encoding='utf-8')
        self.assertIn('function Test-ClaudeMcpExists', content)
        self.assertIn("$ErrorActionPreference = 'Continue'", content)
        self.assertIn('if (Test-ClaudeMcpExists $claude.Source)', content)

if __name__ == '__main__': unittest.main()
