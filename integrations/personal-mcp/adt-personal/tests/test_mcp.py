"""Offline contract/security/transport tests against a synthetic Toolkit checkout."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'mcp'))
from adt_mcp import Toolkit, ToolkitError, process, dispatch

SCRIPT = Path(__file__).resolve().parents[1] / 'mcp' / 'adt_mcp.py'

class TestToolkitMCP(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.manifest = {
          'package': 'ai-development-toolkit', 'version': '5.4.0',
          'core_skills': ['qa-strategy','feature-delivery','ux-ui-design-orchestra','task-scoping','implementation'],
          'extension_skills': [], 'core_roles': ['orchestrator'],
          'profiles': {'general':['qa-strategy'], 'qa-core':['qa-strategy'],
                       'backend':['task-scoping','api-design','implementation','qa-strategy'],
                       'frontend':['task-scoping','component-architecture','implementation'],
                       'fullstack':['task-scoping','end-to-end-feature-design','implementation'],
                       'qa-python':['test-analysis-design','api-testing','pytest-test-design'],
                       'qa-ui':['playwright-testing','test-analysis-design'],
                       'codex-feature':['feature-delivery','qa-strategy'],
                       'ui-orchestra':['ux-ui-design-orchestra'], 'ux-design':['ux-ui-design-process'],
                       'make-feature':['feature-delivery','make-feature'],
                       'prompt-refinement':['prompt-refinement'],
                       'seo-audit':['seo-audit']},
          'extension_packs': {'qa':{'skill_root':'extensions/qa/skills', 'skills':['test-analysis-design','api-testing','pytest-test-design','playwright-testing'],
                                    'role_root':'extensions/qa/roles','roles':['test-designer']},
                             'backend': {'skill_root': 'extensions/backend/skills', 'skills': ['api-design']},
                             'frontend': {'skill_root': 'extensions/frontend/skills', 'skills': ['component-architecture']},
                             'fullstack': {'skill_root': 'extensions/fullstack/skills', 'skills': ['end-to-end-feature-design']},
                             'ai': {'skill_root': 'extensions/ai/skills', 'skills': ['prompt-refinement']},
                             'seo': {'skill_root': 'extensions/seo/skills', 'skills': ['seo-audit']}}
        }
        (self.path / 'MANIFEST.json').write_text(json.dumps(self.manifest),encoding='utf-8')
        for name in self.manifest['core_skills']:
            p = self.path / '.agents' / 'skills' / name / 'SKILL.md'
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f'---\nname: {name}\ndescription: used for QA and coding\n---\n\n# {name}\n', encoding='utf-8')
        for pack, names in [('qa', ['test-analysis-design','api-testing','pytest-test-design','playwright-testing']),
                            ('backend',['api-design']),('frontend',['component-architecture']),
                            ('fullstack',['end-to-end-feature-design']),
                            ('ai',['prompt-refinement']),('seo',['seo-audit'])]:
            for name in names:
                p = self.path / f'extensions/{pack}/skills/{name}/SKILL.md'
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_text('# Original skill\n',encoding='utf-8')
        ref = self.path / '.agents/skills/qa-strategy/references/rules.md'
        ref.parent.mkdir(exist_ok=True)
        ref.write_text('# Guardrails\n', encoding='utf-8')
        for root, role in [('.agents/roles','orchestrator'),('extensions/qa/roles','test-designer')]:
            p = self.path / root / (role+'.md')
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_text('# '+role, encoding='utf-8')
        (self.path / 'AGENT_START.ru.md').write_text('# Начало\n', encoding='utf-8')
        self.tk = Toolkit(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_info_read_no_mutations(self):
        before = {str(p.relative_to(self.path)):p.read_bytes() for p in self.path.rglob('*') if p.is_file()}
        self.assertEqual(self.tk.info()['toolkit_version'], '5.4.0')
        self.assertEqual(self.tk.info()['mcp_server_version'], '0.1.8')
        self.assertEqual(self.tk.info()['mcp_protocol_version'], '2025-06-18')
        self.assertEqual(self.tk.read('skill','test-analysis-design')['content'], '# Original skill\n')
        self.assertEqual(self.tk.read('role','test-designer')['content'], '# test-designer')
        self.assertIn('orchestrator', self.tk.roles)
        after = {str(p.relative_to(self.path)):p.read_bytes() for p in self.path.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_catalog_and_slicing(self):
        self.assertGreaterEqual(self.tk.catalog('profiles', 'qa')['count'],1)
        self.assertEqual(self.tk.read('skill','qa-strategy',offset=0,limit=4)['content'],'---\n')
        self.assertTrue(self.tk.read('skill','qa-strategy',limit=4)['truncated'])
        self.assertIn('Guardrails',self.tk.reference('qa-strategy','references/rules.md')['content'])
        with self.assertRaises(ToolkitError):self.tk.reference('qa-strategy','../feature-delivery/SKILL.md')
        with self.assertRaises(ToolkitError):self.tk.reference('qa-strategy','/etc/passwd')
        with self.assertRaises(ToolkitError): self.tk.read('skill','../../etc/passwd')
        with self.assertRaises(ToolkitError): self.tk.read('skill','qa-strategy',limit=40000)

    def test_route(self):
        self.assertEqual(self.tk.route('Проведи аудит интерфейса')['profile'],'ui-orchestra')
        self.assertEqual(self.tk.route('Проведи UX/UI аудит')['profile'],'ui-orchestra')
        self.assertEqual(self.tk.route('Реализуй новую функцию')['profile'],'codex-feature')
        self.assertEqual(self.tk.route('Нечёткий запрос')['profile'],'general')
        self.assertEqual(self.tk.route('Покрой проект тестами')['profile'],'qa-core')
        self.assertIn('Начало',self.tk.guide()['content'])
        self.assertEqual(self.tk.route('Anything', profile='qa-core')['profile'],'qa-core')
        self.assertIn('make-feature', self.tk.route('anything', profile='make-feature')['unavailable'])
        with self.assertRaises(ToolkitError):self.tk.route('anything',profile='qa-all')

    def test_prompt_and_seo_intent_routing(self):
        cases = (
            ('Сделай хороший промпт для Codex из черновика', 'prompt-refinement'),
            ('Составь промпт: приложение ломается на телефоне', 'prompt-refinement'),
            ('Write a prompt for my QA test review', 'prompt-refinement'),
            ('Проверь SEO моего сайта', 'seo-audit'),
            ('Почему страница не индексируется в Google?', 'seo-audit'),
            ('Audit my website SEO', 'seo-audit'),
            ('Исправь баг на странице', 'codex-feature'),
            ('Сделай сайт фитнес-клуба', 'ui-orchestra'),
        )
        for task, expected in cases:
            with self.subTest(task=task):
                self.assertEqual(expected, self.tk.route(task)['profile'])
        prepared = self.tk.prepare_task('Проверь SEO сайта',
                                        existing_skills=[], existing_roles=[])
        self.assertEqual(prepared['primary_profile'], 'seo-audit')
        self.assertIn('seo-audit', prepared['skills_to_consult'])
        self.assertEqual(prepared['loaded_skills'][0]['name'], 'seo-audit')
        self.assertFalse(prepared['project_files_changed'])
        exported = self.tk.prepare_task('Сделай промпт для Codex',
                                        existing_skills=[], existing_roles=[])
        self.assertEqual(exported['primary_profile'], 'prompt-refinement')
        self.assertEqual(exported['loaded_skills'][0]['name'], 'prompt-refinement')

    def test_composite_routes(self):
        cases = [
            ('Создать REST API на FastAPI и покрыть его тестами pytest', 'backend', ['qa-python']),
            ('Исправь дефект в обработке параметров REST API на Python и проверь тестами', 'backend', ['qa-core']),
            ('Исправь ошибку REST API на Python и покрой его тестами', 'backend', ['qa-core']),
            ('Create REST API with FastAPI and test it with pytest', 'backend', ['qa-python']),
            ('Покрой существующий FastAPI тестами pytest', 'qa-python', []),
            ('Добавь тесты pytest для REST API', 'qa-python', []),
            ('Реализуй API-тесты pytest для существующего FastAPI', 'qa-python', []),
            ('Создай FastAPI сервис и напиши для него unit-тесты', 'backend', ['qa-core']),
            ('Реализуй новую функцию и добавь тесты pytest', 'codex-feature', ['qa-python']),
            ('Исправь баг во фронтенде React и добавь E2E тесты Playwright', 'frontend', ['qa-ui']),
            ('Исправь тесты pytest для FastAPI', 'qa-python', []),
            ('Разработай frontend React и backend FastAPI с тестами pytest', 'fullstack', ['qa-python']),
            ('Сделай сайт и покрой его тестами', 'ui-orchestra', []),
            ('Хочу красивый современный сайт фитнес-клуба', 'ui-orchestra', []),
            ('Проведи UX/UI аудит интерфейса', 'ui-orchestra', []),
            ('Покрой проект тестами', 'qa-core', []),
            ('Реализуй новую функцию', 'codex-feature', []),
        ]
        for task, primary, additions in cases:
            with self.subTest(task=task):
                result = self.tk.route(task)
                self.assertEqual(result['profile'], primary)
                self.assertEqual(result['secondary_profiles'], additions)
                self.assertEqual(len(result['skills']), len(set(result['skills'])))
                self.assertLessEqual(len(result['priority_skills']), 8)
                self.assertEqual(result['source_revision'], 'UNAVAILABLE')
        result = self.tk.route('Создать REST API на FastAPI и покрыть его тестами pytest')
        self.assertIn('api-design', result['priority_skills'])
        self.assertIn('pytest-test-design', result['priority_skills'])
        self.assertIn('api-testing', result['priority_skills'])
        self.assertEqual(result['matches_by_profile']['qa-python'], ['pytest'])
        self.assertEqual(result['skills'].count('task-scoping'), 1)
        visual = self.tk.route('Сделай сайт и покрой его тестами')
        self.assertEqual(visual['visual_phase'], 'create-design')
        self.assertEqual(visual['deferred_profiles'], ['frontend', 'qa-core'])
        self.assertEqual(visual['skills'], ['ux-ui-design-orchestra'])
        explicit = self.tk.route('Создать REST API на FastAPI и покрыть его тестами pytest', profile='qa-python')
        self.assertEqual(explicit['profile'], 'qa-python')
        self.assertEqual(explicit['secondary_profiles'], [])

    def test_prepare_task_auto_missing_skills_no_project_write(self):
        before = {str(p.relative_to(self.path)): p.read_bytes()
                  for p in self.path.rglob('*') if p.is_file()}
        r = self.tk.prepare_task('Создать REST API на FastAPI и покрыть тестами pytest',
                                 existing_skills=['api-design', 'task-scoping'],
                                 existing_roles=['orchestrator'], max_skills=4)
        self.assertEqual(r['primary_profile'], 'backend')
        self.assertEqual(r['secondary_profiles'], ['qa-python'])
        self.assertIn('api-design', r['already_available_skills'])
        self.assertNotIn('api-design', [x['name'] for x in r['loaded_skills']])
        self.assertIn('pytest-test-design', r['skills_to_consult'])
        self.assertEqual(r['loaded_roles'], [])
        self.assertEqual(r['usage_status'], 'GUIDANCE_LOADED_NOT_NATIVE_SKILL_ACTIVATION')
        self.assertFalse(r['installation_performed'])
        self.assertFalse(r['project_files_changed'])
        self.assertLessEqual(len(r['loaded_skills']), 4)
        after = {str(p.relative_to(self.path)): p.read_bytes()
                 for p in self.path.rglob('*') if p.is_file()}
        self.assertEqual(before, after)

    def test_prepare_task_no_inventory_is_unknown_and_role_loads(self):
        result = self.tk.prepare_task('Реализуй новую функцию', max_skills=3)
        self.assertEqual(result['existing_skills_status'], 'NOT_PROVIDED')
        self.assertEqual(result['missing_skills'], [])
        self.assertEqual(result['role_to_consult'], 'orchestrator')
        self.assertEqual(len(result['loaded_roles']), 1)
        self.assertTrue(result['loaded_skills'])
        self.assertEqual(result['loaded_skills'][0]['provenance'], 'LOCAL_SOURCE_GUIDANCE_ONLY')

    def test_prepare_task_validation_and_rpc(self):
        for kwargs in ({'existing_skills':'api-design'},
                       {'existing_roles':['ok',1]}, {'max_skills':False},
                       {'max_skills':9}):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ToolkitError):
                    self.tk.prepare_task('Сделай API', **kwargs)
        rpc = process(self.tk, {'jsonrpc':'2.0','id':10,'method':'tools/call',
                                'params':{'name':'toolkit_prepare_task',
                                          'arguments':{'task':'Разработай FastAPI и тесты pytest',
                                                       'existing_skills':['api-design'],
                                                       'existing_roles':[]}}})
        self.assertEqual(rpc['id'],10)
        self.assertIn('loaded_skills', rpc['result']['structuredContent'])
        self.assertNotIn('error', rpc)

    def test_git_revision_and_dirty_worktree(self):
        if not shutil.which('git'):
            self.skipTest('Git executable not available')
        cmds = [
            ['git','init','-q'],
            ['git','-c','user.name=Local-Test','-c','user.email=local-test@example.invalid',
             'add','MANIFEST.json'],
            ['git','-c','user.name=Local-Test','-c','user.email=local-test@example.invalid',
             'commit','-qm','fixture'],
        ]
        for command in cmds:
            result = subprocess.run(command, cwd=self.path, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
        new_tk = Toolkit(self.path)
        self.assertRegex(new_tk.info()['source_revision'], r'^[a-f0-9]{40}$')
        self.assertEqual(new_tk.info()['working_tree_status'], 'CLEAN_TRACKED')
        # HEAD remains accurate but does not assert clean state after modifying tracked files.
        manifest = self.path / 'MANIFEST.json'
        manifest.write_text(manifest.read_text('utf-8')+'\n', encoding='utf-8')
        dirty = Toolkit(self.path)
        self.assertEqual(dirty.info()['source_revision'], new_tk.info()['source_revision'])
        self.assertEqual(dirty.info()['working_tree_status'], 'MODIFIED_TRACKED')
        before = self.path / 'untracked-check.tmp'
        before.write_text('do not modify', encoding='utf-8')
        self.assertEqual(Toolkit(self.path).info()['working_tree_status'], 'MODIFIED_TRACKED')
        self.assertEqual(before.read_text('utf-8'), 'do not modify')

    def test_symlink_rejected(self):
        external = self.path / 'external.md'
        external.write_text('unsafe',encoding='utf-8')
        p=self.path / '.agents/skills/qa-strategy/SKILL.md'
        p.unlink()
        try: p.symlink_to(external)
        except OSError: self.skipTest('Symlinks unavailable')
        with self.assertRaises(ToolkitError): self.tk.read('skill','qa-strategy')

    def test_json_rpc(self):
        init=process(self.tk,{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}})
        self.assertEqual(init['result']['serverInfo']['name'],'ai-development-toolkit-personal')
        self.assertEqual(init['result']['serverInfo']['version'],'0.1.8')
        self.assertEqual(len(process(self.tk,{'jsonrpc':'2.0','id':2,'method':'tools/list'})['result']['tools']),8)
        route=process(self.tk,{'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'toolkit_route_task','arguments':{'task':'Проведи аудит интерфейса'}}})
        self.assertEqual(route['result']['structuredContent']['profile'],'ui-orchestra')
        self.assertIsNone(process(self.tk,{'jsonrpc':'2.0','method':'notifications/initialized'}))
        unknown=process(self.tk,{'jsonrpc':'2.0','id':5,'method':'tools/call','params':{'name':'undefined','arguments':{}}})
        self.assertEqual(unknown['error']['code'],-32602)
        bad=process(self.tk,{'jsonrpc':'2.0','id':6,'method':'tools/call','params':{'name':'toolkit_get_skill','arguments':{'name':'nope'}}})
        self.assertTrue(bad['result']['isError'])

    def test_diagnostic_stdio_roundtrip(self):
        runner = Path(__file__).resolve().parents[1] / 'diagnose_mcp.py'
        completed = subprocess.run(
            [sys.executable, str(runner), '--launcher', str(SCRIPT), '--source', str(self.path)],
            capture_output=True, text=True, encoding='utf-8', timeout=20)
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        summary = json.loads(completed.stdout)
        self.assertEqual(summary['status'], 'PASS')
        self.assertEqual(summary['request_count'], 46)
        self.assertEqual(summary['response_count'], 46)
        self.assertEqual(summary['pilot_profile'], 'backend')
        self.assertEqual(summary['pilot_secondary_profiles'], ['qa-core'])

    def test_stdio_preserves_id_after_unhandled_skill_decode_error(self):
        # A corrupt SKILL.md must not leave clients waiting for a response ID.
        file = self.path / '.agents/skills/qa-strategy/SKILL.md'
        file.write_bytes(b'\xff\xfe\xfd')
        requests = [
            {'jsonrpc':'2.0','id':12,'method':'initialize','params':{'protocolVersion':'2025-06-18'}},
            {'jsonrpc':'2.0','id':42,'method':'tools/call',
             'params':{'name':'toolkit_get_skill','arguments':{'name':'qa-strategy'}}},
            {'jsonrpc':'2.0','id':43,'method':'tools/call',
             'params':{'name':'toolkit_route_task','arguments':{'task':'Исправь дефект REST API и проверь тестами'}}},
        ]
        result=subprocess.run([sys.executable,str(SCRIPT),'--source',str(self.path)],
                              input=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in requests),
                              text=True,capture_output=True,timeout=8,encoding='utf-8')
        self.assertEqual(result.returncode,0, result.stderr)
        replies=[json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual([r['id'] for r in replies],[12,42,43])
        self.assertEqual(replies[1]['error']['code'],-32603)
        self.assertEqual(replies[2]['result']['structuredContent']['profile'],'backend')


    def test_utf8_mcp_stdio_under_legacy_windows_code_page(self):
        # Simulate a Windows shell where Python's text stdio is cp1251.
        # The wire protocol must remain UTF-8 regardless of that setting.
        import os
        request = {'jsonrpc': '2.0', 'id': 19, 'method': 'tools/call',
                   'params': {'name': 'toolkit_get_guide',
                              'arguments': {'name': 'AGENT_START.ru.md'}}}
        wire_input = (json.dumps(request, ensure_ascii=False) + '\n').encode('utf-8')
        process_result = subprocess.run(
            [sys.executable, str(SCRIPT), '--source', str(self.path)],
            input=wire_input, capture_output=True, timeout=10,
            env={**os.environ, 'PYTHONIOENCODING': 'cp1251'})
        self.assertEqual(process_result.returncode, 0, process_result.stderr)
        text = process_result.stdout.decode('utf-8', errors='strict')
        payload = json.loads(text)
        self.assertEqual(payload['id'], 19)
        self.assertIn('Начало', payload['result']['structuredContent']['content'])

    def test_subprocess_stdio(self):
        requests=[
            {'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-06-18'}},
            {'jsonrpc':'2.0','method':'notifications/initialized'},
            {'jsonrpc':'2.0','id':2,'method':'tools/list'},
            {'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'toolkit_get_skill','arguments':{'name':'qa-strategy'}}},
        ]
        p=subprocess.run([sys.executable,str(SCRIPT),'--source',str(self.path)],
                         input=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in requests),
                         text=True, capture_output=True, timeout=5)
        self.assertEqual(p.returncode,0,p.stderr)
        lines=[json.loads(x) for x in p.stdout.splitlines()]
        self.assertEqual([x['id'] for x in lines],[1,2,3])
        self.assertIn('qa-strategy',lines[2]['result']['content'][0]['text'])

if __name__=='__main__':
    unittest.main()
