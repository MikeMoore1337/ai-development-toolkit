#!/usr/bin/env python3
"""Safe, opt-in live-agent fixture outside user repositories (stdlib only).

This script does not run an AI client; any client skill-use proof must be from
an independently observed real session. Usage:
    python pilot/run_pilot.py prepare
    python pilot/run_pilot.py verify --workspace <printed-path>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET = '''"""API pagination contract, intentionally incomplete for agent pilot."""


def parse_pagination(params: dict[str, str]) -> tuple[int, int]:
    """Return (limit, offset). Defaults are limit=20, offset=0.

    Accept decimal strings only. Valid limits: 1..100. Offset: 0 or higher.
    Reject incorrect types, signed or space-padded inputs, and out-of-range
    values with ValueError. Ignore unrelated query parameters.
    """
    limit = int(params.get("limit", 20))
    offset = int(params.get("offset", 0))
    return limit, offset
'''

TESTS = '''import unittest
from service import parse_pagination


class TestPagination(unittest.TestCase):
    def test_default(self):
        self.assertEqual(parse_pagination({}), (20, 0))

    def test_explicit_values(self):
        self.assertEqual(parse_pagination({"limit": "10", "offset": "2"}), (10, 2))

    def test_upper_limit(self):
        self.assertEqual(parse_pagination({"limit": "100"}), (100, 0))

    def test_limit_zero_rejected(self):
        with self.assertRaises(ValueError):
            parse_pagination({"limit": "0"})

    def test_limit_over_hundred_rejected(self):
        with self.assertRaises(ValueError):
            parse_pagination({"limit": "101"})

    def test_negative_offset_rejected(self):
        with self.assertRaises(ValueError):
            parse_pagination({"offset": "-1"})

    def test_invalid_number_rejected(self):
        with self.assertRaises(ValueError):
            parse_pagination({"limit": "abc"})

    def test_space_padded_number_rejected(self):
        with self.assertRaises(ValueError):
            parse_pagination({"limit": " 3 "})

    def test_boolean_rejected(self):
        with self.assertRaises(ValueError):
            parse_pagination({"limit": True})

    def test_unrelated_keys_preserved_as_unused(self):
        self.assertEqual(parse_pagination({"search": "x"}), (20, 0))
'''

PROMPT = '''# Запрос для отдельной сессии Codex

Работай только с открытой временной папкой `adt-pilot-*`.
Используй автоматически подключённый MCP `ai-development-toolkit`.

Задача: исправь реализацию `parse_pagination` в `service.py` по контракту,
изложенному в docstring, и обеспечь успешное выполнение всех тестов `test_service.py`.

Перед изменением:
1. Вызови `toolkit_info` и `toolkit_route_task` для задачи «Исправь дефект
   в обработке параметров REST API на Python и проверь тестами».
2. Вызови `toolkit_get_skill` для `api-design`, `test-analysis-design`
   (или `pytest-test-design`, если выбран маршрутизатором).
3. Сохрани реальное подтверждение вызовов в ответе: имя, краткая выдержка
   применимого требования и в каком изменении оно использовано.

Ограничения: без внешней сети, установки пакетов, платных API и изменения
`test_service.py`, других проектов, глобальных настроек, Toolkit, AGENTS.md.
Используй только стандартную библиотеку Python. Запусти тесты до и после правки.
В конце покажи итог PASS/FAIL, изменённые файлы и фактические команды/результаты.
Не объявляй что методики применены, если реально лишь прочитал документы.
'''

SIGNATURE = '.adt-pilot.json'


def fixture_line_endings(actual: bytes, baseline: str) -> str | None:
    """Match exact fixture bytes, accepting only LF or all-CRLF line endings.

    Historical version-1 fixtures on Windows were written with write_text,
    which converted LF to CRLF *after* the marker hash was calculated. This
    compatibility check does not allow arbitrary edits or whitespace changes.
    """
    if actual == baseline.encode('utf-8'):
        return 'LF'
    if actual == baseline.replace('\n', '\r\n').encode('utf-8'):
        return 'CRLF'
    return None


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run_tests(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', str(path), '-p', 'test_service.py', '-v'],
                          capture_output=True, text=True, cwd=path, timeout=30,
                          env={**__import__('os').environ, 'PYTHONDONTWRITEBYTECODE': '1'})


def prepare() -> tuple[Path, int]:
    workspace = Path(tempfile.mkdtemp(prefix='adt-pilot-')).resolve()
    (workspace / 'service.py').write_bytes(TARGET.encode('utf-8'))
    (workspace / 'test_service.py').write_bytes(TESTS.encode('utf-8'))
    (workspace / 'PILOT_PROMPT.ru.md').write_text(PROMPT, encoding='utf-8')
    (workspace / SIGNATURE).write_text(json.dumps({
        'fixture_version': 2,
        'service_original_sha256': sha256(TARGET.encode('utf-8')),
        'tests_sha256': sha256(TESTS.encode('utf-8'))
    }, indent=2), encoding='utf-8')
    initial = run_tests(workspace)
    if initial.returncode == 0:
        raise RuntimeError('Fixture baseline unexpectedly passes; abort pilot')
    print(json.dumps({'status': 'PREPARED', 'workspace': str(workspace),
                      'baseline': 'EXPECTED_FAIL', 'prompt_file': str(workspace / 'PILOT_PROMPT.ru.md'),
                      'note': 'Open this temporary directory in Codex; this script does not invoke Codex.'},
                     ensure_ascii=False, indent=2))
    return workspace, 0


def verify(workspace: Path) -> int:
    workspace = workspace.resolve(strict=True)
    marker = workspace / SIGNATURE
    if not marker.is_file() or not workspace.name.startswith('adt-pilot-'):
        raise ValueError('Not an ADT disposable pilot workspace')
    data = json.loads(marker.read_text(encoding='utf-8'))
    if data.get('fixture_version') not in (1, 2):
        raise ValueError('Unexpected pilot fixture version')
    if (data.get('service_original_sha256') != sha256(TARGET.encode('utf-8')) or
        data.get('tests_sha256') != sha256(TESTS.encode('utf-8'))):
        raise ValueError('Pilot marker does not match the bundled fixture contract')
    service = workspace / 'service.py'
    tests = workspace / 'test_service.py'
    original_changed = fixture_line_endings(service.read_bytes(), TARGET) is None
    test_line_endings = fixture_line_endings(tests.read_bytes(), TESTS)
    test_unchanged = test_line_endings is not None
    tested = run_tests(workspace)
    status = ('PASS' if original_changed and test_unchanged and tested.returncode == 0 else 'FAIL')
    print(json.dumps({'status':status, 'workspace':str(workspace),
                      'service_changed':original_changed,
                      'test_contract_unchanged':test_unchanged,
                      'test_contract_line_endings': test_line_endings or 'MISMATCH',
                      'fixture_version': data['fixture_version'],
                      'python_tests':'PASS' if tested.returncode == 0 else 'FAIL',
                      'mcp_usage_evidence':'NOT_VERIFIED_FROM_FILES',
                      'real_agent_skill_application':'REQUIRES_CODEX_TRANSCRIPT_REVIEW',
                      'test_output':(tested.stdout+'\n'+tested.stderr)[-6000:]}, ensure_ascii=False, indent=2))
    return 0 if status == 'PASS' else 1


def main() -> int:
    parser = argparse.ArgumentParser(description='Isolated live Codex skill-use pilot; no client auto-execution')
    parser.add_argument('action', choices=['prepare', 'verify'])
    parser.add_argument('--workspace', type=Path)
    args = parser.parse_args()
    if args.action == 'prepare':
        prepare()
        return 0
    if not args.workspace:
        parser.error('--workspace required for verify')
    try:
        return verify(args.workspace)
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f'PILOT_ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
