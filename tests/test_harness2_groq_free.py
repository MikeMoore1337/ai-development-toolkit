"""Offline security/functional contract for optional Groq Free Windows-WSL smoke."""
from __future__ import annotations

import base64
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import struct
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
H2 = ROOT / "integrations" / "harness2"
WIN = H2 / "groq_free_windows.py"
WSL = H2 / "groq_free_wsl.py"
SH = H2 / "groq-free-smoke.sh"
PS = H2 / "acceptance.ps1"
MODEL = "groq:openai/gpt-oss-20b"
TOKEN = "freellmapi-mocked-unit-test-secret"


def load(name: str, file: Path):
    spec = importlib.util.spec_from_file_location(name, file)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeGateway(BaseHTTPRequestHandler):
    calls: list[dict] = []

    def log_message(self, *args):
        pass

    def do_POST(self):
        size = int(self.headers.get("Content-Length", "0"))
        body = json.loads(self.rfile.read(size))
        type(self).calls.append({
            "model": body.get("model"),
            "authorization": self.headers.get("Authorization"),
        })
        if self.path != "/v1/chat/completions" or body.get("model") != MODEL:
            self.send_error(400)
            return
        result = json.dumps({
            "choices": [{"message": {"content": "MOCKED_OK"}, "finish_reason": "stop"}],
            "model": MODEL,
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Routed-Via", "groq/openai/gpt-oss-20b")
        self.send_header("Content-Length", str(len(result)))
        self.end_headers()
        self.wfile.write(result)


class GroqFreeContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.win = load("h421_windows", WIN)
        cls.wsl = load("h421_wsl", WSL)

    def request(self, model=MODEL, tokens=256, tools=None):
        payload = {"model": model,
                   "messages": [{"role": "user", "content": "Say MOCKED_OK"}],
                   "max_tokens": tokens, "stream": False}
        if tools is not None:
            payload["tools"] = tools
        return payload

    def test_exact_model_allowlist_and_local_only_contract(self):
        valid = self.request()
        raw = json.dumps(valid).encode()
        method, path, body = self.win.validate_request({
            "method": "POST", "path": "/v1/chat/completions",
            "body": base64.b64encode(raw).decode(),
        })
        self.assertEqual((method, path, json.loads(body)), ("POST", "/v1/chat/completions", valid))
        for candidate in (self.request(model="auto"),
                          self.request(model="openrouter/qwen/qwen3-coder:free"),
                          self.request(model="groq:openai/gpt-oss-20b-paid"),
                          self.request(tokens=0), self.request(tokens=513),
                          self.request(tokens=True),
                          self.request(tools=[{"function": {"name": "bash"}}]),
                          self.request(tools=[{"function": "read"}]),
                          self.request(tools=[{"function": []}]),
                          self.request(tools=[None]),
                          self.request(tools=[{"function": {"name": "read"}}] * 2)):
            data = json.dumps(candidate).encode()
            frame = {"method": "POST", "path": "/v1/chat/completions",
                     "body": base64.b64encode(data).decode()}
            with self.subTest(frame=frame["body"][:30]), self.assertRaises(ValueError):
                self.win.validate_request(frame)
            with self.assertRaises(ValueError):
                self.wsl.validate_chat(candidate)
        with self.assertRaises(ValueError):
            self.win.validate_request({"method": "POST", "path": "http://example.com/v1/chat/completions", "body": ""})
        with self.assertRaises(ValueError):
            self.win.validate_request({"method": "GET", "path": "/v1/models", "body": "YQ=="})
        self.wsl.validate_chat(self.request(tools=[{"type": "function", "function": {"name": "read"}}]))

    def test_mocked_gateway_keeps_real_credential_out_of_wsl_and_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "FreeLLMAPI"
            root.mkdir()
            db = sqlite3.connect(root / "freeapi.db")
            try:
                db.execute("CREATE TABLE api_keys(platform TEXT,status TEXT,enabled INTEGER)")
                db.execute("INSERT INTO api_keys VALUES ('groq','healthy',1)")
                db.execute("CREATE TABLE settings(key TEXT,value TEXT)")
                db.execute("INSERT INTO settings VALUES('unified_api_key',?)", (TOKEN,))
                db.commit()
            finally:
                db.close()
            FakeGateway.calls = []
            with ThreadingHTTPServer(("127.0.0.1", 0), FakeGateway) as upstream:
                t = threading.Thread(target=upstream.serve_forever, daemon=True)
                t.start()
                (root / "config.json").write_text(
                    json.dumps({"port": upstream.server_port}), encoding="utf-8")
                with mock.patch.dict(os.environ, {"APPDATA": temp}):
                    model_key = "h421-unit-test-ephemeral-bearer-" + ("x" * 30)
                    with self.wsl.Server(sys.executable, str(WIN), model_key) as bridge:
                        b = threading.Thread(target=bridge.serve_forever, daemon=True)
                        b.start()
                        addr = f"http://127.0.0.1:{bridge.server_port}"
                        self.assertEqual(urlopen(addr + "/health", timeout=5).status, 200)
                        with self.assertRaises(HTTPError) as ctx:
                            urlopen(addr + "/v1/models", timeout=5)
                        self.assertEqual(ctx.exception.code, 403)
                        ctx.exception.close()
                        headers = {"Authorization": "Bearer " + model_key,
                                   "Content-Type": "application/json"}
                        def send(payload):
                            req = Request(addr + "/v1/chat/completions",
                                          data=json.dumps(payload).encode(), headers=headers)
                            return urlopen(req, timeout=12)
                        for bad in (self.request(model="auto"),
                                    self.request(tools=[{"function": {"name": "bash"}}]),
                                    self.request(tools=[{"function": "read"}]),
                                    self.request(tokens=2048)):
                            with self.assertRaises(HTTPError) as denied:
                                send(bad)
                            self.assertIn(denied.exception.code, (400, 403))
                            denied.exception.close()
                        with send(self.request(tools=[{"type": "function", "function": {"name": "read"}}])) as res:
                            self.assertEqual(res.status, 200)
                            payload = res.read()
                        self.assertEqual(json.loads(payload)["choices"][0]["message"]["content"], "MOCKED_OK")
                        self.assertNotIn(TOKEN.encode(), payload)
                        # Enforce an absolute cap before the 7th request is
                        # forwarded, regardless of the upstream's rate limits.
                        for _ in range(self.wsl._MAX_POSTS - 1):
                            with send(self.request()) as extra:
                                self.assertEqual(extra.status, 200)
                                self.assertNotIn(TOKEN.encode(), extra.read())
                        with self.assertRaises(HTTPError) as exhausted:
                            send(self.request())
                        self.assertEqual(exhausted.exception.code, 429)
                        exhausted.exception.close()
                        self.assertEqual(len(FakeGateway.calls), self.wsl._MAX_POSTS)
                        self.assertTrue(all(
                            call["authorization"] == "Bearer " + TOKEN and
                            call["model"] == MODEL for call in FakeGateway.calls
                        ))
                        bridge.shutdown()
                        b.join(timeout=4)
                upstream.shutdown()
                t.join(timeout=4)

    def test_shell_and_windows_explicit_owner_gates(self):
        ps = PS.read_text(encoding="utf-8")
        sh = SH.read_text(encoding="utf-8")
        self.assertIn("HARNESS2_GROQ_FREE_SMOKE_REQUIRES_CONFIRMATION", ps)
        self.assertIn("HARNESS2_UNEXPECTED_GROQ_FREE_CONFIRMATION", ps)
        self.assertIn("'GroqFreeCheck'", ps)
        self.assertIn("'GroqFreeSmoke'", ps)
        self.assertIn("--confirm-groq-free", sh)
        self.assertIn("</dev/null", sh)
        self.assertIn("--pure run", sh)
        self.assertIn('"*": "deny", "read": "allow"', sh)
        self.assertIn('"read"', sh)
        self.assertIn('timeout --kill-after=5s 85s', sh)
        self.assertIn("mktemp -d", sh)
        self.assertIn('realpath -e -- "$TEMP_ROOT"', sh)
        self.assertIn('"$canonical_temp" == "$canonical_home/"*', sh)
        self.assertNotIn("harness2-judge", sh)
        for name in (WIN, WSL):
            self.assertTrue(name.is_file())

    @unittest.skipUnless(os.name == "nt", "PowerShell 5.1 only")
    def test_powershell_refuses_unconfirmed_model_execution_without_wsl(self):
        for args, marker in (
            (["-Action", "GroqFreeSmoke"], "HARNESS2_GROQ_FREE_SMOKE_REQUIRES_CONFIRMATION"),
            (["-Action", "GroqFreeCheck", "-ConfirmGroqFree"],
             "HARNESS2_UNEXPECTED_GROQ_FREE_CONFIRMATION"),
        ):
            command = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy",
                       "Bypass", "-File", str(PS), *args]
            result = subprocess.run(command, text=True, capture_output=True,
                                    errors="replace", timeout=18, check=False)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(marker, result.stderr)


if __name__ == "__main__":
    unittest.main()
