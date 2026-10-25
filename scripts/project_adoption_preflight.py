#!/usr/bin/env python3
"""Read-only project adoption preflight; delegates to existing ADT doctor/router.

This is NOT an installer, a model client, or project-policy discovery.
The exact project's AGENTS.md and authorization requirements always win.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import adt
import recommend_profile

ARCHETYPES = ("generic", "web-app", "agent-service", "private-data")
CLIENT_LAYOUTS = ("codex", "claude")
MARKERS = (
    "AGENTS.md", "CLAUDE.md", "README.md", "pyproject.toml", "package.json",
    "pytest.ini", "playwright.config.ts", ".github/workflows", ".agents/skills",
    ".claude/skills", ".hermes/skills", ".git",
)
# These are reminders to inspect policy, never inferred facts about a project.
REVIEW_CHECKLISTS = {
    "generic": ("Read actual AGENTS.md/README and obtain change permission.",),
    "web-app": ("Check the project's real visual approval and release policy.",
                "Verify data-protection requirements before implementation."),
    "agent-service": ("Verify permissions, secrets and runtime boundaries.",
                      "Remote tool access does not grant deployment permission."),
    "private-data": ("Keep private records and exports out of Toolkit outputs.",
                     "Require explicit review and consent before writes or publishing."),
}


class AdoptionError(ValueError):
    pass


def marker_inventory(target: Path) -> dict[str, str]:
    result = {}
    for name in MARKERS:
        path = target / name
        if path.is_symlink() or path.is_junction():
            result[name] = "UNSAFE_LINK"
        elif path.is_file() or path.is_dir():
            result[name] = "PRESENT_UNREAD"
        else:
            result[name] = "ABSENT"
    return result


def inspect(target: Path, layout: str, task: str, archetype: str,
            *, manifest: dict | None = None) -> dict:
    if layout not in CLIENT_LAYOUTS or archetype not in ARCHETYPES:
        raise AdoptionError("Unsupported client layout or project archetype")
    if task not in recommend_profile.TASKS:
        raise AdoptionError("Unsupported task")
    target = target.expanduser().absolute()
    if target.is_symlink() or target.is_junction():
        raise AdoptionError("Linked project root requires a trusted checkout")
    marker = marker_inventory(target) if target.is_dir() else {}
    selected = None
    if target.is_dir() and not any(v == "UNSAFE_LINK" for v in marker.values()):
        selected = adt.choose(target, manifest or adt.manifest_data(), None, task)
    doctor = adt.diagnose(target, layout, selected)
    blocked = (doctor["result"] == "BLOCKED"
               or any(v == "UNSAFE_LINK" for v in marker.values()))
    has_policy = marker.get("AGENTS.md") == "PRESENT_UNREAD"
    if blocked:
        status = "BLOCKED"
    elif doctor["result"] == "REVIEW_REQUIRED":
        status = "REVIEW_REQUIRED"
    else:
        status = "READY_FOR_HUMAN_REVIEW"
    advice = list(REVIEW_CHECKLISTS[archetype])
    if not has_policy:
        advice.append("AGENTS.md not confirmed in project root; locate source-of-truth policy.")
    if doctor["unmanaged"]:
        advice.append("User-owned skills detected: do not overwrite or adopt them.")
    if marker.get("CLAUDE.md") == "PRESENT_UNREAD":
        advice.append("Existing CLAUDE.md is project-owned, never edit automatically.")
    if any(v == "UNSAFE_LINK" for v in marker.values()):
        advice.append("Linked policy/configuration marker: manual inspection required.")
    return {
        "schema_version": 1,
        "classification": "READ_ONLY_PROJECT_ADOPTION_PREFLIGHT",
        "archetype": archetype,
        "archetype_is_user_declared": True,
        "client_layout": layout,
        "target": str(target),
        "task": task,
        "observed_marker_names_only": marker,
        "marker_contents_read": False,
        "source_of_truth_review": "REQUIRED",
        "selected_profile": selected["profile"] if selected else None,
        "proposed_skills": selected["skills"] if selected else [],
        "selection_reason": selected["reason"] if selected else "BLOCKED",
        "selection_warnings": selected["warnings"] if selected else [],
        "doctor_result": doctor["result"],
        "existing_managed": doctor["managed"],
        "user_owned_skills": doctor["unmanaged"],
        "conflicts": doctor["conflicts"],
        "errors": doctor["errors"],
        "warnings": advice + doctor["warnings"],
        "installation": "NOT_REQUESTED",
        "changed_code": False,
        "client_skill_discovery_L4": "NOT_TESTED",
        "client_skill_use_L5": "NOT_TESTED",
        "client_task_benefit_L6": "NOT_TESTED",
        "result": status,
        "next_step": "Review project policy and run existing adt.py profile plan; "
                     "installation requires separate explicit --apply.",
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", type=Path, required=True)
    p.add_argument("--layout", choices=CLIENT_LAYOUTS, default="codex")
    p.add_argument("--task", choices=recommend_profile.TASKS, required=True)
    p.add_argument("--archetype", choices=ARCHETYPES, default="generic")
    args = p.parse_args(argv)
    try:
        report = inspect(args.target, args.layout, args.task, args.archetype)
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
        return 2 if report["result"] == "BLOCKED" else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
