#!/usr/bin/env python3
"""Offline client contract and skill-tree checks; never invokes an AI client."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from validate_pack import validate_skill

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "compatibility" / "clients.json"
STATES = frozenset({"VERIFIED", "PARTIAL", "NOT_TESTED", "UNSUPPORTED", "UNKNOWN"})
LAYOUTS = {
    "codex": (".agents/skills",),
    "claude-code": (".claude/skills",),
    "hermes": (".agents/skills", ".hermes/skills"),
}
DOC_HOSTS = {
    "codex": "https://learn.chatgpt.com/docs/build-skills",
    "claude-code": "https://code.claude.com/docs/en/skills",
    "hermes": "https://github.com/NousResearch/hermes-agent/blob/",
}
NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
LINK = re.compile(r"(?<!!)\[[^\]\n]+\]\(([^)]+)\)")
FIELDS = frozenset({
    "client_id", "client_name", "documentation_url", "source_revision", "reviewed_on",
    "supported_skill_layouts", "project_scope", "global_scope", "required_metadata",
    "optional_metadata", "installer_support", "manager_support", "migration_support",
    "static_validation_status", "filesystem_test_status", "source_contract_status",
    "client_discovery_status", "live_activation_status", "effectiveness_status", "notes",
})


class ContractError(ValueError):
    """An invalid contract, path or unsupported operation."""


def _unlinked(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ContractError(f"Linked path is not allowed: {part}")


def load_registry(path: Path = REGISTRY) -> dict:
    """Fail closed for unsupported schema and unsubstantiated compatibility claims."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schema_version", "specification_url", "clients"}:
        raise ContractError("Malformed compatibility registry")
    if data["schema_version"] != 1 or data["specification_url"] != "https://agentskills.io/specification":
        raise ContractError("Unsupported contract schema/specification")
    clients = data["clients"]
    if not isinstance(clients, list) or len(clients) != len(LAYOUTS):
        raise ContractError("Missing or unreviewed clients")
    seen = set()
    for row in clients:
        if not isinstance(row, dict) or set(row) != FIELDS:
            raise ContractError("Invalid client contract fields")
        name = row["client_id"]
        if name not in LAYOUTS or name in seen:
            raise ContractError(f"Unknown or duplicated client: {name}")
        seen.add(name)
        if row["supported_skill_layouts"] != list(LAYOUTS[name]):
            raise ContractError(f"Unreviewed client layout: {name}")
        if not isinstance(row["client_name"], str) or not row["client_name"].strip():
            raise ContractError("Missing client name")
        if not isinstance(row["documentation_url"], str) or not row["documentation_url"].startswith(DOC_HOSTS[name]):
            raise ContractError(f"Untrusted documentation source: {name}")
        if not isinstance(row["reviewed_on"], str) or not re.fullmatch(r"20\d\d-\d\d-\d\d", row["reviewed_on"]):
            raise ContractError("Review date is required")
        revision = row["source_revision"]
        if not isinstance(revision, str) or not revision:
            raise ContractError("Missing source revision")
        if name == "hermes":
            if not re.fullmatch(r"[a-f0-9]{40}", revision) or f"/blob/{revision}/" not in row["documentation_url"]:
                raise ContractError("Hermes source must be pinned to an exact commit")
        elif revision != "official-docs-reviewed-2026-10-19":
            raise ContractError("Unreviewed official documentation version")
        for field in ("project_scope", "global_scope", "notes"):
            if not isinstance(row[field], str) or not row[field].strip():
                raise ContractError(f"Missing {field}: {name}")
        if row["required_metadata"] != ["name", "description"]:
            raise ContractError("Agent Skills fields must remain required")
        optional = row["optional_metadata"]
        if not isinstance(optional, list) or any(not isinstance(x, str) for x in optional) or len(set(optional)) != len(optional):
            raise ContractError("Malformed optional metadata")
        for field in ("installer_support", "manager_support", "migration_support",
                      "static_validation_status", "filesystem_test_status", "source_contract_status",
                      "client_discovery_status", "live_activation_status", "effectiveness_status"):
            if row[field] not in STATES:
                raise ContractError(f"Invalid {field}: {name}")
        if any(row[field] != "NOT_TESTED" for field in ("client_discovery_status", "live_activation_status", "effectiveness_status")):
            raise ContractError("L4-L6 require separate real-client evidence (Issue #11)")
        if name == "hermes" and any(row[field] != "UNSUPPORTED" for field in
                                     ("installer_support", "manager_support", "migration_support")):
            raise ContractError("No Hermes-specific installer/manager/adapter is implemented")
        if name != "hermes" and any(row[field] != "VERIFIED" for field in
                                     ("installer_support", "manager_support", "migration_support")):
            raise ContractError("Existing Codex/Claude Manager v2 contract changed")
    if seen != set(LAYOUTS):
        raise ContractError("Client inventory does not match verified contracts")
    return data


