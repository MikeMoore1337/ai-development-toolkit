#!/usr/bin/env python3
"""Offline, read-only review gate for candidate third-party Agent Skills.

This scanner is advisory and does not download, execute, install or authorize skills.
The manifest is operator-supplied metadata, not trusted evidence of upstream origin.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from urllib.parse import urlsplit

MAX_MANIFEST_BYTES = 32_768
MAX_FILES = 80
MAX_FILE_BYTES = 512 * 1024
MAX_TOTAL_BYTES = 2 * 1024 * 1024
PIN = re.compile(r"[a-f0-9]{40}\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "CC0-1.0", "ISC", "MPL-2.0"}
SCRIPT_SUFFIXES = {".sh", ".bash", ".ps1", ".bat", ".cmd", ".py", ".js", ".mjs", ".exe", ".dll", ".so"}
# References are review signals, never automatically trusted as bundled files.
# These match explicit launch/download/hook instructions in SKILL.md without
# executing anything or interpreting those instructions as commands.
EXECUTION_REFERENCES = (
    re.compile(r"(?:^|[\s\x60'\"(])(?:[A-Za-z0-9_.<>-]+/)*scripts/[A-Za-z0-9_./-]+", re.I),
    re.compile(r"\b(?:npx|bunx|pipx|pnpm\s+dlx|curl|wget|powershell|bash)\s+\S+", re.I),
    re.compile(r"\b(?:launcher|executable|binary)\b.{0,120}\b(?:download|run|execute|install)\b", re.I | re.S),
    re.compile(r"\b(?:hooks?|postinstall|preinstall)\b.{0,90}\b(?:enable|install|register|on|off|runs?)\b", re.I | re.S),
)
# Only explicit local Markdown references are interpreted, and only as data.
LOCAL_REFERENCES = re.compile(r"\]\(((?:reference|references|scripts)/[A-Za-z0-9_./-]+)\)")
SUSPICIOUS = (
    re.compile(r"ignore (?:all |previous |prior )?instructions", re.I),
    re.compile(r"(?:curl|wget)\s+.*(?:\||-o|--output)", re.I),
    re.compile(r"\b(?:rm\s+-rf|subprocess\.|os\.system\(|eval\(|exec\()", re.I),
    re.compile(r"(?:\.ssh/|\.aws/|\.config/|\.env\b|api[_-]?key|access[_-]?token)", re.I),
    re.compile(r"(?:send|upload|exfiltrat).{0,60}(?:secret|token|cookie|credential|repository)", re.I),
)


def _issue(code: str, severity: str, path: str | None = None) -> dict:
    result = {"code": code, "severity": severity}
    if path is not None:
        result["path"] = path
    return result


def _safe_name(name: object) -> bool:
    if not isinstance(name, str) or not name or len(name) > 240 or "\\" in name:
        return False
    if any(ord(char) < 32 for char in name):
        return False
    pure = PurePosixPath(name)
    return not pure.is_absolute() and all(segment not in {"", ".", ".."} for segment in name.split("/"))


def _manifest(source: Path, issues: list[dict]) -> dict | None:
    try:
        if source.is_symlink() or not source.is_file() or source.stat().st_size > MAX_MANIFEST_BYTES:
            raise ValueError("Missing, linked or oversized manifest")
        data = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) != {
            "schema_version", "candidate_id", "source_url", "source_revision", "license", "files"
        } or data["schema_version"] != 1:
            raise ValueError("Invalid manifest structure")
        if not isinstance(data["candidate_id"], str) or not SLUG.fullmatch(data["candidate_id"]):
            raise ValueError("Invalid candidate ID")
        if not isinstance(data["source_revision"], str) or not PIN.fullmatch(data["source_revision"]):
            raise ValueError("Revision must be a full pinned commit SHA")
        if not isinstance(data["source_url"], str):
            raise ValueError("Invalid source URL")
        url = urlsplit(data["source_url"])
        if (url.scheme != "https" or url.hostname != "github.com" or url.username or url.password
                or url.port is not None or url.query or url.fragment
                or not re.fullmatch(r"/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/?", url.path)):
            raise ValueError("Source must be an explicit HTTPS GitHub repository URL")
        files = data["files"]
        if (not isinstance(files, dict) or not 1 <= len(files) <= MAX_FILES
                or "SKILL.md" not in files or any(not _safe_name(path)
                or not isinstance(digest, str) or not DIGEST.fullmatch(digest)
                for path, digest in files.items())):
            raise ValueError("Invalid or unpinned expected file inventory")
        return data
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        issues.append(_issue("INVALID_MANIFEST", "BLOCK"))
        return None


MAX_CONTEXT_BYTES = 16_384
CONTEXT_FIELDS = frozenset({
    "schema_version", "task_goals", "existing_skill_overlap",
    "requested_permissions", "dependencies", "cost_class", "removal_plan",
})
PERMISSIONS = frozenset({
    "project_read", "project_write", "shell", "network", "secrets",
    "browser_session", "deploy",
})
COST_CLASSES = frozenset({"NO_PAID_API_CLAIMED", "PAID_API", "UNKNOWN"})
REMOVAL_PLANS = frozenset({"REMOVE_MANAGED_FILES", "RESTORE_PINNED_REVISION", "UNKNOWN"})
REVIEW_ID = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")


def _context(path: Path, candidate: Path) -> dict:
    """Bounded operator declaration outside untrusted candidate; never execute it."""
    if (path.is_symlink() or not path.is_file()
            or path.resolve().is_relative_to(candidate.resolve())):
        raise ValueError("Context must be a regular file outside candidate tree")
    try:
        with path.open("rb") as file:
            raw = file.read(MAX_CONTEXT_BYTES + 1)
        if len(raw) > MAX_CONTEXT_BYTES:
            raise ValueError("Review context too large")
        document = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise ValueError("Invalid review context") from exc
    if not isinstance(document, dict) or set(document) != CONTEXT_FIELDS:
        raise ValueError("Invalid review context fields")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise ValueError("Invalid context schema version")
    for field, maximum, allow_empty in (
        ("task_goals", 12, False), ("existing_skill_overlap", 12, True),
        ("requested_permissions", 7, True), ("dependencies", 16, True),
    ):
        values = document[field]
        if (not isinstance(values, list) or len(values) > maximum
                or (not allow_empty and not values)
                or any(not isinstance(v, str) or
                       (field != "requested_permissions" and not REVIEW_ID.fullmatch(v))
                       for v in values)
                or len(set(values)) != len(values)):
            raise ValueError("Invalid context value: " + field)
    if not set(document["requested_permissions"]) <= PERMISSIONS:
        raise ValueError("Unknown requested permission")
    if (not isinstance(document["cost_class"], str)
            or not isinstance(document["removal_plan"], str)
            or document["cost_class"] not in COST_CLASSES
            or document["removal_plan"] not in REMOVAL_PLANS):
        raise ValueError("Unsupported cost or removal category")
    return document


def _dossier(metadata: dict | None, declaration: dict | None,
             candidate_issues: list[dict]) -> dict:
    """Do not upgrade unverified operator metadata into provenance or authority."""
    return {
        "classification": "OFFLINE_OPERATOR_DECLARATION_AND_FILE_SCAN",
        "source_url_claim": metadata["source_url"] if metadata else None,
        "source_revision_claim": metadata["source_revision"] if metadata else None,
        "license_claim": metadata["license"] if metadata else None,
        "task_goals": declaration["task_goals"] if declaration else [],
        "existing_skill_overlap_claim": declaration["existing_skill_overlap"] if declaration else [],
        "requested_permissions_claim": declaration["requested_permissions"] if declaration else [],
        "dependencies_claim": declaration["dependencies"] if declaration else [],
        "cost_class_claim": declaration["cost_class"] if declaration else "UNKNOWN",
        "removal_plan_claim": declaration["removal_plan"] if declaration else "UNKNOWN",
        "context_status": "OPERATOR_DECLARED_NOT_VERIFIED" if declaration else "NOT_PROVIDED",
        "upstream_revision_verified": False,
        "license_grant_verified": False,
        "overlap_and_dependencies_verified": False,
        "runtime_cost_verified": False,
        "removal_tested": False,
        "prompt_injection_absence_proven": False,
        "publication_gate": "BLOCKED_PENDING_INDEPENDENT_PROVENANCE_AND_OWNER_APPROVAL",
        "installation": "NOT_AUTHORIZED",
        "negative_findings": sorted({item["code"] for item in candidate_issues}),
    }


def review(candidate_dir: Path, manifest_file: Path,
           review_context: Path | None = None) -> dict:
    """Inspect a local candidate only. No network, subprocess or writes."""
    issues: list[dict] = []
    data = _manifest(manifest_file, issues)
    declared = None
    if review_context is not None:
        try:
            declared = _context(review_context, candidate_dir)
        except (ValueError, OSError):
            issues.append(_issue("INVALID_REVIEW_CONTEXT", "BLOCK"))
        else:
            if declared["existing_skill_overlap"]:
                issues.append(_issue("OVERLAP_REQUIRES_REVIEW", "REVIEW"))
            if set(declared["requested_permissions"]) - {"project_read"}:
                issues.append(_issue("REQUESTED_PRIVILEGES_REVIEW", "REVIEW"))
            if declared["cost_class"] == "PAID_API":
                issues.append(_issue("PAID_API_NOT_ALLOWED", "BLOCK"))
            elif declared["cost_class"] == "UNKNOWN":
                issues.append(_issue("COST_UNVERIFIED", "REVIEW"))
            if declared["removal_plan"] == "UNKNOWN":
                issues.append(_issue("REMOVAL_PLAN_MISSING", "REVIEW"))
    if candidate_dir.is_symlink() or not candidate_dir.is_dir():
        issues.append(_issue("INVALID_CANDIDATE_DIRECTORY", "BLOCK"))
    actual: dict[str, Path] = {}
    total = 0
    if candidate_dir.is_dir() and not candidate_dir.is_symlink():
        for directory, subdirs, filenames in os.walk(candidate_dir, topdown=True, followlinks=False):
            parent = Path(directory)
            for subdir in list(subdirs):
                folder = parent / subdir
                rel = folder.relative_to(candidate_dir).as_posix()
                if folder.is_symlink() or subdir == ".git":
                    issues.append(_issue("UNSAFE_DIRECTORY", "BLOCK", rel))
                    subdirs.remove(subdir)
            for filename in filenames:
                path = parent / filename
                rel = path.relative_to(candidate_dir).as_posix()
                if not _safe_name(rel) or path.is_symlink() or not path.is_file():
                    issues.append(_issue("UNSAFE_FILE", "BLOCK", rel))
                    continue
                actual[rel] = path
                if len(actual) > MAX_FILES:
                    issues.append(_issue("TOO_MANY_FILES", "BLOCK"))
                    break
            if len(actual) > MAX_FILES:
                break
    if data is not None:
        license_name = data["license"]
        if not isinstance(license_name, str) or license_name not in LICENSES:
            issues.append(_issue("LICENSE_UNVERIFIED", "REVIEW"))
        expected = set(data["files"])
        for path in sorted(expected - set(actual)):
            issues.append(_issue("EXPECTED_FILE_MISSING", "BLOCK", path))
        for path in sorted(set(actual) - expected):
            issues.append(_issue("UNDECLARED_FILE", "BLOCK", path))
    for rel, path in sorted(actual.items()):
        try:
            size = path.stat().st_size
            total += size
            if size > MAX_FILE_BYTES:
                issues.append(_issue("OVERSIZED_FILE", "BLOCK", rel))
                continue
            if total > MAX_TOTAL_BYTES:
                issues.append(_issue("PACKAGE_TOO_LARGE", "BLOCK"))
                break
            body = path.read_bytes()
            if data is not None and rel in data["files"]:
                if hashlib.sha256(body).hexdigest() != data["files"][rel]:
                    issues.append(_issue("CHECKSUM_MISMATCH", "BLOCK", rel))
            if b"\x00" in body:
                issues.append(_issue("BINARY_CONTENT", "REVIEW", rel))
                continue
            try:
                text = body.decode("utf-8")
            except UnicodeDecodeError:
                issues.append(_issue("NON_UTF8_CONTENT", "REVIEW", rel))
                continue
            parts = PurePosixPath(rel).parts
            if (path.suffix.lower() in SCRIPT_SUFFIXES
                    or any(part in {"scripts", "hooks", ".github", ".husky", "bin"}
                           for part in parts)
                    or path.name in {"package.json", "pyproject.toml", "Makefile", "Dockerfile"}):
                issues.append(_issue("EXECUTABLE_OR_HOOK", "REVIEW", rel))
            if any(pattern.search(text) for pattern in SUSPICIOUS):
                issues.append(_issue("SUSPICIOUS_INSTRUCTIONS", "REVIEW", rel))
            if rel == "SKILL.md":
                if any(pattern.search(text) for pattern in EXECUTION_REFERENCES):
                    issues.append(_issue("EXECUTION_OR_DOWNLOAD_REFERENCE", "REVIEW", rel))
                for target in sorted(set(LOCAL_REFERENCES.findall(text))):
                    if not _safe_name(target):
                        issues.append(_issue("UNSAFE_SKILL_REFERENCE", "BLOCK", rel))
                    elif target not in actual:
                        issues.append(_issue("REFERENCED_FILE_NOT_INCLUDED", "REVIEW", target))
                normalized_text = text.replace("\r\n", "\n")
                # An opening "---" is not sufficient: require a closing delimiter.
                frontmatter = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)",
                                       normalized_text, flags=re.S)
                if frontmatter is None:
                    issues.append(_issue("SKILL_FRONTMATTER_MISSING", "REVIEW", rel))
                elif data is not None:
                    name = re.search(r"^name:\s*([a-z0-9-]+)\s*$",
                                     frontmatter.group(1), flags=re.M)
                    if name is None:
                        issues.append(_issue("SKILL_NAME_MISSING", "REVIEW", rel))
                    elif name.group(1) != data["candidate_id"]:
                        issues.append(_issue("SKILL_NAME_MISMATCH", "BLOCK", rel))
        except OSError:
            issues.append(_issue("UNREADABLE_FILE", "BLOCK", rel))
    severity = {item["severity"] for item in issues}
    decision = ("REJECT" if "BLOCK" in severity else
                "NEEDS_MANUAL_REVIEW" if "REVIEW" in severity else "ALLOW_FOR_REVIEW")
    return {
        "schema_version": 1,
        "decision": decision,
        "issues": issues,
        "file_count": len(actual),
        "external_fetch": "NOT_RUN",
        "execution": "NOT_RUN",
        "installation": "NOT_AUTHORIZED",
        "provenance_verified": False,
        "adoption_dossier": _dossier(data, declared, issues),
        "status": "OFFLINE_STATIC_ADVISORY_ONLY",
    }



# #432: optional, bounded host-configuration rule surface alongside the existing
# candidate-skill gate. It reads only explicit paths, never runs hooks/MCP/tools.
HOST_FILES = (
    ".codex/config.toml", ".codex/hooks.json",
    ".claude/settings.json", ".claude/settings.local.json", ".mcp.json",
)
HOST_MAX_BYTES = 131_072
HOST_TOTAL_BYTES = 524_288
HOOK_COMMAND_KEYS = frozenset(("command",))
HOST_SEVERITY = {"HIGH": "error", "MEDIUM": "warning"}
HOST_NET = re.compile(r"\b(?:curl|wget|Invoke-WebRequest|Invoke-RestMethod|iwr|irm)\b[^\n]{0,250}https?://", re.I)
HOST_PIPE = re.compile(r"\|\s*(?:sh|bash|pwsh|powershell)\b", re.I)
HOST_INTERPOLATION = re.compile(r"\$\{(?:file|command|content|input|args?)\}", re.I)
HOST_DESTRUCTIVE = re.compile(r"\brm\s+-rf\b|\bRemove-Item\b[^\n]{0,120}-Recurse\b", re.I)
HOST_SENSITIVE = re.compile(r"(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD|PRIVATE[_-]?KEY|CREDENTIAL)", re.I)
HOST_ENV_REFERENCE = re.compile(r"\$\{?[A-Za-z_][A-Za-z0-9_]*\}?\Z")
# Review explicit MCP argv references to known collectors or sensitive roots.
# These are *signals*, not execution blocks or proof of exfiltration.
HOST_COLLECTION_ARG = re.compile(
    r"https?://(?:[A-Za-z0-9-]+\.)*(?:webhook\.site|ngrok\.(?:io|app)|requestbin\.com|"
    r"requestcatcher\.com|pipedream\.net|interactsh\.com)(?:[/:?#]|$)", re.I)
HOST_SENSITIVE_ARG = re.compile(
    r"(?:^|[/\\])\.(?:ssh|aws|gnupg|kube)(?:[/\\]|$)|"
    r"^/(?:etc|var/log)(?:/|$)|"
    r"^C:[/\\]Users[/\\][^/\\]+[/\\]\.(?:ssh|aws|kube)(?:[/\\]|$)", re.I)
HOST_INTERPRETER_GRANT = re.compile(
    r"^Bash\((?:[^\s()]*[/\\])?"
    r"(?:bash|sh|zsh|pwsh|powershell|cmd)(?:\.exe)?(?:\s|:\*|\))", re.I)
HOST_MCP_SHELL = re.compile(
    r"(?:^|[/\\])(?:bash|sh|zsh|pwsh|powershell|cmd)(?:\.exe)?$", re.I)


def _host_finding(items: list[dict], rule: str, path: str, severity: str = "HIGH") -> None:
    # Never include untrusted contents, filenames chosen by a model, or secret values.
    item = {"rule": rule, "path": path, "severity": severity}
    if item not in items:
        items.append(item)


def _unique_json_pairs(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("ambiguous duplicate JSON key")
        result[key] = value
    return result


def _reject_json_constant(_: str) -> None:
    raise ValueError("non-finite JSON value")


def _host_hook_commands(data: object, *, depth: int = 0) -> list[str]:
    if depth > 16:
        raise ValueError("overdeep hook")
    if isinstance(data, dict):
        found = []
        for key, val in data.items():
            if key in HOOK_COMMAND_KEYS:
                if not isinstance(val, str):
                    raise ValueError("hook command is not text")
                found.append(val)
            elif isinstance(val, (dict, list)):
                found.extend(_host_hook_commands(val, depth=depth + 1))
        return found
    if isinstance(data, list):
        if len(data) > 128:
            raise ValueError("too many hook entries")
        found = []
        for item in data:
            found.extend(_host_hook_commands(item, depth=depth + 1))
        return found
    raise ValueError("invalid hook structure")


def _host_check_hooks(config: dict, path: str, items: list[dict]) -> None:
    if "hooks" not in config:
        return
    for command in _host_hook_commands(config["hooks"]):
        for pattern, rule in (
            (HOST_NET, "HOOK_NETWORK_EGRESS"),
            (HOST_PIPE, "HOOK_SHELL_PIPE"),
            (HOST_INTERPOLATION, "HOOK_UNTRUSTED_INTERPOLATION"),
            (HOST_DESTRUCTIVE, "HOOK_DESTRUCTIVE_COMMAND"),
        ):
            if pattern.search(command):
                _host_finding(items, rule, path)


def _host_check_mcp(config: dict, path: str, items: list[dict], *, toml: bool) -> None:
    servers = config.get("mcp_servers" if toml else "mcpServers")
    if servers is None:
        return
    if not isinstance(servers, dict):
        raise ValueError("malformed MCP server map")
    if len(servers) > 64:
        raise ValueError("too many MCP servers")
    for server in servers.values():
        if not isinstance(server, dict):
            raise ValueError("invalid MCP server")
        environment = server.get("env", {})
        if not isinstance(environment, dict):
            raise ValueError("invalid MCP environment")
        for key, value in environment.items():
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError("invalid MCP environment entry")
            if HOST_SENSITIVE.search(key) and value and not HOST_ENV_REFERENCE.fullmatch(value):
                _host_finding(items, "MCP_INLINE_CREDENTIAL", path)
        transport = server.get("type")
        if transport is not None and transport not in ("stdio", "http", "sse"):
            raise ValueError("invalid MCP transport")
        url = server.get("url")
        if url is not None:
            if not isinstance(url, str) or len(url.encode("utf-8")) > 2048 or re.search(r"\s", url):
                raise ValueError("invalid MCP URL")
            parsed = urlsplit(url)
            if parsed.scheme not in ("http", "https") or not parsed.hostname:
                raise ValueError("invalid MCP URL")
            if parsed.username is not None or parsed.password is not None:
                _host_finding(items, "MCP_INLINE_CREDENTIAL", path)
            if HOST_COLLECTION_ARG.search(url):
                _host_finding(items, "MCP_COLLECTION_ENDPOINT", path, "MEDIUM")
        if (transport in ("http", "sse") and url is None) or (transport == "stdio" and url is not None):
            raise ValueError("inconsistent MCP transport")
        args = server.get("args", [])
        if not isinstance(args, list) or len(args) > 128 or any(not isinstance(v, str) for v in args):
            raise ValueError("invalid MCP argument list")
        if any(HOST_COLLECTION_ARG.search(arg) for arg in args):
            _host_finding(items, "MCP_COLLECTION_ENDPOINT", path, "MEDIUM")
        if any(HOST_SENSITIVE_ARG.search(arg) for arg in args):
            _host_finding(items, "MCP_SENSITIVE_FILESYSTEM_PATH", path, "MEDIUM")
        if len(args) >= 2 and any(
            args[i] in ("--allow-root", "--filesystem-root", "--directory")
            and args[i + 1] in ("/", "C:\\", "C:/")
            for i in range(len(args) - 1)
        ):
            _host_finding(items, "MCP_BROAD_FILESYSTEM_ROOT", path)
        command = server.get("command", "")
        if not isinstance(command, str):
            raise ValueError("invalid MCP command")
        # A review signal: executable-install-on-use may pull mutable code.
        if re.search(r"(^|[/\\])(?:npx|bunx)(?:\.cmd|\.exe)?$", command, re.I) and (
            "-y" in args or "--yes" in args
        ):
            _host_finding(items, "MCP_DYNAMIC_PACKAGE_EXECUTION", path, "MEDIUM")
        # Static review of explicit argv payloads; never run commands or hooks.
        if HOST_MCP_SHELL.search(command):
            for index, flag in enumerate(args):
                option = flag.casefold()
                if option in ("-encodedcommand", "-enc"):
                    _host_finding(items, "MCP_OPAQUE_SHELL_COMMAND", path)
                if option in ("-c", "-lc", "-ec", "-ce", "-command", "/c"):
                    if index + 1 >= len(args):
                        raise ValueError("missing MCP shell payload")
                    payload = args[index + 1]
                    for pattern, rule in (
                        (HOST_NET, "MCP_SHELL_NETWORK_EGRESS"),
                        (HOST_PIPE, "MCP_SHELL_PIPE"),
                        (HOST_INTERPOLATION, "MCP_SHELL_UNTRUSTED_INTERPOLATION"),
                        (HOST_DESTRUCTIVE, "MCP_SHELL_DESTRUCTIVE_COMMAND"),
                    ):
                        if pattern.search(payload):
                            _host_finding(items, rule, path)


def review_host_config(root: Path) -> dict:
    """Bounded local host-config static audit, no network/process/write effects."""
    findings: list[dict] = []
    files: list[dict] = []
    if (not root.is_dir() or root.is_symlink()
            or (hasattr(root, "is_junction") and root.is_junction())):
        _host_finding(findings, "INVALID_HOST_ROOT", "<root>")
    else:
        total = 0
        for relative in HOST_FILES:
            target = root / relative
            # Check before existence: dangling directory symlinks cannot be ignored.
            parts = (target, target.parent)
            if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction()) for p in parts):
                _host_finding(findings, "HOST_PATH_NOT_REGULAR", relative)
                continue
            if not target.exists():
                continue
            if not target.is_file():
                _host_finding(findings, "HOST_PATH_NOT_REGULAR", relative)
                continue
            try:
                size = target.stat().st_size
                total += size
                if size > HOST_MAX_BYTES or total > HOST_TOTAL_BYTES:
                    _host_finding(findings, "HOST_CONFIG_TOO_LARGE", relative)
                    continue
                body = target.read_bytes()
                if len(body) > HOST_MAX_BYTES or b"\x00" in body:
                    raise ValueError("invalid config bytes")
                files.append({
                    "path": relative, "sha256": hashlib.sha256(body).hexdigest(),
                    "size_bytes": len(body),
                })
                if relative.endswith(".toml"):
                    try:
                        import tomllib
                    except ImportError as exc:
                        raise ValueError("TOML support unavailable") from exc
                    config = tomllib.loads(body.decode("utf-8"))
                else:
                    config = json.loads(
                        body.decode("utf-8"), object_pairs_hook=_unique_json_pairs,
                        parse_constant=_reject_json_constant,
                    )
                if not isinstance(config, dict):
                    raise ValueError("invalid root config")
                if relative == ".codex/config.toml":
                    if config.get("sandbox_mode") == "danger-full-access":
                        _host_finding(findings, "CODEX_UNRESTRICTED_SANDBOX", relative)
                    if config.get("approval_policy") == "never":
                        _host_finding(findings, "CODEX_APPROVAL_DISABLED", relative)
                    _host_check_mcp(config, relative, findings, toml=True)
                elif relative == ".mcp.json":
                    _host_check_mcp(config, relative, findings, toml=False)
                else:
                    _host_check_hooks(config, relative, findings)
                    if relative.startswith(".claude/"):
                        permissions = config.get("permissions", {})
                        if not isinstance(permissions, dict):
                            raise ValueError("invalid permission object")
                        allowed = permissions.get("allow", [])
                        if (not isinstance(allowed, list) or len(allowed) > 256
                                or any(not isinstance(x, str) or len(x) > 512 for x in allowed)):
                            raise ValueError("invalid permission allow-list")
                        # Bare tool names and (*) grant every operation in Claude Code.
                        grants = [grant.strip() for grant in allowed]
                        for tool, rule in (
                            ("Bash", "HOST_UNRESTRICTED_SHELL"),
                            ("Write", "HOST_UNRESTRICTED_WRITE"),
                            ("Edit", "HOST_UNRESTRICTED_EDIT"),
                        ):
                            if any(re.fullmatch(tool + r"(?:\(\s*\*\s*\))?", grant, re.I)
                                   for grant in grants):
                                _host_finding(findings, rule, relative)
                        if any(HOST_INTERPRETER_GRANT.search(grant) for grant in grants):
                            _host_finding(findings, "HOST_SHELL_INTERPRETER_GRANTED", relative)
                        auto_mcp = config.get("enableAllProjectMcpServers", False)
                        if not isinstance(auto_mcp, bool):
                            raise ValueError("invalid project MCP approval setting")
                        if auto_mcp:
                            _host_finding(findings, "HOST_AUTO_APPROVE_PROJECT_MCP",
                                          relative, "MEDIUM")
            except (OSError, ValueError, UnicodeError, TypeError, RecursionError):
                _host_finding(findings, "HOST_CONFIG_UNPARSEABLE", relative)
    if not files and not findings:
        _host_finding(findings, "NO_SUPPORTED_HOST_CONFIG", "<root>", "MEDIUM")
    decision = ("BLOCKED" if any(x["severity"] == "HIGH" for x in findings) else
                "REVIEW_REQUIRED" if findings else "PASS")
    return {
        "schema_version": 1, "decision": decision, "findings": findings,
        "evidence": {"source": "TOOLKIT_OFFLINE_HOST_CONFIG",
                     "files": files, "contents_included": False,
                     "runtime_enforcement": "NOT_VERIFIED", "client_activation": "NOT_VERIFIED"},
        "execution": "NOT_RUN", "network": "NOT_USED",
        "authorization": "NOT_GRANTED",
    }


def host_report_sarif(report: dict) -> dict:
    """SARIF 2.1.0 redacted projection of native host-config findings."""
    rules = sorted({x["rule"] for x in report["findings"]})
    return {
        "version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {"driver": {"name": "Toolkit Native Host Config Gate",
                                "rules": [{"id": key, "shortDescription": {"text": key}}
                                          for key in rules]}},
            "results": [{
                "ruleId": x["rule"], "level": HOST_SEVERITY[x["severity"]],
                "message": {"text": x["rule"] + " - manual review required"},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {"uri": x["path"].replace("<root>", "host-config")},
                    }
                }],
            } for x in report["findings"]],
        }],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--review-context", type=Path,
                        help="Optional operator dossier JSON outside candidate (not provenance)")
    parser.add_argument("--host-config-root", type=Path,
                        help="Opt-in static host config audit, no candidate skill scan")
    parser.add_argument("--format", choices=("json", "sarif"), default="json")
    args = parser.parse_args(argv)
    if args.host_config_root is not None:
        if args.candidate_dir is not None or args.manifest is not None or args.review_context is not None:
            parser.error("Host config audit is exclusive of candidate review")
        report = review_host_config(args.host_config_root)
        payload = host_report_sarif(report) if args.format == "sarif" else report
        print(json.dumps(payload, indent=2, sort_keys=True))
        return {"PASS": 0, "REVIEW_REQUIRED": 1, "BLOCKED": 2}[report["decision"]]
    if args.candidate_dir is None or args.manifest is None or args.format != "json":
        parser.error("Candidate scan requires --candidate-dir --manifest and JSON output")
    result = review(args.candidate_dir, args.manifest, args.review_context)
    print(json.dumps(result, indent=2, sort_keys=True))
    return {"ALLOW_FOR_REVIEW": 0, "NEEDS_MANUAL_REVIEW": 1, "REJECT": 2}[result["decision"]]


if __name__ == "__main__":
    sys.exit(main())
