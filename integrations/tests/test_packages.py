"""Static validation of source-only integrations for distribution."""
import json
from pathlib import Path
import re
import unittest

BASE = Path(__file__).resolve().parents[1]


class SourcePackageTests(unittest.TestCase):
    def test_mcp_version_and_tools(self):
        server = (BASE / 'personal-mcp/adt-personal/mcp/adt_mcp.py').read_text(encoding='utf-8')
        self.assertIn("VERSION = '0.1.13'", server)
        for tool in ('toolkit_info', 'toolkit_get_skill', 'toolkit_get_role', 'toolkit_prepare_task', 'toolkit_model_review_checkpoint', 'toolkit_assess_skill_coverage', 'toolkit_discover_external_skill_candidates', 'toolkit_codex_prepare_delegation', 'toolkit_codex_review_delegation'):
            self.assertIn(tool, server)

    def test_plugin_manifest_and_skill_refs(self):
        folder = BASE / 'chatgpt-plugin/ai-development-toolkit'
        data = json.loads((folder / 'plugin.json').read_text(encoding='utf-8'))
        self.assertEqual(data['name'], folder.name)
        self.assertEqual(data['version'], '0.1.3')
        self.assertLessEqual(len(data['extensions']['com.openai']['interface']['shortDescription']), 30)
        self.assertNotIn('mcpServers', data)
        self.assertNotIn('apps', data.get('extensions', {}).get('com.openai', {}))
        for skill in ('toolkit-prompt-refinement', 'toolkit-seo-audit', 'toolkit-evidence-curator', 'toolkit-task-observer-opt-in'):
            self.assertTrue((folder / 'skills' / skill / 'SKILL.md').is_file())
            self.assertTrue((folder / 'skills' / skill / 'references').is_dir())
        router = (folder / 'skills/toolkit-task-router/SKILL.md').read_text(encoding='utf-8')
        self.assertIn('FULFILL_REQUEST', router)
        self.assertIn('EXPORT_PROMPT', router)
        for p in (folder / 'skills').glob('*/SKILL.md'):
            md = p.read_text(encoding='utf-8')
            self.assertTrue(md.startswith('---\n'))
            self.assertRegex(md, r'(?m)^name: '+re.escape(p.parent.name)+r'$')
            self.assertRegex(md, r'(?m)^description: .+')

    def test_docs_and_no_personal_plugin_identity(self):
        for path in ['personal-mcp/README.md', 'personal-mcp/README.ru.md', 'chatgpt-plugin/README.md', 'chatgpt-plugin/README.ru.md']:
            self.assertTrue((BASE / path).is_file())
        for path in (BASE / 'chatgpt-plugin').rglob('*'):
            if path.is_file():
                self.assertNotIn('plugins_6',path.read_text(encoding='utf8'))
                self.assertNotIn('pluginrel_',path.read_text(encoding='utf8'))

    def test_integration_docs_do_not_rank_chatgpt_or_codex(self):
        for name in (
            'personal-mcp/README.ru.md',
            'chatgpt-plugin/README.ru.md',
            'README.ru.md',
        ):
            text = (BASE / name).read_text(encoding='utf-8')
            for forbidden in (
                'Дополнительный вариант: локальный MCP',
                'Основной вариант для чат-бота',
                'ChatGPT прежде всего',
                'ChatGPT-first',
            ):
                self.assertNotIn(forbidden, text, name)
        mcp_guide = (BASE / 'personal-mcp/README.ru.md').read_text(encoding='utf-8')
        self.assertIn('равноправных способов подключения', mcp_guide)

    def test_unix_install_and_updater_are_present_and_safe_defaults(self):
        server = BASE / 'personal-mcp/adt-personal'
        for name in ('Install-ADT-Personal.sh', 'Enable-ADT-AutoUpdate.sh'):
            content = (server / name).read_text(encoding='utf-8')
            self.assertTrue(content.startswith('#!/bin/sh'))
            self.assertIn('set -eu', content)
            self.assertNotRegex(content, r'(?m)^\s*sudo\s')
        self.assertIn('systemctl --user', (server / 'Enable-ADT-AutoUpdate.sh').read_text())
        self.assertIn('launchctl bootstrap', (server / 'Enable-ADT-AutoUpdate.sh').read_text())
        shell = (server / 'Enable-ADT-AutoUpdate.sh').read_text()
        self.assertIn('reject_linked_path', shell)
        self.assertIn('while [ -n "$path" ]; do', shell)
        self.assertIn('reject_linked_path "$root/updater"', shell)

    def test_platform_guides_and_equal_visibility(self):
        for name in ('personal-mcp/README.md', 'personal-mcp/README.ru.md'):
            text = (BASE / name).read_text(encoding='utf-8')
            for token in ('Windows', 'Linux', 'macOS'):
                self.assertIn(token, text)
        for name in ('chatgpt-plugin/README.md', 'chatgpt-plugin/README.ru.md'):
            text = (BASE / name).read_text(encoding='utf-8')
            for token in ('Windows', 'Linux', 'macOS'):
                self.assertIn(token, text)
        self.assertTrue((BASE / 'chatgpt-plugin/ai-development-toolkit/skills/toolkit-task-router/references/CHAT_WORKFLOWS.md').is_file())
        root = BASE.parent
        for rel in ('docs/INTEGRATIONS.md', 'docs/ru/INTEGRATIONS.md',
                    'integrations/README.md', 'integrations/README.ru.md'):
            overview = (root / rel).read_text(encoding='utf-8')
            self.assertIn('chatgpt-plugin/README', overview, rel)
            self.assertIn('personal-mcp/README', overview, rel)
            self.assertNotIn('ChatGPT-first', overview, rel)
            self.assertNotIn('ChatGPT first', overview, rel)
            self.assertNotIn('прежде всего ChatGPT', overview, rel)
            self.assertNotIn('MCP (дополнительный)', overview, rel)
            self.assertNotIn('MCP (optional)', overview, rel)



if __name__ == '__main__':
    unittest.main()
