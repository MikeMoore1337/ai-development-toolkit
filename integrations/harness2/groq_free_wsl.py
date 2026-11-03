#!/usr/bin/env python3
"""Ephemeral WSL2 loopback-only OpenAI-compatible transport for Groq Free.

A Windows child process talks to the user's existing FreeLLMAPI gateway.
No real credentials enter WSL. This is NOT a general network proxy.
"""
from __future__ import annotations

import base64
import http.server
import json
import os
import secrets
import struct
import subprocess
import sys
import threading

_ALLOWED = {"groq:openai/gpt-oss-20b", "groq:openai/gpt-oss-120b"}
_MAX_POSTS = 6
_MAX_BODY = 256 * 1024
_MAX_TOKENS = 512


def validate_chat(payload: object) -> None:
    if not isinstance(payload, dict) or payload.get("model") not in _ALLOWED:
        raise ValueError("model not in the Free-only allowlist")
    n = payload.get("max_tokens")
    if type(n) is not int or not 1 <= n <= _MAX_TOKENS:
        raise ValueError("output token cap missing or exceeded")
    if not isinstance(payload.get("messages"), list) or not payload["messages"]:
        raise ValueError("no chat messages")
    tools = payload.get("tools") or []
    if not isinstance(tools, list) or len(tools) > 1:
        raise ValueError("only one read tool may be exposed")
    for item in tools:
        if not isinstance(item, dict) or (item.get("function") or {}).get("name") != "read":
            raise ValueError("tool not allowed")


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, python: str, script: str, token: str):
        super().__init__(("127.0.0.1", 0), Handler)
        self.windows_python = python
        self.windows_script = script
        self.bearer_token = token
        self.total_posts = 0
        self.lock = threading.Lock()


class Handler(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"
    server: Server

    def log_message(self, fmt: str, *args: object) -> None:
        # Do not log requests, authorization headers, responses or keys.
        pass

    def send_json(self, status: int, data: dict[str, object]) -> None:
        raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(raw)

    def authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        return secrets.compare_digest(supplied, "Bearer " + self.server.bearer_token)

    def do_GET(self) -> None:
        if self.path == "/health":
            self.send_json(200, {"status": "ready", "scope": "groq-free-smoke-only"})
            return
        if self.path != "/v1/models" or not self.authorized():
            self.send_json(403, {"error": "route_denied"})
            return
        self.send_json(200, {
            "object": "list",
            "data": [
                {"id": m, "object": "model", "owned_by": "groq"}
                for m in sorted(_ALLOWED)
            ],
        })

    def do_POST(self) -> None:
        if self.path != "/v1/chat/completions" or not self.authorized():
            self.send_json(403, {"error": "route_denied"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= _MAX_BODY:
                self.send_json(413, {"error": "body_outside_limit"})
                return
            body = self.rfile.read(length)
            validate_chat(json.loads(body))
        except (ValueError, UnicodeError, TypeError, json.JSONDecodeError):
            self.send_json(400, {"error": "invalid_or_unsafe_chat"})
            return
        with self.server.lock:
            if self.server.total_posts >= _MAX_POSTS:
                self.send_json(429, {"error": "bounded_free_trial_exhausted"})
                return
            self.server.total_posts += 1
        self.forward(body)

    def forward(self, body: bytes) -> None:
        payload = json.dumps({
            "method": "POST",
            "path": "/v1/chat/completions",
            "body": base64.b64encode(body).decode("ascii"),
        }, separators=(",", ":")).encode("ascii") + b"\n"
        proc: subprocess.Popen[bytes] | None = None
        sent = False
        try:
            proc = subprocess.Popen(
                [self.server.windows_python, self.server.windows_script],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            assert proc.stdin is not None and proc.stdout is not None
            proc.stdin.write(payload)
            proc.stdin.close()
            prefix = proc.stdout.read(4)
            if len(prefix) != 4:
                raise RuntimeError("Windows relay did not return a frame")
            n = struct.unpack("!I", prefix)[0]
            if not 1 <= n <= 4096:
                raise RuntimeError("invalid Windows response frame")
            metadata = json.loads(proc.stdout.read(n))
            status = metadata.get("status")
            if type(status) is not int or not 100 <= status <= 599:
                raise RuntimeError("invalid Windows HTTP status")
            ctype = metadata.get("content_type", "application/json")
            if not isinstance(ctype, str) or not (
                ctype.startswith("application/json") or ctype.startswith("text/event-stream")
            ):
                raise RuntimeError("invalid Windows content type")
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            sent = True
            total = 0
            while chunk := proc.stdout.read1(8192):
                total += len(chunk)
                if total > 8 * 1024 * 1024:
                    raise RuntimeError("bounded response size exceeded")
                self.wfile.write(chunk)
                self.wfile.flush()
            proc.wait(timeout=3)
        except Exception:
            if not sent:
                try:
                    self.send_json(502, {"error": "local_windows_relay_unavailable"})
                except (OSError, BrokenPipeError):
                    pass
        finally:
            if proc is not None:
                if proc.poll() is None:
                    proc.kill()
                    proc.wait(timeout=3)
                if proc.stdout is not None:
                    proc.stdout.close()
                if proc.stdin is not None and not proc.stdin.closed:
                    proc.stdin.close()


def main() -> int:
    if len(sys.argv) != 3:
        print("HARNESS2_GROQ_BRIDGE_REFUSED: expected Windows Python and relay script", file=sys.stderr)
        return 2
    token = os.environ.get("HARNESS2_GROQ_BRIDGE_TOKEN", "")
    if len(token) < 32:
        print("HARNESS2_GROQ_BRIDGE_REFUSED: missing ephemeral token", file=sys.stderr)
        return 2
    with Server(sys.argv[1], sys.argv[2], token) as server:
        print(f"HARNESS2_GROQ_BRIDGE_READY={server.server_port}", flush=True)
        server.serve_forever(poll_interval=0.1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
