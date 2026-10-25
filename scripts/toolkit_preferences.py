#!/usr/bin/env python3
"""Read-only, deny-by-default user/project/task preference resolver (#394).

This is a policy *preview*, never client discovery, authorization, payment or
agent execution. Project and task documents can tighten but never grant rights
denied by the user's local configuration.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import sys

SCHEMA_VERSION = 1
MAX_BYTES = 64 * 1024
CLIENTS = frozenset({
    "chatgpt", "chatgpt-plugin", "codex-desktop", "codex-cli",
    "claude-web", "claude-code", "mcp", "api",
})
LANGUAGES = frozenset({"auto", "ru", "en"})
APPROVALS = {"deny": 0, "ask": 1}
SECTION_FIELDS = {
    "clients": frozenset({"preferred", "allowed"}),
    "execution": frozenset({
        "real_agent_pilots", "allow_paid_api", "allow_cli_agents",
        "additional_spend_allowed", "allow_network",
    }),
    "skills": frozenset({"selection", "excluded"}),
    "approvals": frozenset({"file_writes", "git_merge", "deployment"}),
}
DEFAULTS = {
    "language": "auto",
    # Eligible guidance routes, NOT a claim that a client is installed/authorized.
    "clients": {"preferred": "auto", "allowed": sorted(CLIENTS)},
    "execution": {
        "real_agent_pilots": False,
        "allow_paid_api": False,
        "allow_cli_agents": False,
        "additional_spend_allowed": False,
        "allow_network": False,
    },
    "skills": {"selection": "auto", "excluded": []},
    "approvals": {"file_writes": "ask", "git_merge": "ask", "deployment": "ask"},
}


class PreferencesError(ValueError):
    """Refuse malformed, ambiguous or escalating policy without side effects."""


def user_config_path() -> Path:
    """Platform-local location; never a source-controlled Toolkit default."""
    if os.name == "nt":
        base = os.environ.get("APPDATA")
        folder = Path(base) if base else Path.home() / "AppData" / "Roaming"
        return folder / "AI Development Toolkit" / "preferences.json"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    folder = Path(xdg) if xdg and Path(xdg).is_absolute() else Path.home() / ".config"
    return folder / "ai-development-toolkit" / "preferences.json"


def _safe_file(path: Path) -> None:
    # Do not call resolve() first: it would follow linked parents.
    for current in (path, *path.parents):
        if current.is_symlink() or (hasattr(current, "is_junction") and current.is_junction()):
            raise PreferencesError("Linked configuration path is not permitted")


def _strings(value: object, options: frozenset[str] | None, field: str) -> list[str]:
    if not isinstance(value, list) or len(value) > 128:
        raise PreferencesError(f"Invalid list: {field}")
    if any(not isinstance(v, str) or not v or len(v) > 80 for v in value):
        raise PreferencesError(f"Invalid list member: {field}")
    if len(value) != len(set(value)) or (options is not None and set(value) - options):
        raise PreferencesError(f"Unsupported or duplicate values: {field}")
    return value


def validate(document: object, scope: str) -> dict:
    """Reject unexpected keys (including credentials), wrong types and versions."""
    if scope not in {"user", "project", "task"}:
        raise PreferencesError("Invalid configuration scope")
    if not isinstance(document, dict):
        raise PreferencesError("Configuration must be an object")
    if type(document.get("schema_version")) is not int or document["schema_version"] != SCHEMA_VERSION:
        raise PreferencesError("Unsupported configuration schema")
    if set(document) - ({"schema_version", "language"} | set(SECTION_FIELDS)):
        raise PreferencesError("Unknown top-level configuration key")
    if "language" in document and (
        not isinstance(document["language"], str) or document["language"] not in LANGUAGES
    ):
        raise PreferencesError("Invalid language")
    for section, allowed_fields in SECTION_FIELDS.items():
        if section not in document:
            continue
        content = document[section]
        if not isinstance(content, dict) or set(content) - allowed_fields:
            raise PreferencesError(f"Invalid {section} configuration")
        for key, value in content.items():
            if section == "clients":
                if key == "preferred":
                    if not isinstance(value, str) or value not in CLIENTS | {"auto"}:
                        raise PreferencesError("Invalid preferred client")
                else:
                    _strings(value, CLIENTS, "clients.allowed")
            elif section == "execution":
                if type(value) is not bool:
                    raise PreferencesError(f"Execution permission must be boolean: {key}")
            elif section == "skills":
                if key == "selection":
                    if value not in ("auto", "manual") or type(value) is not str:
                        raise PreferencesError("Invalid skill selection")
                else:
                    names = _strings(value, None, "skills.excluded")
                    if any(not all(c.islower() or c.isdigit() or c == "-" for c in n)
                           or n.startswith("-") or n.endswith("-") for n in names):
                        raise PreferencesError("Invalid skill identifier")
            elif section == "approvals":
                if type(value) is not str or value not in APPROVALS:
                    raise PreferencesError(f"Invalid approval mode: {key}")
    return document


def read_optional(path: Path, scope: str, *, required: bool = False) -> dict:
    """A missing optional layer is empty; unreadable, linked or invalid is fatal."""
    _safe_file(path)
    if not path.exists():
        if required:
            raise PreferencesError(f"Missing explicit {scope} configuration")
        return {"schema_version": SCHEMA_VERSION}
    if not path.is_file():
        raise PreferencesError(f"Expected regular {scope} configuration")
    try:
        if path.stat().st_size > MAX_BYTES:
            raise PreferencesError("Configuration file exceeds 64KiB")
        data = path.read_bytes().decode("utf-8-sig")
        return validate(json.loads(data), scope)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreferencesError(f"Cannot read valid {scope} configuration") from exc


def resolve(
    user: dict | None = None,
    project: dict | None = None,
    task: dict | None = None,
) -> dict:
    """Strict precedence with monotonic safety for project and task scopes."""
    policy = deepcopy(DEFAULTS)
    origins = {f"{section}.{key}": "defaults"
               for section, content in policy.items() if isinstance(content, dict)
               for key in content}
    origins["language"] = "defaults"
    for scope, raw in (("user", user), ("project", project), ("task", task)):
        doc = validate(raw if raw is not None else {"schema_version": 1}, scope)
        if "language" in doc:
            policy["language"] = doc["language"]
            origins["language"] = scope
        for section in SECTION_FIELDS:
            for key, value in doc.get(section, {}).items():
                previous = policy[section][key]
                field = f"{section}.{key}"
                if section == "execution" and scope != "user":
                    if value and not previous:
                        raise PreferencesError(f"{scope} cannot enable {field} denied by earlier policy")
                elif section == "approvals" and scope != "user":
                    if APPROVALS[value] > APPROVALS[previous]:
                        raise PreferencesError(f"{scope} cannot loosen {field}")
                elif section == "clients" and key == "allowed" and scope != "user":
                    if not set(value).issubset(previous):
                        raise PreferencesError(f"{scope} cannot add client routes")
                if section == "skills" and key == "excluded":
                    policy[section][key] = sorted(set(previous) | set(value))
                else:
                    policy[section][key] = deepcopy(value)
                origins[field] = scope
    selected = policy["clients"]["preferred"]
    if selected != "auto" and selected not in policy["clients"]["allowed"]:
        raise PreferencesError("Preferred client is forbidden by effective client policy")
    if policy["execution"]["allow_paid_api"] and not policy["execution"]["additional_spend_allowed"]:
        raise PreferencesError("Paid API cannot be enabled while additional spending is denied")
    return {
        "schema_version": SCHEMA_VERSION,
        "classification": "READ_ONLY_PREFERENCES_PREVIEW",
        "effective": policy,
        "sources": origins,
        "client_capabilities_verified": False,
        "execution_authorized": False,
        "per_task_consent_required": True,
        "model_calls": 0,
        "project_files_changed": False,
    }


def preview(
    target: Path | None = None, *,
    user_path: Path | None = None,
    project_path: Path | None = None,
    task_path: Path | None = None,
) -> dict:
    if target is not None:
        _safe_file(target)
        if not target.is_dir():
            raise PreferencesError("Existing project directory required")
    explicit_project_config = project_path is not None
    if project_path is None and target is not None:
        project_path = target / ".adt" / "config.json"
    user_file = user_path if user_path is not None else user_config_path()
    user = read_optional(user_file, "user", required=user_path is not None)
    project = read_optional(project_path, "project", required=explicit_project_config) if project_path else None
    task = read_optional(task_path, "task", required=True) if task_path else None
    report = resolve(user, project, task)
    report["layers"] = {
        "user": "PRESENT" if user_path is not None or user_file.is_file() else "ABSENT",
        "project": "PRESENT" if project_path and project_path.is_file() else "ABSENT",
        "task": "PRESENT" if task_path else "ABSENT",
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, help="existing project; reads .adt/config.json")
    parser.add_argument("--user-config", type=Path, help="explicit local user JSON; no creation")
    parser.add_argument("--project-config", type=Path, help="explicit project JSON; no creation")
    parser.add_argument("--task-config", type=Path, help="explicit task JSON; no creation")
    args = parser.parse_args(argv)
    try:
        report = preview(args.target, user_path=args.user_config,
                         project_path=args.project_config, task_path=args.task_config)
    except (PreferencesError, OSError, TypeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