def _check_links(skill: Path, source: Path, content: str) -> list[str]:
    problems = []
    for raw in LINK.findall(content):
        raw = raw.strip().split(" ", 1)[0].strip("<>")
        parsed = urlsplit(raw)
        if parsed.scheme in ("http", "https", "mailto") or raw.startswith("#"):
            continue
        relative = unquote(parsed.path)
        if (not relative or parsed.scheme or parsed.netloc or relative.startswith("/")
                or "\\" in relative or "\x00" in relative or re.match(r"[A-Za-z]:", relative)):
            problems.append(f"Unsafe reference: {source}: {raw}")
            continue
        destination = source.parent / relative
        try:
            _unlinked(destination)
            if not destination.resolve().is_relative_to(skill.resolve()) or not destination.is_file():
                problems.append(f"Missing or escaping reference: {source}: {raw}")
        except (OSError, RuntimeError, ContractError) as exc:
            problems.append(f"Unsafe reference: {source}: {raw}: {exc}")
    return problems


def check_project(project: Path, client_id: str, skill_names: list[str], *, layout: str | None = None) -> dict:
    """Read-only L1/L2 checks of one explicit supported project layout."""
    if client_id not in LAYOUTS:
        raise ContractError(f"Unsupported client: {client_id}")
    permitted = LAYOUTS[client_id]
    selected = layout or permitted[0]
    if selected not in permitted:
        raise ContractError(f"Unsupported layout for {client_id}: {selected}")
    project = project.absolute()
    if not project.is_dir():
        raise ContractError("Project must be an existing directory")
    _unlinked(project)
    skill_root = project / selected
    _unlinked(skill_root)
    if not skill_names or len(skill_names) != len(set(skill_names)) or any(not NAME.fullmatch(n) for n in skill_names):
        raise ContractError("Explicit, unique, safe skill names are required")
    issues = []
    for name in sorted(skill_names):
        skill = skill_root / name
        _unlinked(skill)
        if not skill.is_dir():
            issues.append(f"Missing skill directory: {selected}/{name}")
            continue
        issues.extend(validate_skill(skill))  # Reuse Toolkit's Agent Skills validator.
        for item in sorted(skill.rglob("*")):
            try:
                _unlinked(item)
                if not item.resolve().is_relative_to(skill.resolve()):
                    issues.append(f"Escaping skill file: {item}")
                elif item.is_file() and item.suffix.lower() == ".md":
                    issues.extend(_check_links(skill, item, item.read_text(encoding="utf-8")))
                elif not item.is_file() and not item.is_dir():
                    issues.append(f"Unsupported skill entry: {item}")
            except (OSError, UnicodeError, RuntimeError, ContractError) as exc:
                issues.append(f"Unsafe skill entry: {item}: {exc}")
    return {"status": "FAIL" if issues else "PASS", "client_id": client_id,
            "layout": selected, "skills_checked": len(skill_names),
            "levels": {"L1": "VERIFIED" if not issues else "PARTIAL",
                       "L2": "VERIFIED" if not issues else "PARTIAL",
                       "L3": "NOT_TESTED", "L4": "NOT_TESTED", "L5": "NOT_TESTED", "L6": "NOT_TESTED"},
            "issues": sorted(issues)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--client", choices=sorted(LAYOUTS))
    parser.add_argument("--layout", help="Explicit directory relative to project root")
    parser.add_argument("--skills", help="Comma-separated skill names")
    args = parser.parse_args()
    try:
        data = load_registry(args.registry)
        if args.project is None:
            if args.client or args.layout or args.skills:
                raise ContractError("--project is required for filesystem checks")
            report = {"status": "PASS", "clients": [r["client_id"] for r in data["clients"]],
                      "scope": "registry only; L4-L6 NOT_TESTED"}
        else:
            if not args.client or not args.skills:
                raise ContractError("--client and --skills are required for filesystem checks")
            report = check_project(args.project, args.client,
                                   [s.strip() for s in args.skills.split(",")], layout=args.layout)
    except (OSError, ValueError, TypeError, UnicodeError) as exc:
        report = {"status": "FAIL", "issues": [str(exc)]}
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
