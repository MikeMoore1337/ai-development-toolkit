"""Offline pilot-fixture verification tests; not a real Codex pilot."""
import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'pilot' / 'run_pilot.py'
spec = importlib.util.spec_from_file_location('adt_pilot', SCRIPT)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class PilotFixtureTests(unittest.TestCase):
    def test_baseline_is_red_and_evidence_not_invented(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(pilot.tempfile, 'mkdtemp', side_effect=lambda **kw: str(Path(root) / 'adt-pilot-probe')):
                (Path(root) / 'adt-pilot-probe').mkdir()
                with redirect_stdout(io.StringIO()) as stream:
                    ws, code = pilot.prepare()
                self.assertEqual(code, 0)
                prep = json.loads(stream.getvalue())
                self.assertEqual(prep['baseline'], 'EXPECTED_FAIL')
                self.assertFalse((ws / '__pycache__').exists())
                with redirect_stdout(io.StringIO()) as stream:
                    status = pilot.verify(ws)
                self.assertEqual(status, 1)
                result = json.loads(stream.getvalue())
                self.assertEqual(result['python_tests'], 'FAIL')
                self.assertEqual(result['mcp_usage_evidence'], 'NOT_VERIFIED_FROM_FILES')

    def test_known_correct_fix_passes_without_claiming_agent_usage(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            ws = Path(root) / 'adt-pilot-probe'
            ws.mkdir()
            with patch.object(pilot.tempfile, 'mkdtemp', side_effect=lambda **kw: str(ws)):
                with redirect_stdout(io.StringIO()):
                    pilot.prepare()
            # Fixture validation only: do not describe as Codex execution.
            corrected = '''def parse_pagination(params: dict[str, str]) -> tuple[int, int]:
    def parse(key: str, default: int) -> int:
        raw = params.get(key, str(default))
        if not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal():
            raise ValueError(f"Invalid {key}")
        return int(raw)
    limit = parse("limit", 20)
    offset = parse("offset", 0)
    if not 1 <= limit <= 100 or offset < 0:
        raise ValueError("Out of range")
    return limit, offset
'''
            (ws / 'service.py').write_text(corrected, encoding='utf-8')
            with redirect_stdout(io.StringIO()) as stream:
                result = pilot.verify(ws)
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(stream.getvalue())['mcp_usage_evidence'], 'NOT_VERIFIED_FROM_FILES')


    def test_prepare_uses_exact_bytes_and_hashes(self):
        with tempfile.TemporaryDirectory() as root:
            ws = Path(root) / 'adt-pilot-byte-check'
            ws.mkdir()
            with patch.object(pilot.tempfile, 'mkdtemp', side_effect=lambda **kw: str(ws)):
                with redirect_stdout(io.StringIO()):
                    pilot.prepare()
            meta = json.loads((ws / pilot.SIGNATURE).read_text(encoding='utf-8'))
            self.assertEqual(meta['fixture_version'], 2)
            self.assertEqual(pilot.sha256((ws / 'service.py').read_bytes()), meta['service_original_sha256'])
            self.assertEqual(pilot.sha256((ws / 'test_service.py').read_bytes()), meta['tests_sha256'])

    def test_legacy_windows_crlf_fixture_does_not_false_fail(self):
        # v0.1.4/v0.1.5 prepared Windows files with CRLF but stored the
        # SHA-256 of the LF template, making verification fail even untouched.
        with tempfile.TemporaryDirectory() as root:
            ws = Path(root) / 'adt-pilot-legacy-windows'
            ws.mkdir()
            with patch.object(pilot.tempfile, 'mkdtemp', side_effect=lambda **kw: str(ws)):
                with redirect_stdout(io.StringIO()):
                    pilot.prepare()
            meta_path = ws / pilot.SIGNATURE
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            meta['fixture_version'] = 1
            meta_path.write_text(json.dumps(meta), encoding='utf-8')
            (ws / 'service.py').write_bytes(pilot.TARGET.replace('\n', '\r\n').encode('utf-8'))
            (ws / 'test_service.py').write_bytes(pilot.TESTS.replace('\n', '\r\n').encode('utf-8'))
            with redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(pilot.verify(ws), 1)
            baseline = json.loads(stream.getvalue())
            self.assertFalse(baseline['service_changed'])
            self.assertTrue(baseline['test_contract_unchanged'])
            self.assertEqual(baseline['test_contract_line_endings'], 'CRLF')
            (ws / 'service.py').write_text("""def parse_pagination(params):
    def validate(key, default):
        raw = params.get(key, str(default))
        if not isinstance(raw, str) or not raw.isascii() or not raw.isdecimal():
            raise ValueError('invalid')
        return int(raw)
    limit, offset = validate('limit', 20), validate('offset', 0)
    if not 1 <= limit <= 100 or offset < 0:
        raise ValueError('range')
    return limit, offset
""", encoding='utf-8')
            with redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(pilot.verify(ws), 0)
            fixed = json.loads(stream.getvalue())
            self.assertTrue(fixed['service_changed'])
            self.assertTrue(fixed['test_contract_unchanged'])
            # Actual modifications, even cosmetic edits, are still detected.
            with (ws / 'test_service.py').open('ab') as handle:
                handle.write(b'\n# changed by agent\n')
            with redirect_stdout(io.StringIO()) as stream:
                self.assertEqual(pilot.verify(ws), 1)
            modified = json.loads(stream.getvalue())
            self.assertFalse(modified['test_contract_unchanged'])

    def test_reject_non_pilot_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                pilot.verify(Path(temp))


if __name__ == '__main__':
    unittest.main()
