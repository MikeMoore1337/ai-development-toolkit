#!/usr/bin/env python3
"""Read-only three-vs-five actual returned-context audit for Toolkit Personal MCP.

Compare bytes the adapter actually returns, not model tokens, API payload size,
inference quality or native client activation. Inspect source-only controller
collisions and deferred reference behavior without executing a client.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
MCP = ROOT / "integrations" / "personal-mcp" / "adt-personal" / "mcp"
sys.path.insert(0, str(MCP))
sys.path.insert(0, str(ROOT / "scripts"))
import adt_mcp
import profile_metrics

CASES = (
    ("general", "Implement a small config default change, preserve permissions."),
    ("backend", "Implement a REST API endpoint with backwards compatible behavior."),
    ("fullstack", "Implement a frontend and backend field with safe rollback."),
    ("qa-python", "Design pytest tests for Python API validation and negative cases."),
    ("ui-orchestra", "Создай сайт и покажи три разных макета до изменения интерфейса."),
)
MANDATORY_INSTRUCTIONS = (
    "Read target AGENTS.md",
    "Existing project skills and roles take precedence.",
    "Inspect original references with toolkit_get_reference only when task requires them.",
    "Never write Toolkit skills",
    "Do not claim success of tool execution or tests that were not performed.",
)
STATUS = "RETURNED_SOURCE_TEXT_UTF8_BYTES_NOT_MODEL_TOKENS"


class AuditError(ValueError):
    pass


def inspect(root: Path = ROOT) -> dict:
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    tk = adt_mcp.Toolkit(root)
    profiles = profile_metrics.measure(root, manifest)["profiles"]
    examples = []
    for profile, task in CASES:
        # Compare the same task, inventory and model-independent instructions.
        compact = tk.prepare_task(task, profile=profile,
                                  existing_skills=[], existing_roles=[], max_skills=3)
        extended = tk.prepare_task(task, profile=profile,
                                   existing_skills=[], existing_roles=[], max_skills=5)
        c, e = (compact["context_load_metrics"], extended["context_load_metrics"])
        selected_c = [x["name"] for x in compact["loaded_skills"]]
        selected_e = [x["name"] for x in extended["loaded_skills"]]
        if any(item["truncated"] for run in (compact, extended)
               for item in run["loaded_skills"] + run["loaded_roles"]):
            raise AuditError("Cannot claim guardrails for truncated instruction")
        if (c["measurement"] != STATUS or e["measurement"] != STATUS or
                selected_c != selected_e[:len(selected_c)] or
                len(set(selected_e)) != len(selected_e) or
                compact["skills_to_consult"] != extended["skills_to_consult"] or
                compact["selected_skills"] != extended["selected_skills"] or
                compact["remaining_skills_to_consult"] !=
                compact["skills_to_consult"][3:] or
                extended["remaining_skills_to_consult"] !=
                extended["skills_to_consult"][5:]):
            raise AuditError("Context selection changed or duplicated")
        if (compact["role_to_consult"] != extended["role_to_consult"] or
                compact["loaded_roles"] != extended["loaded_roles"] or
                c["reference_files_preloaded"] != 0 or
                e["reference_files_preloaded"] != 0 or
                compact["project_files_changed"] is not False or
                extended["project_files_changed"] is not False or
                compact["installation_performed"] is not False or
                extended["installation_performed"] is not False or
                compact["existing_skills_status"] !=
                "PROVIDED_BY_CLIENT_NOT_VERIFIED"):
            raise AuditError("Scope, deferred reference or inventory guard changed")
        rules_c = " ".join(compact["instructions"])
        rules_e = " ".join(extended["instructions"])
        if rules_c != rules_e or any(missing not in rules_c
                                   for missing in MANDATORY_INSTRUCTIONS):
            raise AuditError("Mandatory instructions missing in compact response")
        if profile == "ui-orchestra" and compact["visual_phase"] != "create-design":
            raise AuditError("Visual approval gate suppressed by explicit profile")
        if c["total_source_bytes"] > e["total_source_bytes"]:
            raise AuditError("Compacting paradoxically increased returned source bytes")
        if e["skill_source_bytes"] != sum(len(item["content"].encode("utf-8"))
                                         for item in extended["loaded_skills"]):
            raise AuditError("Untrue byte measurement")
        examples.append({
            "profile": profile,
            "declared_skill_count": profiles[profile]["skill_count"],
            "source_files_total_bytes": profiles[profile]["installed_file_bytes"],
            "selected_skills": compact["selected_skills"],
            "first_three_loaded": selected_c,
            "first_five_loaded": selected_e,
            "compact_source_bytes": c["total_source_bytes"],
            "extended_source_bytes": e["total_source_bytes"],
            "difference_returned_source_bytes": e["total_source_bytes"] -
                                                 c["total_source_bytes"],
            "deferred_after_three": compact["remaining_skills_to_consult"],
            "deferred_after_five": extended["remaining_skills_to_consult"],
            "references_preloaded": 0,
            "same_role_and_policies": True,
            "visual_phase": compact["visual_phase"],
            "model_tokens_saved": "NOT_MEASURED",
            "quality_effect": "NOT_MEASURED",
        })

    # A client-reported skill is excluded from loading; never duplicate the
    # skill in returned guidance. Missing inventory means UNKNOWN, not empty.
    first = tk.prepare_task(CASES[1][1], profile="backend", max_skills=5,
                            existing_skills=["api-design"], existing_roles=[])
    if any(item["name"] == "api-design" for item in first["loaded_skills"]):
        raise AuditError("Duplicated existing client skill")
    if "api-design" not in first["already_available_skills"]:
        raise AuditError("Client skill inventory ignored")
    unknown = tk.prepare_task(CASES[1][1], profile="backend")
    if unknown["existing_skills_status"] != "NOT_PROVIDED":
        raise AuditError("Unknown inventory conflated with empty list")

    # Cross-profile overlap is visible, not silently removed: the same skill
    # can be required by separate domains, but is de-duplicated within a task.
    names = {name: set(manifest["profiles"][name]) for name, _ in CASES}
    overlap = [
        {"profiles": [a, b], "shared_skills": sorted(names[a] & names[b])}
        for n, a in enumerate(names) for b in list(names)[n + 1:]
        if names[a] & names[b]
    ]
    return {
        "classification": "OFFLINE_PERSONAL_MCP_CONTEXT_COMPARISON",
        "source_version": manifest["version"],
        "adapter_version": adt_mcp.VERSION,
        "baseline": "max_skills=3 (current default from issue 276)",
        "alternative": "max_skills=5 (opt-in; no model or project execution)",
        "measurement": STATUS,
        "examples": examples,
        "profile_overlaps": overlap,
        "same_role_and_safety_instructions": True,
        "missing_inventory": "NOT_PROVIDED",
        "preloaded_references": 0,
        "controller_conflict_group": sorted(adt_mcp.CONFLICT_GROUP),
        "controller_policy": "One controller per routed task; never strip guardrails",
        "model_tokens": "NOT_MEASURED",
        "client_benefit": "NOT_MEASURED",
        "runtime_invocation": "NOT_RUN",
        "project_files_changed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        result = inspect(args.root.resolve())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
