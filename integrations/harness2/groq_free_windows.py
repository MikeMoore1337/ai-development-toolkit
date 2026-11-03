#!/usr/bin/env python3
"""One-call FreeLLMAPI relay for the original WSL2 OpenCode smoke.

Runs under Windows Python. The real unified gateway credential stays in the
existing user's FreeLLMAPI SQLite database; it is never sent to WSL2.
No external destinations, arbitrary model names, or credential output.
"""
from __future__ import annotations

import base64
import http.client
import json
import os
from pathlib import Path
import sqlite3
import struct
import sys

_ALLOWED = {"groq:openai/gpt-oss-20b", "groq:openai/gpt-oss-120b"}
_MAX_BODY = 256 * 1024
_MAX_REPLY = 8 * 1024 * 1024
_MAX_TOKENS = 512


def validate_request(message: object) -> tuple[str, str, bytes]:
    if not isinstance(message, dict):
        raise ValueError("request must be a mapping")
    method, path = message.get("method"), message.get("path")
    if (method, path) not in {("GET", "/v1/models"), ("POST", "/v1/chat/completions")}:
        raise ValueError("unsupported route")
    encoded = message.get("body")
    if not isinstance(encoded, str) or len(encoded) > 2 * _MAX_BODY:
        raise ValueError("bad body encoding")
    raw = base64.b64decode(encoded, validate=True)
    if len(raw) > _MAX_BODY:
        raise ValueError("request too large")
    if method == "POST":
        data = json.loads(raw)
        if not isinstance(data, dict) or data.get("model") not in _ALLOWED:
            raise ValueError("model outside Groq Free allowlist")
        tokens = data.get("max_tokens")
        if type(tokens) is not int or not 1 <= tokens <= _MAX_TOKENS:
            raise ValueError("invalid output token budget")
        if not isinstance(data.get("messages"), list) or not data["messages"]:
            raise ValueError("missing messages")
        tools = data.get("tools") or []
        if not isinstance(tools, list) or len(tools) > 1:
            raise ValueError("unsafe tool count")
        for tool in tools:
            if not isinstance(tool, dict) or (tool.get("function") or {}).get("name") != "read":
                raise ValueError("only read tool is allowed")
    elif raw:
        raise ValueError("GET requests must be empty")
    return method, path, raw


def load_gateway() -> tuple[int, str]:
    """Read only the existing desktop gateway's own local authentication."""
    appdata = os.environ.get("APPDATA")
    if not appdata:
        raise RuntimeError("Windows APPDATA not present")
    root = Path(appdata) / "FreeLLMAPI"
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    port = config.get("port")
    if type(port) is not int or not 1024 <= port <= 65535:
        raise RuntimeError("invalid FreeLLMAPI port")
    uri = (root / "freeapi.db").resolve().as_uri() + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=4)
    try:
        status = conn.execute(
            "SELECT status, enabled FROM api_keys WHERE platform = 'groq'"
        ).fetchall()
        if len(status) != 1 or status[0][1] != 1:
            raise RuntimeError("Groq Free key not enabled")
        result = conn.execute(
            "SELECT value FROM settings WHERE key = 'unified_api_key'"
        ).fetchone()
    finally:
        conn.close()
    if not result or not isinstance(result[0], str) or not result[0].startswith("freellmapi-"):
        raise RuntimeError("local unified gateway credential missing")
    return port, result[0]


def frame(meta: dict[str, object]) -> None:
    raw = json.dumps(meta, separators=(",", ":")).encode("utf-8")
    if len(raw) > 4096:
        raise RuntimeError("oversized reply metadata")
    sys.stdout.buffer.write(struct.pack("!I", len(raw)) + raw)
    sys.stdout.buffer.flush()


def relay(request: object) -> None:
    method, path, body = validate_request(request)
    port, key = load_gateway()
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=48)
    header_sent = False
    try:
        conn.request(
            method, path,
            body=body if method == "POST" else None,
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
                "Accept": "text/event-stream, application/json",
            },
        )
        response = conn.getresponse()
        via = response.getheader("X-Routed-Via", "")
        if response.status == 200 and method == "POST" and not via.lower().startswith("groq/"):
            raise RuntimeError("gateway returned an unexpected provider")
        ctype = response.getheader("Content-Type", "application/json")
        if not (ctype.startswith("application/json") or ctype.startswith("text/event-stream")):
            raise RuntimeError("gateway returned an unexpected content type")
        frame({"status": response.status, "content_type": ctype, "routed_via": via[:128]})
        header_sent = True
        total = 0
        while chunk := response.read1(8192):
            total += len(chunk)
            if total > _MAX_REPLY:
                raise RuntimeError("upstream response exceeded bound")
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
    except Exception:
        if not header_sent:
            frame({"status": 502, "content_type": "application/json"})
            sys.stdout.buffer.write(b'{"error":{"message":"bounded Windows relay refused or failed"}}')
            sys.stdout.buffer.flush()
        raise
    finally:
        conn.close()


def main() -> int:
    raw = sys.stdin.buffer.readline(2 * _MAX_BODY + 2)
    if not raw or len(raw) > 2 * _MAX_BODY:
        return 2
    try:
        relay(json.loads(raw))
        return 0
    except Exception:
        # Do not print exceptions: they could contain a provider request or URL.
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
