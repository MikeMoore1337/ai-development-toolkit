#!/usr/bin/env python3
"""Portable, offline-first Toolkit MCP stdio server and project-scoped installer.

Only local Toolkit guidance is exposed over MCP. Writes are intentionally
restricted to an explicit operator CLI action with --apply.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import tomllib
from pathlib import Path

from install import _ensure_no_symlink_chain, skill_sources
from skill_manager import operate

ROOT = Path(__file__).resolve().parents[1]
NAME = "ai-development-toolkit"
PROTOCOL = "2025-11-25"
MAX_INPUT = 1_000_000
MAX_TEXT = 65_536
MAX_SEARCH = 15
INSTRUCTIONS = (
    "Toolkit is a read-only skill and role reference. Search, route, and read "
    "only relevant skills; a plan does not install them. Never claim that an "
    "AI client activated a skill unless independently observed. Never use this "
    "server to edit a user project, run commands, or publish. "
    "For local changes request human review of the Skill Manager preview."
)


def catalog() -> dict:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    return {"version": str(manifest["version"]), "profiles": sorted(manifest["profiles"]),
            "skills": sorted(skill_sources(manifest))}


def _sources() -> dict:
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    return skill_sources(manifest)


def _name(value: object) -> str:
    if not isinstance(value, str) or len(value) > 100 or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", value):
        raise ValueError("Invalid skill name")
    return value


def _roles() -> dict[str, Path]:
    found = {}
    for folder in (ROOT / ".agents" / "roles", ROOT / "extensions" / "qa" / "roles"):
        if not folder.is_dir() or folder.is_symlink():
            continue
        for path in folder.glob("*.md"):
            if path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(ROOT.resolve()):
                if path.stem in found:
                    raise ValueError("Duplicate declared role")
                found[path.stem] = path
    return found


def _tool_defs() -> list[dict]:
    string = lambda description: {"type": "string", "description": description}
    return [
        {"name": "toolkit_catalog", "description": "List local Toolkit skills/profiles and version. Read only.",
         "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
         "annotations": {"readOnlyHint": True}},
        {"name": "toolkit_list_roles", "description": "List available specialist and QA reference roles.",
         "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
         "annotations": {"readOnlyHint": True}},
        {"name": "toolkit_read_role", "description": "Read a reference role without creating or starting an autonomous agent.",
         "inputSchema": {"type": "object", "properties": {"role": string("Exact name from toolkit_list_roles")},
                         "required": ["role"], "additionalProperties": False},
         "annotations": {"readOnlyHint": True}},
        {"name": "toolkit_search_skills",
         "description": "Find potentially relevant skills by words in names and summaries. Results are suggestions, not proof of activation.",
         "inputSchema": {"type": "object", "properties": {"query": string("Task or skill keywords")},
                         "required": ["query"], "additionalProperties": False},
         "annotations": {"readOnlyHint": True}},
        {"name": "toolkit_read_skill", "description": "Read a declared local SKILL.md or a reference inside that skill.",
         "inputSchema": {"type": "object",
                         "properties": {"skill": string("Exact skill name from catalog"),
                                        "reference": string("Optional path inside the selected skill, e.g. references/checklist.md")},
                         "required": ["skill"], "additionalProperties": False},
         "annotations": {"readOnlyHint": True}},
        {"name": "toolkit_route_task", "description": "Return an advisory profile and matching skill suggestions for a task.",
         "inputSchema": {"type": "object", "properties": {"task": string("Task description")},
                         "required": ["task"], "additionalProperties": False},
         "annotations": {"readOnlyHint": True}},
        {"name": "toolkit_preview_install",
         "description": "Preview Skill Manager changes for an already existing project. Does NOT install or modify files.",
         "inputSchema": {"type": "object",
                         "properties": {"project": string("Existing absolute project directory"),
                                        "skills": {"type": "array", "items": string("Skill name"), "minItems": 1, "maxItems": 10},
                                        "layout": {"type": "string", "enum": ["codex", "claude"]}},
                         "required": ["project", "skills", "layout"], "additionalProperties": False},
         "annotations": {"readOnlyHint": True}},
        {"name": "toolkit_status", "description": "Read Skill Manager ownership status in an existing project, without writes.",
         "inputSchema": {"type": "object",
                         "properties": {"project": string("Existing absolute project directory"),
                                        "layout": {"type": "string", "enum": ["codex", "claude"]}},
                         "required": ["project", "layout"], "additionalProperties": False},
         "annotations": {"readOnlyHint": True}},
    ]


def _project(value: object) -> Path:
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise ValueError("Project must be a nonempty absolute path")
    path = Path(value).expanduser()
    if not path.is_absolute() or not path.is_dir():
        raise ValueError("Project must be an existing absolute directory")
    _ensure_no_symlink_chain(path)
    return path


def _layout(value: object) -> str:
    if value not in ("codex", "claude"):
        raise ValueError("layout must be codex or claude")
    return value


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


def _search(query: str) -> list[dict]:
    if not isinstance(query, str) or not query.strip() or len(query) > 500:
        raise ValueError("query must be 1-500 characters")
    words = set(re.findall(r"[\w-]{3,}", query.casefold()))
    results = []
    for name, path in _sources().items():
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()):
            continue
        doc = path / "SKILL.md"
        if not doc.is_file() or doc.is_symlink():
            continue
        summary = doc.read_text(encoding="utf-8")[:1800]
        hay = (name + " " + summary).casefold()
        score = sum((4 if word in name else 1) for word in words if word in hay)
        if score:
            results.append({"skill": name, "score": score,
                            "description": " ".join(summary.split())[:260]})
    return sorted(results, key=lambda x: (-x["score"], x["skill"]))[:MAX_SEARCH]


def invoke(tool: str, args: dict) -> dict:
    if not isinstance(args, dict):
        raise ValueError("Tool arguments must be an object")
    if tool == "toolkit_catalog":
        return catalog()
    if tool == "toolkit_list_roles":
        return {"roles": sorted(_roles()), "status": "REFERENCE_ONLY"}
    if tool == "toolkit_read_role":
        name = _name(args.get("role"))
        path = _roles().get(name)
        if path is None or path.stat().st_size > MAX_TEXT:
            raise ValueError("Unknown or oversized reference role")
        _ensure_no_symlink_chain(path)
        return {"role": name, "text": path.read_text(encoding="utf-8"),
                "status": "ROLE_REFERENCE_NOT_STARTED_AGENT"}
    if tool in ("toolkit_search_skills", "toolkit_route_task"):
        query = args.get("query") if tool == "toolkit_search_skills" else args.get("task")
        matches = _search(query)
        if tool == "toolkit_search_skills":
            return {"matches": matches, "status": "SUGGESTED_NOT_ACTIVATED"}
        profiles = catalog()["profiles"]
        query_terms = set(re.findall(r"[a-z0-9-]+", query.casefold()))
        candidates = [profile for profile in profiles
                      if any(part in query_terms for part in profile.split("-"))]
        normalized = " ".join(query.casefold().replace("ё", "е").split())
        if "prompt-refinement" in profiles and _explicit_prompt_request(query):
            candidates = ["prompt-refinement"]
        elif ("ui-orchestra" in profiles and
              re.search(r'\b(?:сделай|создай|разработай|нарисуй)\s+'
                        r'(?:(?:красивый|современный)\s+)?(?:сайт|лендинг)\b',
                        normalized)):
            candidates = ["ui-orchestra"]
        elif ("seo-audit" in profiles and
              (re.search(r'(?<!\w)(?:seo|сео)(?!\w)', normalized)
               or "поисков" in normalized or "не индексируется" in normalized)):
            candidates = ["seo-audit"]
        role_words = set(re.findall(r"[a-z0-9-]+", query.casefold()))
        role_matches = [name for name in sorted(_roles())
                        if any(word in name for word in role_words if len(word) >= 4)]
        return {"profile": candidates[0] if candidates else ("general" if "general" in profiles else None),
                "skills": matches[:5], "roles": role_matches[:5],
                "status": "ADVISORY_ONLY", "requires_review": True}
    if tool == "toolkit_read_skill":
        name = _name(args.get("skill"))
        sources = _sources()
        if name not in sources:
            raise ValueError("Unknown skill")
        rel = args.get("reference", "SKILL.md")
        if not isinstance(rel, str) or len(rel) > 200 or "\\" in rel or rel.startswith("/"):
            raise ValueError("Invalid reference path")
        parts = rel.split("/")
        if any(part in ("", ".", "..") for part in parts) or (rel != "SKILL.md" and not rel.startswith("references/")):
            raise ValueError("Only SKILL.md or skill references/ are readable")
        path = sources[name] / rel
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(sources[name].resolve()):
            raise ValueError("Unavailable or unsafe reference")
        _ensure_no_symlink_chain(path)
        if path.stat().st_size > MAX_TEXT:
            raise ValueError("Document exceeds read limit")
        return {"skill": name, "reference": rel, "text": path.read_text(encoding="utf-8"),
                "status": "SOURCE_READ_NOT_CLIENT_ACTIVATION"}
    if tool in ("toolkit_status", "toolkit_preview_install"):
        project = _project(args.get("project"))
        layout = _layout(args.get("layout"))
        if tool == "toolkit_status":
            return {"status": "READ_ONLY", "result": operate("status", project, layout=layout)}
        names = args.get("skills")
        if not isinstance(names, list) or not 1 <= len(names) <= 10:
            raise ValueError("skills must be a list of 1-10 names")
        names = [_name(n) for n in names]
        return {"status": "PREVIEW_ONLY", "result": operate("install", project, names=names,
                                                            layout=layout, apply=False)}
    raise ValueError("Unknown Toolkit tool")


def _error(request_id: object, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle(message: object) -> dict | None:
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        return _error(None, -32600, "Invalid JSON-RPC request")
    request_id = message.get("id")
    if "id" not in message:
        return None  # Notifications do not receive a response.
    if not isinstance(request_id, (str, int)) or isinstance(request_id, bool):
        return _error(None, -32600, "Invalid request id")
    method = message.get("method")
    params = message.get("params", {})
    if not isinstance(params, dict):
        return _error(request_id, -32602, "Invalid params")
    if method == "initialize":
        version = params.get("protocolVersion")
        if version not in (PROTOCOL, "2025-06-18", "2025-03-26"):
            version = PROTOCOL
        result = {"protocolVersion": version, "capabilities": {"tools": {"listChanged": False}},
                  "serverInfo": {"name": NAME, "version": catalog()["version"]},
                  "instructions": INSTRUCTIONS}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": _tool_defs()}
    elif method == "resources/list":
        result = {"resources": []}
    elif method == "prompts/list":
        result = {"prompts": []}
    elif method == "tools/call":
        tool = params.get("name")
        if tool not in {t["name"] for t in _tool_defs()}:
            return _error(request_id, -32602, "Unknown tool")
        try:
            value = invoke(tool, params.get("arguments", {}))
            result = {"content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False)}],
                      "structuredContent": value}
        except (ValueError, OSError, KeyError, TypeError) as exc:
            result = {"content": [{"type": "text", "text": str(exc)[:300]}], "isError": True}
    else:
        return _error(request_id, -32601, "Method not found")
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def serve() -> None:
    for raw in sys.stdin.buffer:
        if len(raw) > MAX_INPUT:
            response = _error(None, -32700, "Request too large")
        else:
            try:
                response = handle(json.loads(raw))
            except (ValueError, UnicodeError, TypeError):
                response = _error(None, -32700, "Parse error")
            except Exception:  # Keep the stdio transport alive without leaking secrets.
                response = _error(None, -32603, "Internal server error")
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
            sys.stdout.flush()


def _client_path(project: Path, client: str) -> Path:
    if client not in ("codex", "claude"):
        raise ValueError("Client must be codex or claude")
    return project / (".codex/config.toml" if client == "codex" else ".mcp.json")


def _entry() -> dict:
    return {"command": sys.executable, "args": [str(Path(__file__).resolve()), "serve"]}


def config_plan(project: Path, client: str, *, remove: bool = False) -> tuple[Path, bytes | None, str]:
    path = _client_path(project, client)
    _ensure_no_symlink_chain(path)
    old = path.read_bytes() if path.is_file() else b""
    entry = _entry()
    if client == "claude":
        current = json.loads(old.decode("utf-8")) if old else {}
        if not isinstance(current, dict):
            raise ValueError("Invalid .mcp.json root")
        servers = current.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            raise ValueError("Invalid mcpServers object")
        if NAME in servers and servers[NAME] != entry:
            raise ValueError("Existing Toolkit MCP entry differs; refusing overwrite/removal")
        if remove:
            if NAME not in servers:
                return path, None, "ALREADY_ABSENT"
            servers.pop(NAME)
        else:
            if NAME in servers:
                return path, None, "ALREADY_INSTALLED"
            servers[NAME] = entry
        result = (json.dumps(current, indent=2, ensure_ascii=False) + "\n").encode()
    else:
        current = old.decode("utf-8")
        parsed = tomllib.loads(current) if current.strip() else {}
        servers = parsed.get("mcp_servers", {})
        if not isinstance(servers, dict):
            raise ValueError("Invalid Codex mcp_servers table")
        if NAME in servers:
            v = servers[NAME]
            if not isinstance(v, dict) or v.get("command") != entry["command"] or v.get("args") != entry["args"]:
                raise ValueError("Existing Toolkit MCP entry differs; refusing overwrite/removal")
            if not remove:
                return path, None, "ALREADY_INSTALLED"
            pattern = r"(?m)^\[mcp_servers\.ai-development-toolkit\]\s*\n(?:(?!^\[).*\n?)*"
            modified, count = re.subn(pattern, "", current)
            if count != 1:
                raise ValueError("Could not safely identify managed Codex block")
            result = modified.encode()
        else:
            if remove:
                return path, None, "ALREADY_ABSENT"
            heading = "\n" if not current or current.endswith("\n") else "\n\n"
            block = ("[mcp_servers.ai-development-toolkit]\n"
                     "command = " + json.dumps(entry["command"]) + "\n"
                     "args = " + json.dumps(entry["args"]) + "\n")
            result = (current + heading + block).encode()
            tomllib.loads(result.decode("utf-8"))
    return path, result, ("REMOVE" if remove else "INSTALL")


def configure(project: str, client: str, *, apply: bool, remove: bool = False) -> dict:
    target = _project(project)
    path, data, action = config_plan(target, client, remove=remove)
    report = {"action": action, "client": client, "path": str(path),
              "project": str(target), "applied": False}
    if data is None:
        return report
    if not apply:
        return report
    _ensure_no_symlink_chain(path.parent)
    path.parent.mkdir(parents=True, exist_ok=True)
    _ensure_no_symlink_chain(path)
    # Do not overwrite a destination that changed since preview.
    _, check, _ = config_plan(target, client, remove=remove)
    if check != data:
        raise ValueError("Config changed while preparing write")
    fd, tmp = tempfile.mkstemp(prefix=".toolkit-mcp-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    report["applied"] = True
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("serve")
    for action in ("install", "uninstall", "doctor"):
        p = sub.add_parser(action, help="Project-scoped config; preview unless --apply")
        p.add_argument("--client", required=True, choices=("codex", "claude"))
        p.add_argument("--project", required=True, help="Existing trusted project path")
        if action != "doctor":
            p.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if args.action == "serve":
        serve()
        return 0
    try:
        report = configure(args.project, args.client, apply=getattr(args, "apply", False),
                           remove=(args.action == "uninstall"))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        print("ERROR: " + str(exc)[:300], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
