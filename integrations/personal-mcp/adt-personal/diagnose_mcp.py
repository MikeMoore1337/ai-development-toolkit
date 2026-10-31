#!/usr/bin/env python3
"""Safe local stdio smoke test for installed ADT MCP; does not invoke Codex.

Windows:
    py -3 diagnose_mcp.py
No network access, package installation, writing to Toolkit or project files.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PILOT = 'Исправь дефект в обработке параметров REST API на Python и проверь тестами'
COMPOSITE = 'Создать REST API на FastAPI и покрыть его тестами pytest'


def rpc(request_id: int, method: str, params: dict | None = None) -> dict:
    item = {'jsonrpc': '2.0', 'id': request_id, 'method': method}
    if params is not None:
        item['params'] = params
    return item


def main() -> int:
    parser = argparse.ArgumentParser(description='Diagnostic check of installed ADT local stdio MCP')
    default_root = (Path(os.environ.get('LOCALAPPDATA', str(Path.home() / 'AppData' / 'Local'))) / 'ADT-Personal'
                    if os.name == 'nt' else Path(os.environ.get('XDG_DATA_HOME', str(Path.home() / '.local/share'))) / 'adt-personal')
    parser.add_argument('--launcher', type=Path, default=default_root / 'mcp' / 'adt_mcp.py')
    parser.add_argument('--source', type=Path, default=default_root / 'toolkit-source')
    parser.add_argument('--timeout', type=int, default=20)
    args = parser.parse_args()
    if not args.launcher.is_file() or not (args.source / 'MANIFEST.json').is_file():
        print(json.dumps({'status': 'BLOCKED', 'reason': 'Installed MCP or Toolkit manifest not found'}, ensure_ascii=False))
        return 2
    if args.timeout < 2 or args.timeout > 60:
        parser.error('--timeout must be between 2 and 60 seconds')

    queries = [
        rpc(1, 'initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                              'clientInfo': {'name': 'adt-local-diagnostic', 'version': '0.1.0'}}),
        rpc(2, 'tools/list'),
        rpc(3, 'tools/call', {'name': 'toolkit_info', 'arguments': {}}),
        rpc(4, 'tools/call', {'name': 'toolkit_route_task', 'arguments': {'task': PILOT}}),
        rpc(5, 'tools/call', {'name': 'toolkit_route_task', 'arguments': {'task': COMPOSITE}}),
        rpc(46, 'tools/call', {'name': 'toolkit_prepare_task', 'arguments': {'task': COMPOSITE, 'existing_skills': ['api-design'], 'existing_roles': []}}),
        rpc(47, 'tools/call', {'name': 'toolkit_assess_skill_coverage', 'arguments': {'query': 'qa-strategy'}}),
        rpc(48, 'tools/call', {'name': 'toolkit_assess_skill_coverage', 'arguments': {'query': 'zqxw-no-matching-skill'}}),
        rpc(49, 'tools/call', {'name': 'toolkit_discover_external_skill_candidates', 'arguments': {'query': 'qa-strategy'}}),
        rpc(50, 'tools/call', {'name': 'toolkit_prepare_stage', 'arguments': {
            'task': COMPOSITE, 'stage': 'Test backend API', 'requested_skills': ['qa-strategy']}}),
    ]
    for i in range(6, 46):
        queries.append(rpc(i, 'tools/call', {'name': 'toolkit_route_task',
                                             'arguments': {'task': PILOT if i % 2 else COMPOSITE}}))
    input_data = ''.join(json.dumps(q, ensure_ascii=False) + '\n' for q in queries)
    started = time.perf_counter()
    try:
        completed = subprocess.run([sys.executable, '-B', str(args.launcher), '--source', str(args.source)],
                                   input=input_data.encode('utf-8'), capture_output=True, timeout=args.timeout)
    except subprocess.TimeoutExpired:
        print(json.dumps({'status': 'FAIL', 'reason': 'Local MCP stdio process timed out',
                          'timeout_seconds': args.timeout}, ensure_ascii=False))
        return 1
    except OSError as exc:
        print(json.dumps({'status': 'BLOCKED', 'reason': type(exc).__name__}, ensure_ascii=False))
        return 2

    elapsed_ms = round((time.perf_counter() - started) * 1000)
    # Decode bytes explicitly. With subprocess(text=True), a Windows code-page
    # mismatch can cause an exception in an internal subprocess reader thread,
    # leaving a misleading response-shape error instead of a UTF-8 diagnosis.
    try:
        stdout_text = completed.stdout.decode('utf-8', errors='strict')
    except UnicodeDecodeError as exc:
        print(json.dumps({'status': 'FAIL', 'reason': 'MCP_STDOUT_NOT_UTF8',
                          'invalid_byte_offset': exc.start, 'exit_code': completed.returncode,
                          'elapsed_ms': elapsed_ms}, ensure_ascii=False))
        return 1
    stderr_text = completed.stderr.decode('utf-8', errors='replace')
    try:
        replies = [json.loads(line) for line in stdout_text.splitlines() if line.strip()]
        indexed = {r['id']: r for r in replies if isinstance(r, dict) and isinstance(r.get('id'), int)}
        received = set(indexed)
        wanted = set(q['id'] for q in queries)
        def get_result(request_id: int) -> dict:
            envelope = indexed.get(request_id, {})
            result = envelope.get('result')
            return result if isinstance(result, dict) else {}
        def get_structured(request_id: int) -> dict:
            structured = get_result(request_id).get('structuredContent')
            return structured if isinstance(structured, dict) else {}
        info = get_structured(3)
        pilot = get_structured(4)
        composite = get_structured(5)
        prepared = get_structured(46)
        local_coverage = get_structured(47)
        missing_coverage = get_structured(48)
        external_without_consent = get_structured(49).get('external_discovery', {})
        stage = get_structured(50)
        tools = get_result(2).get('tools', [])
        tools = tools if isinstance(tools, list) else []
        has_errors = any(isinstance(r, dict) and (
            'error' in r or (isinstance(r.get('result'), dict) and r['result'].get('isError')))
            for r in replies)
        ok = (completed.returncode == 0 and received == wanted and len(replies) == len(queries)
              and not has_errors
              and pilot.get('profile') == 'backend' and 'qa-core' in pilot.get('secondary_profiles', [])
              and composite.get('profile') == 'backend'
              and 'qa-python' in composite.get('secondary_profiles', [])
              and len(tools) == 14 and any(t.get('name') == 'toolkit_prepare_stage' for t in tools)
              and [s.get('name') for s in stage.get('loaded_skills', [])] == ['qa-strategy']
              and stage.get('client_activation') == 'NOT_OBSERVED'
              and prepared.get('primary_profile') == 'backend'
              and 'qa-python' in prepared.get('secondary_profiles', [])
              and len(prepared.get('loaded_skills', [])) > 0
              and local_coverage.get('coverage') == 'FOUND_LOCAL'
              and 'qa-strategy' in local_coverage.get('candidates', [])
              and missing_coverage.get('coverage') == 'MISSING'
              and local_coverage.get('external_skill_install') == 'NOT_AUTHORIZED'
              and missing_coverage.get('external_skill_install') == 'NOT_AUTHORIZED'
              and local_coverage.get('client_activation') == 'NOT_OBSERVED'
              and missing_coverage.get('client_activation') == 'NOT_OBSERVED'
              and external_without_consent.get('status') == 'NO_NETWORK'
              and external_without_consent.get('installation') == 'NOT_AUTHORIZED')
        summary = {'status': 'PASS' if ok else 'FAIL', 'transport': 'DIRECT_STDIO_NOT_CODEX',
                   'mcp_server_version': info.get('mcp_server_version', 'NOT_RETURNED'),
                   'request_count': len(queries), 'response_count': len(replies),
                   'missing_ids': sorted(wanted - received),
                   'pilot_profile': pilot.get('profile', 'NOT_RETURNED'),
                   'pilot_secondary_profiles': pilot.get('secondary_profiles', []),
                   'composite_profile': composite.get('profile', 'NOT_RETURNED'),
                   'composite_secondary_profiles': composite.get('secondary_profiles', []),
                   'tool_count': len(tools), 'prepared_skills': len(prepared.get('loaded_skills',[])),
                   'skill_coverage_local': local_coverage.get('coverage', 'NOT_RETURNED'),
                   'skill_coverage_missing': missing_coverage.get('coverage', 'NOT_RETURNED'),
                   'skill_installation': local_coverage.get('external_skill_install', 'NOT_RETURNED'),
                   'external_without_consent': external_without_consent.get('status', 'NOT_RETURNED'),
                   'elapsed_ms': elapsed_ms,
                   'exit_code': completed.returncode}
        if not ok:
            summary['reason'] = 'RPC_RESPONSE_VALIDATION_FAILED'
            summary['error_codes'] = sorted({str(r['error'].get('code')) for r in replies
                                             if isinstance(r, dict) and isinstance(r.get('error'), dict)})
            summary['stderr_error_type_only'] = stderr_text.split(':', 1)[-1].strip().splitlines()[-1][:150] if stderr_text else None
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0 if ok else 1
    except (ValueError, TypeError, KeyError, AttributeError) as exc:
        print(json.dumps({'status':'FAIL','reason':'Unexpected MCP JSON-RPC response shape',
                          'exception_type':type(exc).__name__, 'response_count': len(stdout_text.splitlines()),
                          'elapsed_ms': elapsed_ms}, ensure_ascii=False))
        return 1



if __name__ == '__main__':
    raise SystemExit(main())
