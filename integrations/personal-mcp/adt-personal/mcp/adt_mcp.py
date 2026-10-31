#!/usr/bin/env python3
"""Personal, read-only AI Development Toolkit MCP stdio adapter (stdlib only)."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any
from adt_discovery import DiscoveryDenied, discover as discover_pinned_skills

NAME = 'ai-development-toolkit-personal'
VERSION = '0.1.14'
PROTOCOL = '2025-06-18'

# Routing guidance only; the toolkit manifest remains the source of truth.
ROUTES: tuple[tuple[str, tuple[str, ...]], ...] = (
    # Only explicit prompt-writing requests use EXPORT_PROMPT; ordinary tasks remain actionable.
    ('prompt-refinement', ('сделай промпт', 'составь промпт', 'напиши промпт',
                           'улучши промпт', 'адаптируй промпт', 'перепиши промпт',
                           'промпт для', 'хороший промпт', 'формулируй запрос для ии',
                           'improve prompt', 'rewrite prompt', 'write a prompt',
                           'create a prompt', 'prompt for', 'turn into a prompt')),
    ('seo-audit', ('seo', 'сео', 'поисковая оптимизац', 'поисковую оптимизац',
                   'сео аудит', 'индексац страниц', 'не индексируется',
                   'indexability', 'search engine optimization', 'sitemap.xml',
                   'robots.txt', 'canonical url')),
    ('ui-orchestra', ('ux audit', 'ui audit', 'ux/ui аудит', 'ui/ux аудит', 'аудит ux', 'аудит ui', 'design audit', 'design orchestra', 'аудит интерфейс', 'аудит дизай', 'оцени интерфейс', 'проверь дизайн', 'review ui')),
    ('ui-motion', ('animation', 'motion', 'анимац', 'переходы интерфейс')),
    ('ux-design', ('design landing', 'design screen', 'user flow', 'wireframe', 'нарисуй дизайн', 'дизайн лендинг', 'спроектируй интерфейс', 'проектировани ux')),
    ('ui-fix', ('pixel perfect', 'visual mismatch', 'screenshot', 'визуальн', 'скриншот', 'исправь верстк', 'поправь интерфейс')),
    ('accessibility-qa', ('accessibility', 'a11y', 'wcag', 'доступност', 'скринридер')),
    ('qa-security', ('пентест', 'security testing', 'тест безопасност', 'уязвимост', 'vulnerability')),
    ('security-engineering', ('security architecture', 'authz', 'authentication', 'авторизац', 'аутентификац', 'безопасност')),
    ('observability-sre', ('incident', 'observability', 'slo', 'sre', 'инцидент', 'логировани', 'мониторинг')),
    ('ai-engineering-qa', ('rag', 'llm evaluation', 'prompt regression', 'tool use', 'проверка llm', 'тестировани ии', 'оценка модели')),
    ('performance-load-testing', ('нагрузочн', 'load test', 'latency benchmark', 'производительност тест')),
    ('dependency-maintenance', ('обнови зависимост', 'dependency update', 'upgrade packages', 'dependabot', 'renovate')),
    ('qa-ci', ('flaky', 'нестабильн тест', 'pipeline fail', 'ci failure', 'падает ci', 'ошибк ci')),
    ('qa-ui', ('e2e', 'playwright', 'ui test', 'тест ui', 'тест интерфейс', 'браузерн тест')),
    ('qa-python', ('pytest', 'python тест', 'тест python', 'тест api на python')),
    ('qa-contract', ('contract test', 'контрактн тест', 'совместимост api')),
    ('qa-release', ('release gate', 'регрессионн', 'релизн проверк', 'проверка релиз')),
    ('qa-core', ('test cases', 'тест-кейс', 'тестировани', 'покрой тест', 'покрой проект', 'покрой код', 'тестами', 'тесты', 'тестов', 'unit test', 'unit-тест', 'tests', 'протестиру', 'написать тест', 'напиши тест', 'добавь тест', 'qa audit', 'проверь качеств')),
    ('backend', ('backend', 'бэкенд', 'бэкенда', 'серверн', 'api endpoint', 'api метод', 'базу данных', 'fastapi', 'django', 'flask', 'rest api', 'restful api', 'graphql', 'grpc', 'эндпоинт', 'эндпойнт', 'api')),
    ('frontend', ('frontend', 'фронтенд', 'фронтенда', 'react', 'vue', 'svelte', 'компонент ui', 'сайт', 'лендинг', 'веб-приложен', 'web app')),
    ('fullstack', ('fullstack', 'фулстек', 'сквозн функци', 'ui и api', 'frontend and backend')),
    ('data-engineering', ('data pipeline', 'etl', 'хранилище данных', 'миграция данных')),
    ('devops-infrastructure', ('docker', 'kubernetes', 'terraform', 'инфраструктур', 'devops', 'деплой')),
    ('maintenance-support', ('maintenance', 'обслуживан', 'support workflow', 'поддержка продукта')),
    ('business-system-analysis', ('бизнес анализ', 'требовани систем', 'use case', 'user story')),
    ('product-discovery', ('product discovery', 'продуктовая гипотез', 'исследовани продукт')),
    ('research', ('research', 'исследуй', 'изучи подход', 'сравни подход')),
    ('docs-technical', ('readme', 'documentation', 'документац', 'инструкци')),
    ('codex-feature', ('реализуй', 'разработай', 'разработать', 'создай', 'создать', 'сделай', 'добавь функцию', 'добавить функцию', 'feature', 'исправь баг', 'fix bug', 'implement', 'build', 'create')),
)

# Priority for explicit profiles. Only manifest-defined profile names are accepted.
SELECTABLE = set(x for x, _ in ROUTES)
CONFLICT_GROUP = frozenset({'make-feature', 'feature-delivery', 'adaptive-delivery'})
QA_PROFILES = frozenset({'qa-python', 'qa-ui', 'qa-contract', 'qa-ci', 'qa-release', 'qa-security', 'qa-core'})
VISUAL_CREATION_TERMS = ('сделай сайт', 'создай сайт', 'создать сайт', 'разработай сайт',
                         'современный сайт', 'красивый сайт', 'лендинг', 'landing page',
                         'нарисуй интерфейс', 'спроектируй интерфейс', 'новый интерфейс',
                         'дизайн сайта', 'дизайн интерфейса', 'редизайн', 'redesign',
                         'создай экран', 'нарисуй экран')
BUILD_TERMS = ('реализуй', 'реализовать', 'разработай', 'разработать', 'создай', 'создать', 'сделай',
               'исправь баг', 'исправить баг', 'почини баг', 'исправь дефект', 'исправить дефект',
               'исправь ошибку', 'исправить ошибку', 'почини ошибку', 'fix bug', 'fix defect', 'refactor feature',
               'добавь', 'добавить', 'построй', 'build', 'create', 'implement', 'develop', 'напиши код')
TEST_ONLY_ACTIONS = ('создай тест', 'создать тест', 'реализуй тест', 'разработай тест',
                     'исправь тест', 'исправить тест', 'почини тест', 'fix test',
                     'сделай тест', 'добавь тест', 'разработай e2e тест', 'реализуй api-тест', 'создай api-тест', 'разработай api-тест', 'create api test', 'create test', 'implement test', 'build test')
# Read at most the highest-signal skills first; all selected skills remain available in `skills`.
PRIORITY_SKILLS = {
    'backend': ('api-design', 'service-architecture', 'implementation', 'qa-strategy'),
    'frontend': ('component-architecture', 'frontend-api-integration', 'implementation', 'qa-strategy'),
    'fullstack': ('end-to-end-feature-design', 'fullstack-integration', 'implementation', 'qa-strategy'),
    'codex-feature': ('task-scoping', 'feature-delivery', 'implementation', 'qa-strategy'),
    'qa-python': ('api-testing', 'pytest-test-design', 'test-analysis-design', 'test-review'),
    'qa-ui': ('playwright-testing', 'e2e-testing', 'test-review'),
    'qa-contract': ('contract-testing', 'integration-testing'),
    'qa-core': ('test-analysis-design', 'test-review', 'quality-gate-assessment'),
    'ui-orchestra': ('ux-ui-design-orchestra', 'design-system-consistency', 'screenshot-fidelity'),
    'prompt-refinement': ('prompt-refinement',),
    'seo-audit': ('seo-audit', 'research-verification'),
}


def _explicit_prompt_request(task: str) -> bool:
    """Recognize a requested prompt artifact, not an instruction to execute one."""
    text = ' '.join(task.casefold().replace('ё', 'е').split())
    if 'промпт' not in text and 'prompt' not in text:
        return False
    noun = r'(?:промпт\w*|prompt\w*)'
    patterns = (
        r'(?<!\w)(?:сделай|создай|составь|напиши|улучши|адаптируй|перепиши|'
        r'подготовь|сформулируй|составить|написать|улучшить|адаптировать|'
        r'переписать|помоги составить)\s+'
        r'(?:(?:хороший|нормальный|качественный|детальный|подробный|отличный|'
        r'четкий|понятный|готовый|мой|этот|мне)\s+){0,3}' + noun + r'\b',
        r'(?<!\w)(?:сделай|создай|преврати|составь)\s+из\b.{0,150}\b'
        + noun + r'\b',
        r'(?<!\w)(?:хочу|нужен|дай|нужна)\s+'
        r'(?:(?:хороший|нормальный|качественный|подробный|готовый|мне)\s+){0,3}'
        + noun + r'\b',
        r'(?<!\w)(?:make|write|create|rewrite|improve|adapt|draft)\s+'
        r'(?:(?:me|a|an|the|my|this|good|better|detailed|professional)\s+){0,4}'
        r'prompt\w*\b',
        r'\bturn\b.{0,120}\binto\s+(?:a\s+)?prompt\b',
    )
    return any(re.search(pattern, text) for pattern in patterns)


def match_term(text: str, term: str) -> bool:
    """Match ASCII terms at word boundaries; allow inflected Russian word stems."""
    if not term:
        return False
    if term[0].isascii() and term[0].isalnum():
        return re.search(r'(?<!\w)' + re.escape(term) + r'(?!\w)', text) is not None
    return term in text


def _split_explicit_prohibitions(task: str) -> tuple[str, list[str]]:
    """Bounded prefix-only exclusions, not semantic language understanding."""
    negative_start = re.compile(
        r"^(?:не\s+(?:нужен|нужна|нужно|нужны|надо|хочу|делай|проводи|создавай)|"
        r"do\s+not|don't|skip|no\s+need\s+to)\b", re.I)
    actionable, excluded = [], []
    for chunk in re.split(r"\s*;\s*", task):
        chunk = chunk.strip()
        if not chunk:
            continue
        if negative_start.match(chunk):
            pieces = re.split(r"[:,]\s*", chunk, maxsplit=1)
            excluded.append(pieces[0])
            if len(pieces) == 2 and len(pieces[1].split()) >= 2:
                actionable.append(pieces[1])
        else:
            actionable.append(chunk)
    return "; ".join(actionable), excluded


def has_build_intent(text: str) -> bool:
    """Distinguish code implementation from commands that only create tests."""
    without_test_commands = text
    for term in TEST_ONLY_ACTIONS:
        if term[0].isascii():
            without_test_commands = re.sub(r'(?<!\w)' + re.escape(term) + r'\w*', ' ', without_test_commands)
        else:
            without_test_commands = re.sub(re.escape(term) + r'\w*', ' ', without_test_commands)
    return any(match_term(without_test_commands, term) for term in BUILD_TERMS)

def _model_review_hint(task: str, observed_findings: list[str] | None = None) -> dict[str, Any]:
    """Bounded read-only risk hint for an opted-in Codex client.

    Reuses the existing task and route; this is NOT a model-selection engine.
    Model inventory, execution capability, user consent and cost are never
    established by task keywords or the Personal MCP server.
    """
    if observed_findings is None:
        observed_findings = []
    if (not isinstance(observed_findings, list) or len(observed_findings) > 8
            or any(not isinstance(x, str) or not 1 <= len(x) <= 320
                   or any(ord(c) < 32 for c in x)
                   for x in observed_findings)):
        raise ToolkitError('observed_findings must be up to 8 bounded plain-text observations')
    actionable, _ = _split_explicit_prohibitions(task)
    # Findings are data supplied by the host, NOT instructions to be executed.
    # Return only fixed enum values; never reflect private or malicious input.
    combined = actionable + ' ; ' + ' ; '.join(observed_findings)
    text = ' '.join(combined.casefold().replace('ё', 'е').split())[:8000]
    def hit(terms: tuple[str, ...]) -> bool:
        return any(match_term(text, term) for term in terms)

    security = hit(('безопасност', 'уязвимост', 'security', 'vulnerability',
                    'authorization', 'authz', 'threat model', 'цепочк поставок',
                    'git hooks', 'git hook', 'core.hookspath', 'origin spoofing',
                    'symlink traversal', 'hardlink', 'reparse'))
    concurrency = hit(('конкурентн', 'гонк', 'блокировк', 'race condition',
                       'concurrency', 'deadlock', 'toctou', 'locking', 'os-lock',
                       'os lock', 'advisory lock', 'file lock', 'stale lock'))
    integrity = hit(('откат', 'восстановлен', 'потеря данных', 'поврежден',
                     'атомарн', 'журнал', 'reparse', 'symlink', 'git origin',
                     'rollback', 'recovery', 'data loss', 'state corruption',
                     'atomic', 'journal', 'fsync', 'hardlink', 'fetch_head',
                     'interrupted update', 'прерыван', 'pending journal'))
    migration = hit(('миграц', 'migration', 'schema change', 'breaking change'))
    architecture = hit(('архитектур', 'architecture', 'cross-system',
                        'нескольких сервис', 'multiple services'))
    review = hit(('аудит', 'audit', 'review', 'ревью', 'проверь', 'verify',
                  'провер', 'analyse', 'analyze', 'исправь', 'fix'))
    routine_docs = hit(('опечатк', 'typo', 'readme', 'документац',
                        'documentation', 'инструкци')) and not (
                        concurrency or integrity or migration)

    # Only combined concrete risks merit interrupting ordinary development.
    # A mere mention of "security" or a routine README request is not enough.
    signal = (
        (security and (concurrency or integrity or migration))
        or (migration and (concurrency or integrity))
        or (architecture and security and review)
    ) and not routine_docs
    reason = ('MULTI_BOUNDARY_SECURITY_REVIEW' if security and (concurrency or integrity)
              else 'MIGRATION_RECOVERY_REVIEW' if migration and (concurrency or integrity)
              else 'ARCHITECTURE_SECURITY_REVIEW' if signal
              else 'INSUFFICIENT_COMBINED_RISK_SIGNALS')
    from_new_findings = bool(observed_findings) and signal and (
        _model_review_hint(task)['status'] != 'REVIEW_CANDIDATE')
    return {
        'schema_version': 1,
        'status': 'REVIEW_CANDIDATE' if signal else 'NO_REVIEW_SIGNAL',
        'new_risk_boundary': from_new_findings,
        'risk_context': 'TASK_AND_CLIENT_FINDINGS' if observed_findings else 'TASK_ONLY',
        'findings_verification': ('CLIENT_REPORTED_NOT_INDEPENDENTLY_VERIFIED'
                                  if observed_findings else 'NOT_PROVIDED'),
        'reason_code': reason,
        'evidence': 'BOUNDED_TASK_LEXICAL_HEURISTIC_NOT_MODEL_INFERENCE',
        'model_inventory': 'NOT_OBSERVED_BY_PERSONAL_MCP',
        'available_models': [],
        'user_consent': 'NOT_REQUESTED',
        'advice_only': True,
        'execution': 'NOT_RUN',
        'extra_model_calls': 0,
        'client_action': ('EVALUATE_LIVE_INVENTORY_THEN_OFFER_OPTIONAL_CHAT_CHOICE'
                          if signal else 'CONTINUE_PRIMARY_MODEL_WITHOUT_ADVISOR_PROMPT'),
    }


class ToolkitError(Exception):
    pass

class Toolkit:
    def __init__(self, source: Path):
        self.source = source.expanduser().resolve(strict=True)
        if not self.source.is_dir():
            raise ToolkitError('Source must be a directory')
        manifest_path = self.source / 'MANIFEST.json'
        if not manifest_path.is_file() or manifest_path.is_symlink():
            raise ToolkitError('Toolkit MANIFEST.json missing or unsafe; pass --source to a local Toolkit checkout')
        try:
            self.manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        except (ValueError, OSError) as exc:
            raise ToolkitError(f'Cannot read Toolkit manifest: {exc}') from exc
        if self.manifest.get('package') != 'ai-development-toolkit':
            raise ToolkitError('Wrong Toolkit manifest')
        self.profiles = self.manifest.get('profiles', {})
        self.skills = self._skills()
        self.roles = self._roles()
        self.source_revision, self.working_tree_status = self._source_revision()

    def _source_revision(self) -> tuple[str, str]:
        """Report actual local Git HEAD, never fabricate a version from MANIFEST.json."""
        if not (self.source / '.git').exists() or not shutil.which('git'):
            return 'UNAVAILABLE', 'UNKNOWN'
        try:
            rev = subprocess.run(
                ['git', '-C', str(self.source), 'rev-parse', '--verify', 'HEAD^{commit}'],
                capture_output=True, text=True, timeout=4, check=False,
                env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'},
            )
            sha = rev.stdout.strip()
            if rev.returncode != 0 or not re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', sha):
                return 'UNAVAILABLE', 'UNKNOWN'
            status = subprocess.run(
                ['git', '-C', str(self.source), 'status', '--porcelain', '--untracked-files=no'],
                capture_output=True, text=True, timeout=4, check=False,
                env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'},
            )
            state = ('UNKNOWN' if status.returncode else
                     'MODIFIED_TRACKED' if status.stdout.strip() else 'CLEAN_TRACKED')
            return sha.lower(), state
        except (OSError, subprocess.TimeoutExpired):
            return 'UNAVAILABLE', 'UNKNOWN'

    def _safe_file(self, relative: str) -> Path:
        p = self.source / relative
        # Reject junction/symlink components even if the link resolves inside the source.
        cur = self.source
        for part in Path(relative).parts:
            if part in ('', '.', '..') or part.startswith('\\') or ':' in part:
                raise ToolkitError('Invalid relative path')
            cur = cur / part
            if cur.is_symlink():
                raise ToolkitError('Symlink files/paths are not allowed')
        try:
            real = p.resolve(strict=True)
        except (OSError, RuntimeError) as exc:
            raise ToolkitError(f'Declared Toolkit file is missing or inaccessible: {relative}') from exc
        if not real.is_relative_to(self.source) or not real.is_file():
            raise ToolkitError('File is outside the Toolkit source')
        return real

    def _skills(self) -> dict[str, str]:
        found: dict[str, str] = {}
        for name in self.manifest.get('core_skills', []) + self.manifest.get('extension_skills', []):
            found[name] = f'.agents/skills/{name}/SKILL.md'
        # Include other core skills present in the checkout, not only core_skills.
        core = self.source / '.agents' / 'skills'
        if core.is_dir():
            for p in sorted(core.iterdir()):
                if p.is_dir() and not p.is_symlink() and (p / 'SKILL.md').is_file():
                    found.setdefault(p.name, f'.agents/skills/{p.name}/SKILL.md')
        for entry in self.manifest.get('extension_packs', {}).values():
            root = entry.get('skill_root')
            if not root or not isinstance(root, str):
                continue
            for name in entry.get('skills', []):
                if isinstance(name, str):
                    found.setdefault(name, f'{root}/{name}/SKILL.md')
        return found

    def _roles(self) -> dict[str, str]:
        found = {name: f'.agents/roles/{name}.md' for name in self.manifest.get('core_roles', [])}
        for pack in self.manifest.get('extension_packs', {}).values():
            root = pack.get('role_root')
            if root:
                for name in pack.get('roles', []):
                    found.setdefault(name, f'{root}/{name}.md')
        return found

    def diagnostic(self, *, loaded_skills: list[str] | None = None) -> dict[str, Any]:
        """Local-source evidence only; never attest to host-client activation."""
        observed = [] if loaded_skills is None else list(dict.fromkeys(loaded_skills))
        return {
            'schema_version': 1,
            'adapter': 'PERSONAL_MCP',
            'adapter_version': VERSION,
            'toolkit_version': self.manifest.get('version', 'NOT_VERIFIED'),
            'source_sha': self.source_revision,
            'source_worktree': self.working_tree_status,
            # These are distinct identities. This stdio process has no access to
            # ChatGPT installation state or GitHub release status.
            'version_boundaries': {
                'running_mcp_adapter': VERSION,
                'toolkit_checkout_manifest': self.manifest.get('version', 'NOT_VERIFIED'),
                'toolkit_checkout_sha': self.source_revision,
                'published_github_release': 'NOT_VERIFIED',
                'installed_chatgpt_plugin': 'NOT_VERIFIED',
                'public_chatgpt_plugin_source': 'NOT_VERIFIED',
                'source_checkout_updater_enabled': 'NOT_VERIFIED',
                'mcp_package_auto_upgrade': False,
                'chatgpt_plugin_auto_upgrade': False,
            },
            'loaded_skills': observed,
            'loaded_skill_evidence': ('RETURNED_LOCAL_GUIDANCE' if observed else
                                      'NO_GUIDANCE_RETURNED_BY_THIS_CALL'),
            'fallback': 'NONE',
            'l4_client_discovery': 'NOT_VERIFIED',
            'l5_client_invocation': 'NOT_VERIFIED',
            'l6_client_benefit': 'NOT_MEASURED',
            'client_activation': 'NOT_VERIFIED',
            'target_execution': 'NOT_RUN',
            'project_files_changed': False,
        }

    def info(self) -> dict[str, Any]:
        return {'source': str(self.source), 'toolkit_version': self.manifest.get('version'),
                'mcp_server_version': VERSION, 'mcp_protocol_version': PROTOCOL,
                'skills': len(self.skills), 'profiles': len(self.profiles), 'roles': len(self.roles),
                'mode': 'READ_ONLY', 'execution': 'NONE', 'client_activation': 'NOT_VERIFIED',
                'source_revision': self.source_revision, 'working_tree_status': self.working_tree_status,
                'diagnostics': self.diagnostic()}

    def catalog(self, kind: str, query: str = '') -> dict[str, Any]:
        data = {'skills': self.skills, 'roles': self.roles, 'profiles': self.profiles}.get(kind)
        if data is None:
            raise ToolkitError('kind must be skills, roles or profiles')
        query = query.casefold().strip()
        results = [{'name': name, 'path': path} if kind != 'profiles'
                   else {'name': name, 'skills': path}
                   for name, path in sorted(data.items()) if query in name.casefold()]
        return {'kind': kind, 'count': len(results), 'items': results[:150]}

    def read(self, kind: str, name: str, offset: int = 0, limit: int = 16000) -> dict[str, Any]:
        names = self.skills if kind == 'skill' else self.roles if kind == 'role' else None
        if names is None or name not in names:
            raise ToolkitError('Unknown declared skill/role. Call toolkit_catalog first.')
        if not isinstance(offset, int) or offset < 0 or not isinstance(limit, int) or limit < 1 or limit > 32000:
            raise ToolkitError('Invalid offset/limit (limit 1..32000)')
        path = self._safe_file(names[name])
        data = path.read_text(encoding='utf-8')
        return {'name': name, 'path': names[name], 'content': data[offset:offset+limit],
                'offset': offset, 'total_chars': len(data), 'truncated': offset+limit < len(data),
                'provenance': 'LOCAL_SOURCE_GUIDANCE_ONLY'}

    def reference(self, skill: str, relative_path: str, offset: int = 0, limit: int = 16000) -> dict[str, Any]:
        if skill not in self.skills:
            raise ToolkitError('Unknown skill. Call toolkit_catalog first.')
        if not isinstance(relative_path, str) or not relative_path or '\\' in relative_path:
            raise ToolkitError('Reference path must be a nonempty relative POSIX path')
        reference = PurePosixPath(relative_path)
        if reference.is_absolute() or any(x in ('', '.', '..') for x in relative_path.split('/')):
            raise ToolkitError('Reference path traversal is forbidden')
        if reference.suffix.lower() not in ('.md', '.txt', '.json', '.yaml', '.yml', '.toml'):
            raise ToolkitError('Only textual supporting files can be read')
        if not isinstance(offset, int) or offset < 0 or not isinstance(limit, int) or not 1 <= limit <= 32000:
            raise ToolkitError('Invalid offset/limit')
        relative = str(PurePosixPath(self.skills[skill]).parent / reference)
        content = self._safe_file(relative).read_text(encoding='utf-8')
        return {'skill':skill,'path':relative,'content':content[offset:offset+limit],
                'offset':offset,'total_chars':len(content),'truncated':offset+limit < len(content),
                'provenance':'LOCAL_SOURCE_GUIDANCE_ONLY'}

    def guide(self, name: str = 'AGENT_START.ru.md', offset: int = 0, limit: int = 16000) -> dict[str, Any]:
        if name not in ('AGENT_START.ru.md', 'AGENT_START.md', 'AGENTS.md'):
            raise ToolkitError('Unsupported guide name')
        if not isinstance(offset, int) or offset < 0 or not isinstance(limit, int) or not 1 <= limit <= 32000:
            raise ToolkitError('Invalid offset/limit')
        content = self._safe_file(name).read_text(encoding='utf-8')
        return {'name': name, 'content': content[offset:offset+limit], 'offset': offset,
                'total_chars':len(content),'truncated':offset+limit < len(content),
                'provenance':'LOCAL_SOURCE_GUIDANCE_ONLY'}

    def model_review_checkpoint(self, task: str, observed_findings: list[str],
                                stage: str, proactive_model_advice: bool) -> dict[str, Any]:
        """Read-only risk checkpoint after actual client inspection, with opt-in."""
        if type(proactive_model_advice) is not bool or not proactive_model_advice:
            raise ToolkitError('MODEL_ADVISOR_OPT_IN_REQUIRED')
        if not isinstance(task, str) or not 1 <= len(task) <= 6000:
            raise ToolkitError('task must be text of length 1..6000')
        if stage not in ('NEW_RISK', 'PRE_CHANGE', 'PRE_PR'):
            raise ToolkitError('stage must be NEW_RISK, PRE_CHANGE or PRE_PR')
        if not isinstance(observed_findings, list):
            raise ToolkitError('observed_findings must be explicitly provided as a list')
        hint = _model_review_hint(task, observed_findings)
        return {
            **hint, 'stage': stage, 'source_revision': self.source_revision,
            'toolkit_version': self.manifest.get('version', 'NOT_VERIFIED'),
            'candidate_chat_notice': (
                'SECOND_OPINION_MAY_HELP_VERIFY_CLIENT_CAPABILITIES_FIRST'
                if hint['status'] == 'REVIEW_CANDIDATE' else 'NO_CHAT_PROMPT_NEEDED'),
            'host_inventory': 'REQUIRES_NATIVE_CLIENT_INSPECTION',
            'client_confirmation': 'REQUIRED_BEFORE_ANY_EXTRA_CALL',
        }

    def prepare_task(self, task: str, existing_skills: list[str] | None = None,
                     existing_roles: list[str] | None = None, profile: str = '',
                     max_skills: int = 3,
                     proactive_model_advice: bool = False) -> dict[str, Any]:
        """Load narrow task guidance by comparing inventories supplied by Codex.

        This does NOT scan or write the corporate workspace. An omitted inventory is
        unknown, not evidence that the project is missing all its skills.
        """
        def inventory(value: list[str] | None, label: str) -> tuple[set[str], str]:
            if value is None:
                return set(), 'NOT_PROVIDED'
            if (not isinstance(value, list) or len(value) > 256 or
                any(not isinstance(v, str) or len(v) > 128 for v in value)):
                raise ToolkitError(f'{label} must be an array of up to 256 names')
            return set(value), 'PROVIDED_BY_CLIENT_NOT_VERIFIED'

        installed_skills, skill_inventory_status = inventory(existing_skills, 'existing_skills')
        installed_roles, role_inventory_status = inventory(existing_roles, 'existing_roles')
        if not isinstance(max_skills, int) or isinstance(max_skills, bool) or not 1 <= max_skills <= 8:
            raise ToolkitError('max_skills must be an integer between 1 and 8')
        if type(proactive_model_advice) is not bool:
            raise ToolkitError('proactive_model_advice must be a boolean opt-in')
        routing = self.route(task, profile)
        selected = routing['skills']
        missing = [n for n in selected if n not in installed_skills]
        present = [n for n in selected if n in installed_skills]
        high_priority = [n for n in routing['priority_skills'] if n in missing]
        ordered = list(dict.fromkeys(high_priority + missing))
        loaded_skills = []
        errors = []
        for name in ordered[:max_skills]:
            try:
                loaded_skills.append(self.read('skill', name, limit=32000))
            except (ToolkitError, OSError, UnicodeError) as exc:
                # Failure of one optional skill must not misrepresent its activation.
                errors.append({'name': name, 'error_type': type(exc).__name__})

        lower = task.casefold()
        profiles = routing['profiles']
        if len(profiles) > 1 or routing['profile'] == 'ui-orchestra':
            role = 'orchestrator'
        elif ('review' in lower or 'ревью' in lower or 'проверка кода' in lower):
            role = 'reviewer'
        elif routing['profile'].startswith('qa-'):
            role = 'qa-verifier'
        elif routing['profile'] == 'research':
            role = 'researcher'
        else:
            role = 'implementer'
        role_candidates = [role, 'orchestrator']
        role_name = next((r for r in role_candidates if r in self.roles), None)
        loaded_roles = []
        if role_name and role_name not in installed_roles:
            try:
                loaded_roles.append(self.read('role', role_name, limit=32000))
            except (ToolkitError, OSError, UnicodeError) as exc:
                errors.append({'name': role_name, 'error_type': type(exc).__name__})

        # Count actually returned instruction bytes; this is not runtime token use.
        skill_bytes = sum(len(item['content'].encode('utf-8')) for item in loaded_skills)
        role_bytes = sum(len(item['content'].encode('utf-8')) for item in loaded_roles)
        context_load_metrics = {
            'measurement': 'RETURNED_SOURCE_TEXT_UTF8_BYTES_NOT_MODEL_TOKENS',
            'skill_source_bytes': skill_bytes,
            'role_source_bytes': role_bytes,
            'total_source_bytes': skill_bytes + role_bytes,
            'deferred_skill_count': len(ordered[max_skills:]),
            'reference_files_preloaded': 0,
            'model_tokens': 'NOT_MEASURED',
            'client_usefulness': 'NOT_TESTED',
        }
        return {
            # Enabled ONLY by a caller using an explicit opt-in. No new model
            # tool invocation, provider discovery, persistent logging, or UI.
            **({'model_advisor': _model_review_hint(task)}
               if proactive_model_advice else {}),
            'primary_profile': routing['profile'],
            'secondary_profiles': routing['secondary_profiles'],
            'visual_phase': routing['visual_phase'],
            'deferred_profiles': routing['deferred_profiles'],
            'existing_skills_status': skill_inventory_status,
            'existing_roles_status': role_inventory_status,
            'selected_skills': selected,
            'already_available_skills': present,
            'missing_skills': missing if skill_inventory_status != 'NOT_PROVIDED' else [],
            'required_setup': {
                'status': ('DISCOVERY_REQUIRED' if skill_inventory_status == 'NOT_PROVIDED'
                           else 'INSTALL_MISSING' if missing else 'VERIFY_TOOLS'),
                'skills': ordered[:max_skills] if skill_inventory_status != 'NOT_PROVIDED' else [],
                'executor': 'HOST_CLIENT',
                'scope': 'USER',
                'manager_action': 'ensure',
                'policy': self.manifest.get('required_setup_policy', {}),
            },
            'skills_to_consult': ordered,
            'loaded_skills': loaded_skills,
            'context_load_metrics': context_load_metrics,
            'diagnostics': self.diagnostic(loaded_skills=[row['name'] for row in loaded_skills]),
            'remaining_skills_to_consult': ordered[max_skills:],
            'role_to_consult': role_name,
            'loaded_roles': loaded_roles,
            'already_available_roles': ([role_name] if role_name in installed_roles else []),
            'load_errors': errors,
            'source_revision': self.source_revision,
            'usage_status': 'GUIDANCE_LOADED_NOT_NATIVE_SKILL_ACTIVATION',
            'project_files_changed': False,
            'installation_performed': False,
            'instructions': [
                'Client must inspect applicable workspace, ancestor and user-level skill/role inventories before calling this tool; missing inventories remain unknown.',
                'Read target AGENTS.md and follow project-specific rules and approvals. Existing project skills and roles take precedence.',
                'Use returned instructions as task guidance in the current conversation, not as automatically installed native Codex skills or spawned subagents.',
                'Additional skills remain available in remaining_skills_to_consult: read them via toolkit_get_skill when the task actually requires them.',
                'Inspect original references with toolkit_get_reference only when task requires them.',
                'Never write Toolkit skills, roles, reports or caches into a corporate project by default; prefer the client user scope for required setup.',
                'Install missing task-required skills and tools through the host after verifying actual absence, source, license, pinned revision and files; prefer user scope and preserve existing skills.',
                'For bundled skills use Skill Manager ensure preview, then --apply within existing authorization; do not ask again for already authorized setup. Install deferred skills only when needed.',
                'For required external originals use the reviewed native installer or verified skill files with licenses and provenance; never substitute reference-only methods for a required original.',
                'Honor explicit no-install/reference-only requests and host/project restrictions. If required setup is unavailable, report a concrete BLOCKED reason; MCP itself does not install anything.',
                'Verify installed files, client discovery and actual invocation separately. Keep project reports and caches outside Toolkit; project-scoped installation follows project approval rules.',
                'Do not claim success of tool execution or tests that were not performed.',
                'Default FULFILL_REQUEST: perform the task in the available client; use EXPORT_PROMPT only if the user explicitly asks to write or improve a prompt.',
            ],
        }

    def assess_skill_coverage(self, query: str) -> dict[str, Any]:
        """Conservative local evidence, never proof of semantic coverage.

        Report FOUND_LOCAL only for a readable exact skill slug. Routing keyword
        overlaps are ambiguous hints; no overlap is lexical absence, not a
        statement that no suitable skill exists. No remote lookup or import.
        """
        if not isinstance(query, str) or not query.strip() or len(query) > 500:
            raise ToolkitError('query must be nonempty text up to 500 characters')
        needle = query.strip().casefold()
        found = next((name for name in self.skills if name.casefold() == needle), None)
        if found is not None:
            try:
                self.read('skill', found, limit=1)
            except (ToolkitError, OSError, UnicodeError):
                found = None
        text = re.sub(r'\s+', ' ', needle.replace('ё', 'е'))
        candidates = []
        for profile, terms in ROUTES:
            if profile not in self.profiles or not any(match_term(text, term) for term in terms):
                continue
            skill_names = [name for name in self.profiles[profile] if name in self.skills]
            for name in skill_names:
                if name not in candidates:
                    candidates.append(name)
                if len(candidates) >= 5:
                    break
            if len(candidates) >= 5:
                break
        if found is not None:
            coverage, evidence = 'FOUND_LOCAL', 'exact_readable_local_skill_name'
            candidates = [found] + [name for name in candidates if name != found]
        elif candidates:
            coverage, evidence = 'AMBIGUOUS', 'profile_keyword_overlap_not_coverage_proof'
        else:
            coverage, evidence = 'MISSING', 'no_profile_keyword_overlap_not_semantic_absence'
        return {
            'coverage': coverage, 'evidence': evidence,
            'candidates': candidates[:5],
            'external_skill_search': 'NOT_RUN',
            'external_skill_install': 'NOT_AUTHORIZED',
            'client_activation': 'NOT_OBSERVED',
            'status': 'SOURCE_ONLY_ADVISORY',
            'requires_review': True,
            'source_revision': self.source_revision,
        }

    def discover_external_skill_candidates(
            self, query: str, consent: object = False,
            allowed_repos: object = None) -> dict[str, Any]:
        """Combine local evidence and opt-in public path-only search; no installs.

        Source pins are supplied by the caller, not inferred from skill text.
        The external candidates are not trusted, downloaded or activated.
        """
        local = self.assess_skill_coverage(query)
        try:
            external = discover_pinned_skills(query, consent, allowed_repos)
        except DiscoveryDenied as exc:
            raise ToolkitError(str(exc)) from None
        return {
            'local_skill_coverage': local,
            'external_discovery': external,
            'next_step': 'MANUAL_SOURCE_AND_LICENSE_VERIFICATION'
                         if external['status'] == 'REVIEW_ONLY' else 'NONE',
            'security_gate': 'NOT_RUN',
            'external_skill_install': 'NOT_AUTHORIZED',
            'client_activation': 'NOT_OBSERVED',
            'source_revision': self.source_revision,
        }

    def route(self, task: str, profile: str = '') -> dict[str, Any]:
        if not isinstance(task, str) or not task.strip() or len(task) > 12000:
            raise ToolkitError('task must be nonempty text up to 12000 characters')
        if not isinstance(profile, str):
            raise ToolkitError('profile must be a string')
        actionable_task, excluded_clauses = _split_explicit_prohibitions(task)
        text = re.sub(r'\s+', ' ', actionable_task.casefold().replace('ё', 'е'))
        no_positive_intent = bool(excluded_clauses) and not actionable_task
        matches = {
            candidate: [term for term in terms if match_term(text, term)]
            for candidate, terms in ROUTES if candidate in self.profiles
        }
        matches = {candidate: hits for candidate, hits in matches.items() if hits}
        explicit_prompt = _explicit_prompt_request(text)
        if explicit_prompt and 'prompt-refinement' in self.profiles:
            matches.setdefault('prompt-refinement', ['explicit-prompt-artifact'])
        secondary: list[str] = []
        deferred: list[str] = []
        visual_phase = 'none'
        if profile:
            if profile not in self.profiles:
                raise ToolkitError('Unknown profile; see toolkit_catalog(kind=profiles)')
            chosen = profile
            matched = ['explicit-profile']
            # An explicit profile is not approval to skip visual acceptance.
            # Keep the same create-design gate as automatic routing for a
            # requested new site/screen or major redesign.
            if chosen == 'ui-orchestra' and any(
                match_term(text, term) for term in VISUAL_CREATION_TERMS
            ):
                visual_phase = 'create-design'
        else:
            chosen = next(iter(matches), 'general')
            building = has_build_intent(text)
            engineering = [name for name in ('fullstack', 'backend', 'frontend') if name in matches]
            qa = [name for name in matches if name in QA_PROFILES]
            # More specific QA takes precedence over generic testing guidance.
            specific_qa = next((name for name in qa if name != 'qa-core'), qa[0] if qa else '')
            if explicit_prompt and 'prompt-refinement' in self.profiles:
                chosen = 'prompt-refinement'
            elif any(match_term(text, term) for term in VISUAL_CREATION_TERMS) and 'ui-orchestra' in self.profiles:
                # A new or redesigned visual interface requires the owner's design gate.
                chosen = 'ui-orchestra'
                visual_phase = 'create-design'
                deferred = engineering + ([specific_qa] if specific_qa else [])
                deferred = list(dict.fromkeys(x for x in deferred if x != 'ui-orchestra'))
            elif building and engineering:
                if ('fullstack' in self.profiles and
                    ('fullstack' in matches or ('backend' in matches and 'frontend' in matches))):
                    chosen = 'fullstack'
                else:
                    chosen = engineering[0]
                if specific_qa and specific_qa != chosen:
                    secondary.append(specific_qa)
            elif building and chosen in QA_PROFILES and 'codex-feature' in matches and not engineering:
                # E.g. "Реализуй функцию и покрой её тестами" - implementation + QA.
                chosen = 'codex-feature'
                if specific_qa:
                    secondary.append(specific_qa)
            elif chosen in QA_PROFILES and specific_qa:
                chosen = specific_qa
            elif chosen == 'ui-orchestra' and 'qa-ui' in matches:
                secondary.append('qa-ui')
            matched = matches.get(chosen, ['visual-design-gate'] if visual_phase != 'none' else [])
            if chosen == 'fullstack' and 'fullstack' not in matches:
                matched = matches.get('backend', []) + matches.get('frontend', [])
            if chosen not in self.profiles:
                chosen = 'general' if 'general' in self.profiles else next(iter(self.profiles), '')
                matched = []
        profiles = [chosen] + [name for name in secondary if name in self.profiles and name != chosen]
        selected: list[str] = []
        unavailable: list[str] = []
        dropped_controllers: list[str] = []
        active_controller = ''
        for item in profiles:
            for name in self.profiles.get(item, []):
                if name not in self.skills:
                    if name not in unavailable:
                        unavailable.append(name)
                elif no_positive_intent or any(name.replace('-', ' ') in ' '.join(re.findall(r'[a-zа-яё0-9]+', clause.casefold().replace('ё', 'е'))) for clause in excluded_clauses):
                    continue
                elif name in CONFLICT_GROUP and active_controller and name != active_controller:
                    if name not in dropped_controllers:
                        dropped_controllers.append(name)
                elif name not in selected:
                    selected.append(name)
                    if name in CONFLICT_GROUP:
                        active_controller = name
        priority = []
        for item in profiles:
            for name in PRIORITY_SKILLS.get(item, ()):
                if name in selected and name not in priority:
                    priority.append(name)
        if not priority:
            priority = selected[:4]
        intent_mode = 'EXPORT_PROMPT' if explicit_prompt else 'FULFILL_REQUEST'
        route_status = ('NO_POSITIVE_INTENT' if no_positive_intent else
                        'SUGGESTIONS_ONLY' if matched else 'INSUFFICIENT_EVIDENCE')
        routing_decision = {
            'schema_version': 1,
            'intent_mode': intent_mode,
            'status': route_status,
            'primary_profile': chosen if matched and not no_positive_intent else None,
            'primary_skills': priority[:1] if matched and not no_positive_intent else [],
            'auxiliary_profiles': profiles[1:],
            'auxiliary_skills': priority[1:8] if matched and not no_positive_intent else [],
            'excluded_clauses': excluded_clauses,
            'evidence_basis': 'EXPLICIT_PROFILE' if profile else 'HEURISTIC_KEYWORD_MATCH',
            'uncertainty': 'NOT_CALIBRATED',
            'client_activation': 'NOT_OBSERVED',
            'execution': 'NOT_RUN',
            'installation_performed': False,
            'project_files_changed': False,
        }
        return {
            'profile': chosen, 'secondary_profiles': profiles[1:], 'profiles': profiles,
            'routing_decision': routing_decision,
            'deferred_profiles': deferred, 'visual_phase': visual_phase,
            'matched': matched, 'matches_by_profile': {k: v for k, v in matches.items() if k in profiles},
            'skills': selected, 'priority_skills': priority[:8],
            'unavailable': unavailable, 'excluded_conflicting_controllers': dropped_controllers,
            'roles': ['orchestrator'] if 'orchestrator' in self.roles else [],
            'instructions': [
                'Determine target project from the client workspace. Toolkit is guidance, not the target.',
                'Inspect target AGENTS.md/CLAUDE.md and existing task approval/release rules before modifying anything.',
                'Read the priority_skills first using toolkit_get_skill; load additional selected skills only if needed.',
                'If visual_phase is create-design, propose and obtain visual acceptance before implementing deferred engineering profiles.',
                'The chosen profiles are heuristic. Refine selection using actual task requirements and project context.',
                'Avoid parallel feature-delivery/make-feature controllers.',
                'Work and store outputs only in the authorized target project or chat, never this Toolkit source.',
                'Do not claim tool or skill activation, file changes, tests, CI or deploy unless actually verified.',
                'This MCP adapter is read-only; modifications require separate client tools and permission.',
            ],
            'classification': 'HEURISTIC_MULTI_ROUTE_NOT_MODEL_INFERENCE',
            'source': 'LOCAL_TOOLKIT_MANIFEST',
            'source_revision': self.source_revision,
            'skill_coverage': (self.assess_skill_coverage(task) if len(task) <= 500
                               else {'coverage': 'NOT_EVALUATED',
                                     'evidence': 'query_exceeds_coverage_limit',
                                     'external_skill_install': 'NOT_AUTHORIZED',
                                     'client_activation': 'NOT_OBSERVED',
                                     'requires_review': True}),
        }

def _host_orchestration_tool(tk: Toolkit, name: str, args: dict[str, Any]) -> dict[str, Any]:
    """Invoke vetted local read-only contract, never a Codex session tool.

    The installed Personal MCP keeps its own launcher and imports the exact
    declared module from the dedicated Toolkit source checkout. Verify the
    tracked source digest on every call: a stale/missing source fails closed.
    This does NOT attest host inventory, cost, native execution, or leases.
    """
    relative = 'scripts/codex_host_orchestration.py'
    source = tk._safe_file(relative)
    sums = tk._safe_file('SHA256SUMS.txt')
    match = next((line[:64] for line in sums.read_text(encoding='utf-8').splitlines()
                  if line[64:] == '  ' + relative and len(line) == 66 + len(relative)), None)
    if match is None or hashlib.sha256(source.read_bytes().replace(b'\r\n', b'\n')).hexdigest() != match:
        raise ToolkitError('CODEX_CONTRACT_SOURCE_INTEGRITY_NOT_VERIFIED')
    spec = importlib.util.spec_from_file_location('_adt_personal_codex_contract', source)
    if spec is None or spec.loader is None:
        raise ToolkitError('CODEX_CONTRACT_NOT_AVAILABLE')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if name == 'toolkit_codex_prepare_delegation':
        exact = {'request', 'consent', 'target_model', 'state',
                 'client_snapshot', 'context', 'confirmed_for_this_call'}
        if set(args) != exact:
            raise ToolkitError('INVALID_PREPARE_ARGUMENTS')
        return module.prepare(args['request'], args['consent'], args['target_model'],
                              args['state'], args['client_snapshot'], args['context'],
                              confirmed_for_this_call=args['confirmed_for_this_call'])
    if name == 'toolkit_codex_review_delegation':
        required = {'plan', 'spawn_response', 'wait_response'}
        if not required <= set(args) or set(args) - required - {'host_claimed_one_shot_lease'}:
            raise ToolkitError('INVALID_REVIEW_ARGUMENTS')
        return module.review(args['plan'], args['spawn_response'], args['wait_response'],
                             host_claimed_one_shot_lease=args.get('host_claimed_one_shot_lease', False))
    raise ToolkitError('UNKNOWN_CODEX_CONTRACT_TOOL')


TOOLS: list[dict[str, Any]] = [
    {'name':'toolkit_codex_prepare_delegation',
     'description':'Read-only policy preview for optional native Codex delegation. NEVER spawns agents, spends quotas, authenticates cost, or reserves leases.',
     'inputSchema':{'type':'object','properties':{
         'request':{'type':'object'},'consent':{'type':'object'},
         'target_model':{'type':'string'},'state':{'type':'object'},
         'client_snapshot':{'type':'object'},'context':{'type':'string'},
         'confirmed_for_this_call':{'type':'boolean'}},
         'required':['request','consent','target_model','state','client_snapshot',
                     'context','confirmed_for_this_call'],'additionalProperties':False}},
    {'name':'toolkit_codex_review_delegation',
     'description':'Read-only review of host-supplied native spawn/wait outputs; NO execution or observed backend model attestation.',
     'inputSchema':{'type':'object','properties':{
         'plan':{'type':'object'},'spawn_response':{'type':'object'},
         'wait_response':{'type':'object'},
         'host_claimed_one_shot_lease':{'type':'boolean'}},
         'required':['plan','spawn_response','wait_response'],'additionalProperties':False}},

    {'name':'toolkit_info','description':'Inspect installed AI Development Toolkit version and capabilities (read-only).',
     'inputSchema':{'type':'object','properties':{},'additionalProperties':False}},
    {'name':'toolkit_catalog','description':'List available real Toolkit skills, roles or profiles (read-only).',
     'inputSchema':{'type':'object','properties':{'kind':{'type':'string','enum':['skills','roles','profiles']},'query':{'type':'string'}},'required':['kind'],'additionalProperties':False}},
    {'name':'toolkit_route_task','description':'Select primary and secondary Toolkit profiles for natural-language software engineering and QA tasks. Returns priority skills to read first; selection is heuristic, not model inference.',
     'inputSchema':{'type':'object','properties':{'task':{'type':'string'},'profile':{'type':'string','description':'Optional explicit manifest profile'}},'required':['task'],'additionalProperties':False}},
    {'name':'toolkit_assess_skill_coverage',
     'description':'Read-only local lexical skill coverage advisory: exact local / ambiguous / missing. Never searches external sources or installs skills.',
     'inputSchema':{'type':'object','properties':{'query':{'type':'string','minLength':1,'maxLength':500}},
                    'required':['query'],'additionalProperties':False}},
    {'name':'toolkit_discover_external_skill_candidates',
     'description':'Explicit opt-in, pinned, public GitHub Skill path metadata search. No source contents, external execution, installation or trust approval. Requires exact source commit SHAs; defaults to NO_NETWORK.',
     'inputSchema':{'type':'object','properties':{
         'query':{'type':'string','minLength':1,'maxLength':500},
         'consent':{'type':'boolean','description':'Must explicitly be true to allow public GitHub metadata network lookup'},
         'allowed_repos':{'type':'array','maxItems':3,'items':{'type':'string'},
                          'description':'Explicit allowlist of https://github.com/owner/repo@<full 40-char SHA>'}},
         'required':['query'],'additionalProperties':False}},
    {'name':'toolkit_model_review_checkpoint',
     'description':'After discovering real risk in client-inspected code or diff, reassess optional second-opinion value without loading skills. Explicit opt-in required; no model discovery or execution.',
     'inputSchema':{'type':'object','properties':{
         'task':{'type':'string','minLength':1,'maxLength':6000},
         'observed_findings':{'type':'array','maxItems':8,'items':{'type':'string','minLength':1,'maxLength':320}},
         'stage':{'type':'string','enum':['NEW_RISK','PRE_CHANGE','PRE_PR']},
         'proactive_model_advice':{'type':'boolean',
                                  'description':'Must be true from an opted-in user/client.'}},
         'required':['task','observed_findings','stage','proactive_model_advice'],
         'additionalProperties':False}},
    {'name':'toolkit_prepare_task','description':'For a Codex task, compare client-reported existing skill/role names with relevant Toolkit guidance and return only needed skill and role contents. No project scans, copies, installation or agent spawning (read-only).',
     'inputSchema':{'type':'object','properties':{
         'task':{'type':'string'},'existing_skills':{'type':'array','items':{'type':'string'},'maxItems':256},
         'existing_roles':{'type':'array','items':{'type':'string'},'maxItems':256},
         'profile':{'type':'string'},'max_skills':{'type':'integer','minimum':1,'maximum':8,
             'description':'Default 3 priority skills, up to 8 on explicit request; remaining skills remain selectable'},
         'proactive_model_advice':{'type':'boolean',
             'description':'Explicit user opt-in: return bounded task-risk advisory metadata only; no models or calls.'}},
         'required':['task'],'additionalProperties':False}},
    {'name':'toolkit_get_reference','description':'Read referenced Markdown/text/JSON/YAML files within one declared Toolkit skill (read-only).',
     'inputSchema':{'type':'object','properties':{'skill':{'type':'string'},'path':{'type':'string'},
                 'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':32000}},
                 'required':['skill','path'],'additionalProperties':False}},
    {'name':'toolkit_get_guide','description':'Read real Toolkit agent entrypoint/instructions AGENTS.md or AGENT_START.* from local source.',
     'inputSchema':{'type':'object','properties':{'name':{'type':'string','enum':['AGENT_START.ru.md','AGENT_START.md','AGENTS.md']},
              'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':32000}},'additionalProperties':False}},
    {'name':'toolkit_get_skill','description':'Read the real skill instructions from your local Toolkit checkout (not mere names).',
     'inputSchema':{'type':'object','properties':{'name':{'type':'string'},'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':32000}},'required':['name'],'additionalProperties':False}},
    {'name':'toolkit_get_role','description':'Read a real agent role file from your local Toolkit checkout.',
     'inputSchema':{'type':'object','properties':{'name':{'type':'string'},'offset':{'type':'integer','minimum':0},'limit':{'type':'integer','minimum':1,'maximum':32000}},'required':['name'],'additionalProperties':False}},
]
for t in TOOLS:
    t['annotations'] = {'readOnlyHint': True, 'destructiveHint': False, 'openWorldHint': t['name'] == 'toolkit_discover_external_skill_candidates', 'idempotentHint': True}

def dispatch(tk: Toolkit, name: str, args: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(args, dict):
        raise ToolkitError('Arguments must be an object')
    if name in ('toolkit_codex_prepare_delegation', 'toolkit_codex_review_delegation'):
        try:
            return _host_orchestration_tool(tk, name, args)
        except (ValueError, TypeError, KeyError) as exc:
            raise ToolkitError(str(exc)[:160]) from exc
    if name == 'toolkit_info':
        return tk.info()
    if name == 'toolkit_catalog':
        return tk.catalog(args.get('kind', ''), args.get('query', ''))
    if name == 'toolkit_route_task':
        return tk.route(args.get('task', ''), args.get('profile', ''))
    if name == 'toolkit_assess_skill_coverage':
        return tk.assess_skill_coverage(args.get('query', ''))
    if name == 'toolkit_discover_external_skill_candidates':
        return tk.discover_external_skill_candidates(
            args.get('query', ''), args.get('consent', False), args.get('allowed_repos'))
    if name == 'toolkit_model_review_checkpoint':
        return tk.model_review_checkpoint(args.get('task'), args.get('observed_findings'),
                                          args.get('stage'),
                                          args.get('proactive_model_advice', False))
    if name == 'toolkit_prepare_task':
        return tk.prepare_task(args.get('task',''), args.get('existing_skills'),
                               args.get('existing_roles'), args.get('profile',''), args.get('max_skills',3),
                               args.get('proactive_model_advice', False))
    if name == 'toolkit_get_reference':
        return tk.reference(args.get('skill',''),args.get('path',''),args.get('offset',0),args.get('limit',16000))
    if name == 'toolkit_get_guide':
        return tk.guide(args.get('name','AGENT_START.ru.md'),args.get('offset',0),args.get('limit',16000))
    if name in ('toolkit_get_skill','toolkit_get_role'):
        return tk.read('skill' if name == 'toolkit_get_skill' else 'role',
                       args.get('name', ''), args.get('offset', 0), args.get('limit', 16000))
    raise KeyError(name)

def process(tk: Toolkit, request: dict[str, Any]) -> dict[str, Any] | None:
    if not isinstance(request, dict) or request.get('jsonrpc') != '2.0':
        return {'jsonrpc':'2.0','id':request.get('id') if isinstance(request, dict) else None,
                'error':{'code':-32600,'message':'Invalid JSON-RPC request'}}
    if 'id' not in request:
        return None # Notifications require no reply.
    rid = request['id']
    method = request.get('method')
    try:
        if method == 'initialize':
            # Return the client's compatible version where appropriate.
            ver = request.get('params', {}).get('protocolVersion', PROTOCOL)
            if ver not in ('2024-11-05', '2025-03-26','2025-06-18','2025-11-25','2026-07-28'):
                ver = PROTOCOL
            result = {'protocolVersion':ver, 'capabilities':{'tools':{'listChanged':False}},
                      'serverInfo':{'name':NAME,'version':VERSION}}
        elif method == 'ping':
            result = {}
        elif method == 'tools/list':
            result = {'tools':TOOLS}
        elif method == 'tools/call':
            p = request.get('params', {})
            try:
                content = dispatch(tk, p.get('name',''), p.get('arguments', {}))
                result = {'content':[{'type':'text','text':json.dumps(content, ensure_ascii=False)}],
                          'structuredContent':content}
            except ToolkitError as exc:
                result = {'content':[{'type':'text','text':str(exc)}], 'isError':True}
            except KeyError as exc:
                raise ValueError('Unknown tool: '+str(exc)) from exc
        else:
            return {'jsonrpc':'2.0','id':rid,'error':{'code':-32601,'message':'Method not found'}}
        return {'jsonrpc':'2.0','id':rid,'result':result}
    except UnicodeError:
        raise  # Corrupt Toolkit content is a server-side error, not invalid tool input.
    except (TypeError, AttributeError, ValueError) as exc:
        return {'jsonrpc':'2.0','id':rid,'error':{'code':-32602,'message':str(exc)}}

def serve(tk: Toolkit) -> None:
    """MCP JSON-RPC over UTF-8 stdio, with matching request IDs on errors.

    The client waits for the ID it sent. Returning a parse-error response with
    id=null after a valid tools/call can leave it waiting until its timeout.
    """
    for line in sys.stdin.buffer:
        try:
            request = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            response = {'jsonrpc': '2.0', 'id': None,
                        'error': {'code': -32700, 'message': 'Parse error'}}
            print(f'{NAME}: invalid JSON request: {type(exc).__name__}', file=sys.stderr)
        else:
            try:
                response = process(tk, request)
            except Exception as exc:
                # Preserve the original ID, don't dump source contents to stdout.
                response = {'jsonrpc': '2.0',
                            'id': request.get('id') if isinstance(request, dict) else None,
                            'error': {'code': -32603, 'message': 'Internal MCP tool error'}}
                print(f'{NAME}: internal tool error: {type(exc).__name__}', file=sys.stderr)
        if response is not None:
            # MCP stdio requires UTF-8 on every platform. In Windows pipe mode
            # sys.stdout may use the active ANSI code page (e.g. cp1251), so
            # writing Unicode through TextIOWrapper can corrupt JSON-RPC.
            payload = (json.dumps(response, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')
            sys.stdout.buffer.write(payload)
            sys.stdout.buffer.flush()


def main() -> int:
    parser = argparse.ArgumentParser(description='AI Development Toolkit personal MCP (read-only)')
    parser.add_argument('--source', type=Path, required=True, help='Absolute path to a local Toolkit checkout')
    parser.add_argument('--check', action='store_true', help='Validate source and print capability JSON')
    args = parser.parse_args()
    try:
        toolkit = Toolkit(args.source)
    except (ToolkitError, OSError) as exc:
        print(f'{NAME}: {exc}', file=sys.stderr)
        return 2
    if args.check:
        print(json.dumps(toolkit.info(), ensure_ascii=False, indent=2))
        return 0
    serve(toolkit)
    return 0

if __name__ == '__main__':
    sys.exit(main())
