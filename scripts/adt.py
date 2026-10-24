#!/usr/bin/env python3
"""Beginner entrypoint for Skill Manager v2. No second installer or network access."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path

import recommend_profile
import skill_manager
from install import ROOT, _ensure_no_symlink_chain

LAYOUTS = ("codex", "claude")
MIN_PYTHON = (3, 12)
GUIDANCE = {
    "missing": "Create the project folder yourself, then repeat this command. No folder was created.",
    "linked": "Use a real project folder without symlinks or Windows junctions in managed paths.",
    "state": "Do not delete or replace the lockfile. Inspect .adt and use Skill Manager recovery guidance.",
    "pending": "Preview: python scripts/skill_manager.py recover --target TARGET; then explicitly --apply after review.",
    "drift": "Review local edits. Skill Manager will refuse unsafe changes; do not delete its ownership records.",
    "conflict": "Review the existing user-owned skill. It will never be adopted or overwritten.",
}


def manifest_data(root: Path = ROOT) -> dict:
    return json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))


def choose(target: Path, manifest: dict, profile: str | None, task: str | None) -> dict:
    if profile:
        if profile not in manifest["profiles"]:
            raise ValueError(f"Unknown profile '{profile}'. Run: python scripts/adt.py profile list")
        selected = {"profile": profile, "reason": "Explicitly selected profile",
                    "detected": {}, "warnings": [], "alternatives": [],
                    "confidence": "explicit", "optional_skills": [], "optional_profiles": []}
    elif task:
        selected = recommend_profile.recommend(target, task, manifest)
    else:
        selected = {"profile": "general", "reason": "Minimal general starting point",
                    "detected": {}, "warnings": [], "alternatives": [],
                    "confidence": "default", "optional_skills": [], "optional_profiles": []}
    selected = dict(selected)
    selected["skills"] = list(manifest["profiles"][selected["profile"]])
    if selected["profile"] == "qa-all":
        selected["warnings"] = [*selected["warnings"],
            "qa-all includes 27 heterogeneous QA skills, some only conditionally useful "
            "(for example graphify-adapter). Prefer a focused QA profile unless you "
            "need broad coverage. File count is not a token-usage measurement."]
        selected["alternatives"] = sorted(set(selected["alternatives"]) | {"qa-core"})
    if selected["profile"] in ("qa-python", "qa-fullstack") and not task:
        selected["warnings"] = [*selected["warnings"],
            "The availability of pytest is NOT_VERIFIED; Python project files are not proof."]
    if selected["profile"] in ("qa-ui", "qa-fullstack") and not task:
        selected["warnings"] = [*selected["warnings"],
            "The availability of Playwright is NOT_VERIFIED; configuration is not proof."]
    return selected


def diagnose(target: Path, layout: str, selected: dict | None = None) -> dict:
    """Read only manager state and immediate skill directories; never scan project sources."""
    target = target.expanduser().absolute()
    report = {"action": "doctor", "target": str(target), "layout": layout,
              "client_activation": "NOT_VERIFIED", "checks": {},
              "diagnostics": {"schema_version": 1, "adapter": "LOCAL_CLI",
                  "adapter_version": "UNVERSIONED_SCRIPT",
                  "toolkit_version": manifest_data().get("version", "NOT_VERIFIED"),
                  "source_sha": "NOT_VERIFIED", "source_worktree": "NOT_CHECKED",
                  "loaded_skills": [], "loaded_skill_evidence": "NO_GUIDANCE_RETURNED_BY_THIS_CALL",
                  "fallback": "NONE", "l4_client_discovery": "NOT_VERIFIED",
                  "l5_client_invocation": "NOT_VERIFIED", "l6_client_benefit": "NOT_MEASURED",
                  "client_activation": "NOT_VERIFIED", "target_execution": "NOT_RUN",
                  "project_files_changed": False},
              "warnings": [], "errors": [], "managed": [],
              "unmanaged": [], "conflicts": [], "result": "OK"}
    checks, errors, warnings = report["checks"], report["errors"], report["warnings"]
    checks["python"] = "OK" if sys.version_info >= MIN_PYTHON else "FAIL"
    if checks["python"] == "FAIL":
        errors.append("Python 3.12 or newer is required.")
    checks["project"] = "OK" if target.is_dir() else "FAIL"
    if checks["project"] == "FAIL":
        errors.append(GUIDANCE["missing"])
        report["result"] = "BLOCKED"
        return report
    try:
        for path in (target, target / ".adt", target / ".adt" / "history",
                     skill_manager.skill_root(target, layout)):
            _ensure_no_symlink_chain(path)
    except ValueError:
        checks["critical_paths"] = "FAIL"
        errors.append(GUIDANCE["linked"])
        report["result"] = "BLOCKED"
        return report
    checks["critical_paths"] = "OK"
    # os.access is only a heuristic (not an actual write attempt).
    checks["write_access"] = "NOT_VERIFIED" if os.access(target, os.W_OK) else "UNKNOWN"
    warnings.append("Write permission has not been verified: doctor never creates files.")
    warnings.append("The chosen layout is a folder convention, not proof that an AI client is installed.")
    try:
        state = skill_manager.read_state(target, layout)
        checks["lockfile"] = "OK" if state["skills"] else "NOT_INSTALLED"
        pending = skill_manager.pending_transactions(target)
        orphans = skill_manager.orphan_staging(target)
        if pending or orphans:
            checks["transactions"] = "FAIL"
            errors.append("Interrupted transaction detected. " +
                          GUIDANCE["pending"].replace("TARGET", shlex.quote(str(target))))
        else:
            checks["transactions"] = "OK"
        root = skill_manager.skill_root(target, layout)
        for name in sorted(state["skills"]):
            try:
                actual = skill_manager.tree_digest(root / name)
                if actual != state["skills"][name]["digest"]:
                    raise skill_manager.ManagerError("modified")
            except (OSError, ValueError):
                errors.append(f"Managed skill '{name}' is modified, missing or unsafe. " +
                              GUIDANCE["drift"])
        report["managed"] = sorted(state["skills"])
        if root.exists():
            for child in root.iterdir():
                if child.is_symlink() or child.is_junction():
                    errors.append("Linked skill entry detected; inspect the managed skills folder.")
                    continue
                if child.is_dir() and child.name not in state["skills"]:
                    report["unmanaged"].append(child.name)
        if report["unmanaged"]:
            warnings.append(f"{len(report['unmanaged'])} user-owned skill folder(s) found; "
                            "they are not managed by Toolkit.")
        if selected is not None:
            report["conflicts"] = sorted(set(selected["skills"]) & set(report["unmanaged"]))
            if report["conflicts"]:
                errors.append("Selected skills conflict with user-owned folders: " +
                              ", ".join(report["conflicts"]) + ". " + GUIDANCE["conflict"])
        checks["managed_drift"] = "FAIL" if any("Managed skill" in x for x in errors) else "OK"
        checks["selected_profile"] = selected["profile"] if selected else "NOT_CHECKED"
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError):
        checks["manager_state"] = "FAIL"
        errors.append("Manager ownership or transaction state cannot be verified. " + GUIDANCE["state"])
    if errors:
        report["result"] = "BLOCKED"
    elif report["unmanaged"]:
        report["result"] = "REVIEW_REQUIRED"
    return report


def preview(target: Path, layout: str, selected: dict, *, apply: bool) -> dict:
    report = diagnose(target, layout, selected)
    result = {"action": "init" if apply else "plan", "target": str(target.absolute()),
              "layout": layout, "selection": selected, "doctor": report,
              "changes": [], "file_diffs": {}, "already_managed": [],
              "applied": False}
    if report["result"] == "BLOCKED":
        result["result"] = "BLOCKED"
        return result
    installed = set(report["managed"])
    names = [name for name in selected["skills"] if name not in installed]
    result["already_managed"] = sorted(installed & set(selected["skills"]))
    if not names:
        result["result"] = "ALREADY_INSTALLED"
        return result
    # Both preview and mutation are delegated to the existing owner-aware manager.
    plan = skill_manager.operate("install", target, names=names, layout=layout, apply=False)
    result["changes"], result["file_diffs"] = plan["changes"], plan["file_diffs"]
    result["result"] = "REVIEW_REQUIRED" if report["result"] == "REVIEW_REQUIRED" else "PREVIEW"
    if apply:
        done = skill_manager.operate("install", target, names=names, layout=layout, apply=True)
        result["applied"] = done["applied"]
        result["result"] = "APPLIED" if done["applied"] else "ALREADY_INSTALLED"
        result["verification"] = skill_manager.operate("status", target, layout=layout)
    return result


def format_report(data: dict, json_mode: bool) -> None:
    if json_mode:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return
    if data["action"] == "profile list":
        print("Profiles from MANIFEST.json (nothing will be installed):")
        for name, skills in data["profiles"].items():
            print(f"  {name}: {len(skills)} skill(s)")
        print("Use: python scripts/adt.py profile plan --target PROJECT --profile general")
        return
    print(f"Result: {data.get('result', 'OK')}")
    if "target" in data:
        print(f"Project: {data['target']}\nClient layout: {data['layout']}")
    if data["action"] == "doctor":
        for key, value in data["checks"].items():
            print(f"  {key}: {value}")
        print(f"Managed: {len(data['managed'])}; user-owned: {len(data['unmanaged'])}")
        for message in data["errors"] + data["warnings"]:
            print(f"  - {message}")
        return
    if data["action"] == "status":
        for name, value in data["skills"].items():
            print(f"  {name}: {value['status']}")
        return
    sel = data["selection"]
    print(f"Profile: {sel['profile']} ({sel['confidence']})\nReason: {sel['reason']}")
    print("Detected:", json.dumps(sel["detected"], ensure_ascii=False))
    for message in sel["warnings"] + data["doctor"]["errors"] + data["doctor"]["warnings"]:
        print(f"  - {message}")
    print("Already managed:", ", ".join(data["already_managed"]) or "none")
    print("New skills:", ", ".join(data["changes"]) or "none")
    for name, diffs in data["file_diffs"].items():
        for diff in diffs:
            print(f"  {name}/{diff['path']}: {diff['change']}")
    if data["result"] in ("PREVIEW", "REVIEW_REQUIRED"):
        print("Nothing changed. Review the plan, then repeat init with --apply.")
    if data["result"] == "APPLIED":
        print("Managed installation completed. Verify with: python scripts/adt.py status --target PROJECT")


def run(args: argparse.Namespace, root: Path = ROOT) -> dict:
    manifest = manifest_data(root)
    if args.command == "profile" and args.profile_command == "list":
        return {"action": "profile list", "profiles": dict(sorted(manifest["profiles"].items()))}
    target = args.target.expanduser().absolute()
    # Route missing projects through the same structured BLOCKED diagnostic, even
    # when a task-based profile would otherwise fail during selection.
    if args.command in ("doctor", "init", "profile") and not target.is_dir():
        return diagnose(target, args.layout)
    if args.command == "doctor":
        selection = choose(target, manifest, args.profile, args.task) if (args.profile or args.task) else None
        return diagnose(target, args.layout, selection)
    if args.command == "status":
        output = skill_manager.operate("status", target, layout=args.layout)
        return {"result": "OK", **output}
    selection = choose(target, manifest, args.profile, args.task)
    if args.command == "init" or (args.command == "profile" and args.profile_command == "plan"):
        if args.command == "profile" and args.profile_command == "plan":
            return preview(target, args.layout, selection, apply=False)
        return preview(target, args.layout, selection, apply=args.apply)
    raise ValueError("Unknown command")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Machine-readable result")
    sub = parser.add_subparsers(dest="command", required=True)
    def target_flags(command, *, selection=False):
        command.add_argument("--target", required=True, type=Path, help="Existing project folder")
        command.add_argument("--layout", choices=LAYOUTS, default="codex")
        if selection:
            group = command.add_mutually_exclusive_group()
            group.add_argument("--profile")
            group.add_argument("--task", choices=recommend_profile.TASKS)
    init = sub.add_parser("init", help="Preview installation; --apply is required to write")
    target_flags(init, selection=True)
    init.add_argument("--apply", action="store_true", help="Apply reviewed installation")
    doctor = sub.add_parser("doctor", help="Read-only environment and manager diagnostic")
    target_flags(doctor, selection=True)
    target_flags(sub.add_parser("status", help="Show managed skills without changing them"))
    profiles = sub.add_parser("profile", help="Choose and preview curated skill profiles")
    profile_sub = profiles.add_subparsers(dest="profile_command", required=True)
    profile_sub.add_parser("list", help="List profiles from MANIFEST.json")
    target_flags(profile_sub.add_parser("plan", help="Read-only installation preview"), selection=True)
    try:
        args = parser.parse_args(argv)
        result = run(args)
        format_report(result, args.json)
        return 2 if result.get("result") == "BLOCKED" else 0
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as exc:
        print(f"ERROR: {exc}\nNext step: run 'python scripts/adt.py --help' or 'doctor --target PROJECT'.",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
