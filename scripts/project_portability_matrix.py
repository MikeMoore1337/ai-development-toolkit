#!/usr/bin/env python3
"""Five neutral, ephemeral project portability scenarios. No real client/API use.

The only mutations create synthetic files in a system temporary directory.
Toolkit adoption inspection and change-impact planning remain read-only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys
from tempfile import TemporaryDirectory

import adt
import project_adoption_preflight as adoption
import qa_change_impact as impact
import ux_ui_evals

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures" / "project_portability_20261024.json"
IDS = ("python-backend", "frontend-ui", "fullstack", "agent-service", "docs-heavy")
FIELDS = {"id", "markers", "changed_paths", "qa_profile", "expected_checks", "visual_scenario"}
VISUAL_SCENARIOS = {None, "new-site", "substantial-redesign"}
ALLOWED_MARKERS = {
    "AGENTS.md", "README.md", "pyproject.toml", "pytest.ini",
    "package.json", "playwright.config.ts", "docs/architecture/README.md"
}


class PortabilityError(ValueError):
    pass


def load(path: Path = FIXTURE) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {
        "schema_version", "description", "baseline_sha", "author", "cases"
    }:
        raise PortabilityError("Unexpected fixture fields")
    if (type(data["schema_version"]) is not int or data["schema_version"] != 1
            or data["author"] != "AI_ASSISTED_UNREVIEWED_SCENARIOS"
            or not isinstance(data["baseline_sha"], str)
            or len(data["baseline_sha"]) != 40
            or any(c not in "0123456789abcdef" for c in data["baseline_sha"])
            or not isinstance(data["description"], str)):
        raise PortabilityError("Unpinned or unreviewed fixture provenance")
    rows = data["cases"]
    if not isinstance(rows, list) or len(rows) != 5 or [r.get("id") for r in rows
            if isinstance(r, dict)] != list(IDS):
        raise PortabilityError("Exactly five ordered generic projects required")
    for row in rows:
        if set(row) != FIELDS:
            raise PortabilityError("Unexpected project fixture fields")
        markers = row["markers"]
        if (not isinstance(markers, list) or len(markers) < 2
                or len(markers) != len(set(markers))
                or any(not isinstance(s, str) or s not in ALLOWED_MARKERS
                       for s in markers)):
            raise PortabilityError("Unsafe or duplicate project markers")
        if (not isinstance(row["expected_checks"], list)
                or not row["expected_checks"]
                or not set(row["expected_checks"]) <= set(impact.CHECKS)
                or len(set(row["expected_checks"])) != len(row["expected_checks"])):
            raise PortabilityError("Unknown QA check or duplicate")
        if row["qa_profile"] not in {
                "qa-python", "qa-ui", "qa-fullstack", "qa-core"}:
            raise PortabilityError("Unknown QA profile")
        if row["visual_scenario"] not in VISUAL_SCENARIOS:
            raise PortabilityError("Invalid visual scenario")
        impact.validate_paths(row["changed_paths"])
    return data


def inspect(root: Path = ROOT, path: Path = FIXTURE) -> dict:
    fixture = load(path)
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    scenario_catalog = ux_ui_evals.catalog(root)
    results = []
    with TemporaryDirectory(prefix="adt-portability-") as temp:
        base = Path(temp)
        for row in fixture["cases"]:
            project = base / row["id"]
            project.mkdir()
            # Synthetic marker bodies, never read from an actual user's repo.
            for rel in row["markers"]:
                file = project / PurePosixPath(rel)
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text("synthetic marker; no private source\n", encoding="utf-8")
            before = {p.relative_to(project).as_posix(): p.read_bytes()
                      for p in project.rglob("*") if p.is_file()}
            adoption_report = adoption.inspect(
                project, "codex", "qa", "generic", manifest=manifest)
            change = impact.plan(row["changed_paths"])
            after = {p.relative_to(project).as_posix(): p.read_bytes()
                     for p in project.rglob("*") if p.is_file()}
            if before != after:
                raise PortabilityError("Read-only inspection changed synthetic project")
            if (adoption_report["result"] == "BLOCKED"
                    or adoption_report["selected_profile"] != row["qa_profile"]
                    or adoption_report["installation"] != "NOT_REQUESTED"
                    or adoption_report["changed_code"] is not False
                    or adoption_report["marker_contents_read"] is not False):
                raise PortabilityError("Adoption baseline differs: " + row["id"])
            checks = {item["id"] for item in change["recommendations"]}
            if not set(row["expected_checks"]) <= checks:
                raise PortabilityError("QA risk selection lost: " + row["id"])
            if (change["executed_tests"] != 0 or change["gate"] != "INSUFFICIENT_EVIDENCE"
                    or any(c["status"] != "NOT_RUN" for c in change["recommendations"])):
                raise PortabilityError("Unsupported QA execution claim")
            scenario = row["visual_scenario"]
            visual_gate = "NOT_APPLICABLE"
            directions_required = 0
            if scenario is not None:
                spec = scenario_catalog[scenario]
                if (not spec["needs_three"]
                        or spec["expected_gate"] != "HUMAN_VISUAL_REVIEW_REQUIRED"):
                    raise PortabilityError("Visual approval gate missing")
                visual_gate = "HUMAN_VISUAL_REVIEW_REQUIRED"
                directions_required = 3
            if (adoption_report["client_skill_discovery_L4"] != "NOT_TESTED"
                    or adoption_report["client_skill_use_L5"] != "NOT_TESTED"
                    or adoption_report["client_task_benefit_L6"] != "NOT_TESTED"):
                raise PortabilityError("Client results cannot follow from synthetic files")
            results.append({
                "project_class": row["id"],
                "marker_names": row["markers"],
                "changed_paths": row["changed_paths"],
                "adoption_status": adoption_report["result"],
                "selected_qa_profile": adoption_report["selected_profile"],
                "risk_check_ids": sorted(checks),
                "critical_check_ids": change["required_critical_check_ids"],
                "required_expected_checks_present": True,
                "test_execution": "NOT_RUN",
                "visual_scenario": scenario,
                "visual_gate": visual_gate,
                "required_design_directions": directions_required,
                "rendered_visual_assets": "NOT_PRODUCED",
                "human_visual_approval": "NOT_OBSERVED",
                "target_project_changed": False,
                "source_contents_read": False,
            })
    return {
        "classification": "SYNTHETIC_FIVE_PROJECT_PORTABILITY_OFFLINE",
        "fixture_provenance": fixture["author"],
        "baseline_sha": fixture["baseline_sha"],
        "scenario_count": len(results),
        "cases": results,
        "real_client_L4_L5": "NOT_RUN",
        "real_task_quality_L6": "NOT_MEASURED",
        "actual_visual_approval": "NOT_OBSERVED",
        "actual_project_execution": "NOT_RUN",
        "real_project_sources_accessed": False,
        "mutations_to_real_projects": False,
        "limit": "Marker-only synthetic QA routing; no proof of model use, UI quality or deployed code.",
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=ROOT)
    ap.add_argument("--fixtures", type=Path, default=FIXTURE)
    args = ap.parse_args(argv)
    try:
        result = inspect(args.root.resolve(), args.fixtures)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
