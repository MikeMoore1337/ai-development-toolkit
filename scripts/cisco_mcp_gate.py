#!/usr/bin/env python3
"""Opt-in, source-only Toolkit MCP contract scan using pinned Cisco MCP Scanner.

Never connect to, execute, discover or authenticate against a live MCP server.
A temporary JSON snapshot contains tool descriptions and input schemas only.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
CISCO_COMMIT = "4dd0caae7b0d3a80c8c09ed7e4680a9911b0a86e"
CISCO_SOURCE = f"git+https://github.com/cisco-ai-defense/mcp-scanner.git@{CISCO_COMMIT}"
EXPECTED_ANALYZERS = frozenset({"yara", "schema"})
MAX_STDOUT = 2 * 1024 * 1024
MAX_SNAPSHOT = 384 * 1024
TIMEOUT_SECONDS = 240
ALLOWED_ENV = frozenset({
    "PATH", "HOME", "USERPROFILE", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP",
    "TMP", "TMPDIR", "APPDATA", "LOCALAPPDATA", "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME", "XDG_DATA_HOME", "LANG", "LC_ALL", "CI",
    "PYTHONIOENCODING", "NO_COLOR", "UV_CACHE_DIR", "SSL_CERT_FILE",
    "SSL_CERT_DIR",
})


def _blocked(reason: str, scope: str, **extra: object) -> dict:
    return {"status": "BLOCKED", "reason": reason, "scope": scope,
            "scanner": "Cisco MCP Scanner", "source_commit": CISCO_COMMIT,
            "analyzers": sorted(EXPECTED_ANALYZERS), "live_mcp": "NOT_RUN",
            "paid_api": "NOT_USED", **extra}


def snapshot(scope: str = "personal") -> dict:
    """Read first-party declarative tool definitions; no server is started."""
    if scope == "personal":
        module_root = ROOT / "integrations" / "personal-mcp" / "adt-personal" / "mcp"
        sys.path.insert(0, str(module_root))
        try:
            # adt_mcp imports a first-party local helper; it does not serve()
            # until __main__ runs. It must never call dispatch or tools/call.
            mod = importlib.import_module("adt_mcp")
            tools = mod.TOOLS
        finally:
            sys.path.pop(0)
    elif scope == "project":
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            mod = importlib.import_module("toolkit_mcp")
            tools = mod._tool_defs()
        finally:
            sys.path.pop(0)
    else:
        raise ValueError("Unknown first-party MCP scope")
    if (not isinstance(tools, list) or not tools
            or len(tools) > 100 or any(
                not isinstance(t, dict)
                or not isinstance(t.get("name"), str)
                or not t["name"].startswith("toolkit_")
                or not isinstance(t.get("description"), str)
                or not isinstance(t.get("inputSchema"), dict)
                for t in tools)):
        raise ValueError("Unexpected MCP tool schema")
    if len({t["name"] for t in tools}) != len(tools):
        raise ValueError("Duplicate MCP tool names")
    # JSON roundtrip detaches caller input and rejects non-JSON data.
    data = {"tools": json.loads(json.dumps(tools, ensure_ascii=False))}
    if len(json.dumps(data, ensure_ascii=False).encode("utf-8")) > MAX_SNAPSHOT:
        raise ValueError("Oversized MCP declaration")
    return data


def verify_report(payload: object, expected_names: set[str], scope: str,
                  exit_code: int) -> dict:
    """Enforce complete tool coverage; scanner failures can never pass."""
    if exit_code != 0 or not isinstance(payload, dict):
        return _blocked("SCANNER_FAILED_OR_INVALID_REPORT", scope)
    if payload.get("requested_analyzers") != ["yara", "schema"]:
        return _blocked("ANALYZER_SCOPE_MISMATCH", scope)
    items = payload.get("scan_results")
    if not isinstance(items, list) or len(items) != len(expected_names):
        return _blocked("INCOMPLETE_TOOL_COVERAGE", scope)
    seen: set[str] = set()
    reviews: list[dict] = []
    for result in items:
        if not isinstance(result, dict) or not isinstance(result.get("tool_name"), str):
            return _blocked("INVALID_TOOL_RESULT", scope)
        name = result["tool_name"]
        if (name not in expected_names or name in seen
                or result.get("status") != "completed"
                or result.get("is_safe") not in (True, False)
                or type(result.get("is_safe")) is not bool
                or result.get("analyzer_errors")):
            return _blocked("INCOMPLETE_OR_UNTRUSTED_RESULT", scope)
        seen.add(name)
        found = result.get("findings")
        if not isinstance(found, dict):
            return _blocked("MISSING_ANALYZER_EVIDENCE", scope)
        for analyzer in ("yara_analyzer", "schema_analyzer"):
            item = found.get(analyzer)
            if (not isinstance(item, dict) or item.get("status") in ("error", "partial")
                    or item.get("severity") not in ("SAFE", "INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")
                    or type(item.get("total_findings")) is not int
                    or item["total_findings"] < 0):
                return _blocked("MISSING_ANALYZER_EVIDENCE", scope)
            if item["total_findings"] or item["severity"] not in ("SAFE", "INFO"):
                reviews.append({"tool": name, "analyzer": analyzer,
                                "severity": item["severity"],
                                "count": item["total_findings"]})
        if result["is_safe"] is False and not any(x["tool"] == name for x in reviews):
            return _blocked("INCONSISTENT_SAFETY_VERDICT", scope)
        if result["is_safe"] is True and any(x["tool"] == name for x in reviews):
            return _blocked("INCONSISTENT_SAFETY_VERDICT", scope)
    if seen != expected_names:
        return _blocked("INCOMPLETE_TOOL_COVERAGE", scope)
    status = ("BLOCKED" if any(x["severity"] in ("HIGH", "CRITICAL") for x in reviews)
              else "REVIEW_REQUIRED" if reviews else "PASS")
    return {"status": status, "reason": "STATIC_CONTRACT_SCAN", "scope": scope,
            "scanner": "Cisco MCP Scanner", "source_commit": CISCO_COMMIT,
            "analyzers": sorted(EXPECTED_ANALYZERS), "tool_count": len(seen),
            "findings": reviews, "live_mcp": "NOT_RUN", "paid_api": "NOT_USED"}


def scan(scope: str = "personal", *,
         runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
         executable: str = "uvx",
         environ: Mapping[str, str] | None = None) -> dict:
    """Run isolated static tool-description scan; never invoke MCP methods."""
    try:
        data = snapshot(scope)
    except (ValueError, OSError, TypeError, ImportError, KeyError):
        return _blocked("SNAPSHOT_UNAVAILABLE", scope)
    raw = json.dumps(data, ensure_ascii=False)
    incoming = os.environ if environ is None else environ
    env = {k: v for k, v in incoming.items() if k.upper() in ALLOWED_ENV}
    # Force uv to disregard credential-bearing user-wide index overrides.
    env["UV_NO_CONFIG"] = "1"
    try:
        with tempfile.TemporaryDirectory(prefix="adt-mcp-cisco-") as directory:
            path = Path(directory) / "tools.json"
            path.write_text(raw, encoding="utf-8")
            cmd = [
                executable, "--from", CISCO_SOURCE, "mcp-scanner",
                "--analyzers", "yara,schema", "--format", "raw",
                "static", "--tools", str(path),
            ]
            proc = runner(cmd, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=TIMEOUT_SECONDS, env=env,
                          check=False)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return _blocked("SCANNER_UNAVAILABLE_OR_TIMEOUT", scope)
    if proc.returncode != 0 or not isinstance(proc.stdout, str):
        return _blocked("SCANNER_FAILED", scope)
    if len(proc.stdout.encode("utf-8")) > MAX_STDOUT:
        return _blocked("REPORT_TOO_LARGE", scope)
    try:
        output = json.loads(proc.stdout)
    except (ValueError, TypeError):
        return _blocked("INVALID_REPORT_JSON", scope)
    return verify_report(output, {t["name"] for t in data["tools"]}, scope,
                         proc.returncode)



# Native, deliberately narrow MCP poisoning detection (#432). Unlike the
# optional Cisco subprocess, this checks first-party declarations offline.
# This is not a replacement for a complete YARA/schema or runtime audit.
NATIVE_PATTERNS = (
    ("PROMPT_OVERRIDE", "HIGH", re.compile(
        r"\bignore\s+(?:all\s+|previous\s+|prior\s+)?instructions?\b|"
        r"\bигнорируй\s+(?:все\s+)?(?:предыдущие\s+)?инструкции\b", re.I)),
    ("ROLE_FORGERY", "HIGH", re.compile(
        r"(?:^|[\n\r])\s*(?:system|assistant)\s*:|"
        r"\byou\s+are\s+now\s+the\s+system\b", re.I)),
    ("SECRET_EXFILTRATION_INSTRUCTION", "HIGH", re.compile(
        r"\b(?:send|upload|exfiltrate|steal|отправь|передай|загрузи)\b.{0,80}"
        r"\b(?:tokens?|secrets?|credentials?|passwords?|ключи?|пароли?|токены?)\b",
        re.I)),
    ("EXTERNAL_COLLECTION_ENDPOINT", "MEDIUM", re.compile(
        r"\b(?:webhook\.site|ngrok\.(?:io|app)|requestbin\.com)\b",
        re.I)),
)


def _native_desc_fields(value: object, depth: int = 0) -> list[str]:
    """Bounded JSON-schema description walk; no evaluation of descriptions."""
    if depth > 12:
        raise ValueError("Overdeep schema")
    if isinstance(value, dict):
        if len(value) > 256:
            raise ValueError("Oversized schema object")
        found = []
        for key, item in value.items():
            if key == "description":
                if not isinstance(item, str) or len(item.encode("utf-8")) > 16_384:
                    raise ValueError("Invalid description")
                found.append(item)
            elif isinstance(item, (dict, list)):
                found.extend(_native_desc_fields(item, depth + 1))
        return found
    if isinstance(value, list):
        if len(value) > 128:
            raise ValueError("Oversized schema array")
        found = []
        for item in value:
            if isinstance(item, (dict, list)):
                found.extend(_native_desc_fields(item, depth + 1))
            elif not isinstance(item, (str, int, float, bool, type(None))):
                raise ValueError("Unsupported schema array item")
        return found
    raise ValueError("Unexpected schema")


def scan_native_descriptions(scope: str = "personal", *, data: dict | None = None) -> dict:
    """Pure source/fixture heuristic; never starts Cisco, an MCP server or a model."""
    base = {"scope": scope, "scanner": "Toolkit Native MCP Description Gate",
            "external_scanner": "NOT_USED", "live_mcp": "NOT_RUN",
            "paid_api": "NOT_USED", "runtime_enforcement": "NOT_VERIFIED"}
    try:
        payload = snapshot(scope) if data is None else data
        raw = json.dumps(payload, ensure_ascii=False, allow_nan=False)
        if len(raw.encode("utf-8")) > MAX_SNAPSHOT or not isinstance(payload, dict):
            raise ValueError("Invalid snapshot")
        tools = payload.get("tools")
        if not isinstance(tools, list) or not 1 <= len(tools) <= 100:
            raise ValueError("Incomplete tools")
        names = set()
        findings: list[dict] = []
        for item in tools:
            if not isinstance(item, dict):
                raise ValueError("Invalid tool")
            name = item.get("name")
            if (not isinstance(name, str) or not name.startswith("toolkit_")
                    or len(name) > 100 or
                    not all(c.isascii() and (c.isalnum() or c == "_") for c in name)
                    or name in names):
                raise ValueError("Invalid or duplicate tool name")
            names.add(name)
            if not isinstance(item.get("inputSchema"), dict):
                raise ValueError("Missing tool schema")
            texts = _native_desc_fields(item)
            if not texts:
                raise ValueError("No inspected description")
            for label, severity, pattern in NATIVE_PATTERNS:
                if any(pattern.search(message) for message in texts):
                    findings.append({"tool": name, "rule": label, "severity": severity})
        status = ("BLOCKED" if any(f["severity"] == "HIGH" for f in findings) else
                  "REVIEW_REQUIRED" if findings else "PASS")
        return {**base, "status": status, "reason": "HEURISTIC_STATIC_ONLY",
                "tool_count": len(names), "findings": findings,
                "claim": "NO_MATCH_IS_NOT_PROOF_OF_SAFETY"}
    except (ValueError, TypeError, RecursionError, ImportError, OSError, KeyError):
        return {**base, "status": "BLOCKED", "reason": "INVALID_OR_INCOMPLETE_SNAPSHOT",
                "findings": [], "claim": "NOT_EVALUATED"}

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scope", choices=("personal", "project"), default="personal")
    parser.add_argument("--native", action="store_true",
                        help="Pure native heuristic scan; no Cisco runtime or network")
    args = parser.parse_args()
    result = scan_native_descriptions(args.scope) if args.native else scan(args.scope)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
