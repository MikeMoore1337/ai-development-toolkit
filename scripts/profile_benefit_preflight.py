#!/usr/bin/env python3
"""Read-only, zero-cost preflight for five profile-vs-baseline experiments.

No models, client CLIs, commands from target projects, network or write calls.
Optional scoring consumes independently collected pair records via skill_eval;
it cannot prove attestation, observation quality or economic benefit.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import agent_eval_fixtures
import profile_metrics
import skill_eval

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "fixtures/profile_benefit_20261024.json"
PROFILES = ("general", "backend", "fullstack", "qa-python", "ui-orchestra")
CASE_IDS = ("general-change", "backend-retry", "fullstack-port",
            "qa-python-parser", "ui-orchestra-mobile")
TOP_FIELDS = frozenset({"schema_version", "description", "source_sha",
                        "owner_policy", "label_provenance", "cases"})
CASE_FIELDS = frozenset({"id", "profile", "scenario", "task", "oracle_type",
                         "acceptance", "risk_checks", "fixture_source"})
ALLOWED_ORACLES = frozenset({"HUMAN_REVIEW_CHECKLIST",
                             "EXISTING_DETERMINISTIC_FIXTURE",
                             "HUMAN_VISUAL_REVIEW_GATE"})


class BenefitError(ValueError):
    pass


def load_cases(root: Path = ROOT, path: Path = CASES) -> tuple[dict, dict]:
    manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != TOP_FIELDS:
        raise BenefitError("Invalid plan keys")
    if (data["schema_version"] != 1 or data["owner_policy"] !=
            "ZERO_SPEND_NO_REAL_AGENT_CLI" or data["label_provenance"] !=
            "AI_AUTHORED_NOT_INDEPENDENTLY_REVIEWED" or
            not isinstance(data["source_sha"], str) or
            len(data["source_sha"]) != 40 or
            any(ch not in "0123456789abcdef" for ch in data["source_sha"])):
        raise BenefitError("Unpinned or unreviewed evaluation plan")
    if not isinstance(data["description"], str) or not data["description"]:
        raise BenefitError("Missing plan description")
    rows = data["cases"]
    if not isinstance(rows, list) or len(rows) != len(PROFILES):
        raise BenefitError("Exactly five profiles required")
    if ([row.get("id") for row in rows if isinstance(row, dict)] !=
            list(CASE_IDS) or [row.get("profile") for row in rows
                              if isinstance(row, dict)] != list(PROFILES)):
        raise BenefitError("Profile/case contract changed")
    for row in rows:
        if set(row) != CASE_FIELDS:
            raise BenefitError("Unexpected fields in evaluation case")
        if row["profile"] not in manifest["profiles"]:
            raise BenefitError("Missing declared profile")
        if row["oracle_type"] not in ALLOWED_ORACLES:
            raise BenefitError("Unsupported oracle")
        for field in ("scenario", "task"):
            if not isinstance(row[field], str) or not 20 <= len(row[field]) <= 1200:
                raise BenefitError("Invalid " + field)
        for field in ("acceptance", "risk_checks"):
            checks = row[field]
            if (not isinstance(checks, list) or len(checks) < 2 or
                    len(checks) > 8 or any(not isinstance(v, str)
                    or not v.strip() or len(v) > 400 for v in checks)):
                raise BenefitError("Missing/invalid oracle criteria")
        source = row["fixture_source"]
        if source is not None and source not in agent_eval_fixtures.FIXTURES:
            raise BenefitError("Unknown pinned synthetic fixture")
        if (row["oracle_type"] == "EXISTING_DETERMINISTIC_FIXTURE" and
                source is None):
            raise BenefitError("Deterministic fixture missing")
    return data, manifest


def preflight(root: Path, plan: dict, manifest: dict) -> dict:
    sizes = profile_metrics.measure(root, manifest)["profiles"]
    return {
        "issue": 298,
        "status": "OFFLINE_PROTOCOL_READY",
        "source_sha": plan["source_sha"],
        "case_author": plan["label_provenance"],
        "client_runs": "NOT_RUN",
        "acceptance_delta": "NOT_MEASURED",
        "task_quality_benefit": "NOT_MEASURED",
        "elapsed_time_benefit": "NOT_MEASURED",
        "model_token_benefit": "NOT_MEASURED",
        "incremental_api_cost": "NOT_MEASURED",
        "independent_review": "NOT_RUN",
        "runner_execution": "PROHIBITED_ZERO_SPEND_ISSUE_11",
        "profiles": [
            {
                "profile": row["profile"],
                "task_id": row["id"],
                "oracle": row["oracle_type"],
                "fixture_source": row["fixture_source"],
                "source_skill_count": sizes[row["profile"]]["skill_count"],
                "candidate_installed_file_bytes": sizes[row["profile"]]["installed_file_bytes"],
                "candidate_skill_md_bytes": sizes[row["profile"]]["skill_md_bytes"],
                "baseline_skill_source_bytes": 0,
                "metric_scope": "source files available, NOT loaded context/model tokens",
                "result": "NOT_RUN",
            }
            for row in plan["cases"]
        ],
    }


def score_recordings(plan: dict, recorded: dict, directory: Path) -> dict:
    """Score owner/imported records with an explicit self-attested human gate.

    This method reads files; the caller must verify the review and zero-charge
    assertions externally. The existing skill_eval checks pair completeness and
    basic evidence file existence, NOT authenticity or test-oracle execution.
    """
    if not isinstance(recorded, dict) or set(recorded) != {
        "schema_version", "dataset", "model", "repository_sha", "runs",
        "trial_protocol"
    }:
        raise BenefitError("Unexpected score record format")
    gate = recorded["trial_protocol"]
    if not isinstance(gate, dict) or set(gate) != {
        "client_version", "tool_permissions", "reviewer",
        "independent_review_attested", "incremental_cost_verified_zero",
        "case_order"
    }:
        raise BenefitError("Missing trial protocol")
    for field in ("client_version", "tool_permissions", "reviewer"):
        if not isinstance(gate[field], str) or not gate[field].strip():
            raise BenefitError("Missing experiment metadata: " + field)
    if (gate["independent_review_attested"] is not True or
            gate["incremental_cost_verified_zero"] is not True):
        raise BenefitError("Unverified independent review or zero charge")
    if recorded["repository_sha"] != plan["source_sha"]:
        raise BenefitError("Recorded source SHA mismatch")
    order = gate["case_order"]
    if not isinstance(order, dict) or set(order) != set(CASE_IDS):
        raise BenefitError("All five cases must have trial order")
    expected = [["baseline", "candidate"], ["candidate", "baseline"]]
    for task in CASE_IDS:
        if order[task] != expected:
            raise BenefitError("Each case requires two counterbalanced trials")
    if not isinstance(recorded["runs"], list) or len(recorded["runs"]) != 20:
        raise BenefitError("Exactly two paired runs per case required")
    keys = {(item.get("task_id"), item.get("trial"), item.get("variant"))
            for item in recorded["runs"] if isinstance(item, dict)}
    expected_keys = {(task, n, variant) for task in CASE_IDS
                     for n in (1, 2) for variant in ("baseline", "candidate")}
    if keys != expected_keys:
        raise BenefitError("Missing or extra profile/trial pairs")
    for record in recorded["runs"]:
        # This field must be documented per trial and cannot be upgraded to
        # native model activation by looking at the source file on disk.
        if record.get("client_skill_use") not in {
                "OBSERVED_WITH_TRACE", "NOT_OBSERVED", "NOT_VERIFIED"}:
            raise BenefitError("Missing observed skill use")
        if (record["variant"] == "baseline" and
                record["client_skill_use"] != "NOT_OBSERVED"):
            raise BenefitError("Baseline cannot claim candidate skill use")
    result = skill_eval.evaluate({k: recorded[k] for k in (
        "schema_version", "dataset", "model", "repository_sha", "runs")}, directory)
    result.update({
        "profile_count": len(PROFILES),
        "independent_review": "SELF_ATTESTED_NOT_INDEPENDENTLY_VERIFIED",
        "zero_cost": "SELF_ATTESTED_NOT_INDEPENDENTLY_VERIFIED",
        "native_client_activation": "TRACE_REVIEW_REQUIRED",
        "classification": "EXPLORATORY_RECORDED_PAIRS_NOT_CERTIFIED",
        "source_only_baseline": False,
    })
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--cases", type=Path, default=CASES)
    parser.add_argument("--score", type=Path, default=None,
                        help="Read human-reviewed, externally obtained recordings. Does NOT run agents")
    args = parser.parse_args(argv)
    try:
        plan, manifest = load_cases(args.root, args.cases)
        if args.score is None:
            report = preflight(args.root, plan, manifest)
        else:
            report = score_recordings(
                plan, json.loads(args.score.read_text(encoding="utf-8")),
                args.score.resolve().parent)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
