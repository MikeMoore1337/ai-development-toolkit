#!/usr/bin/env python3
"""Convert human-reviewed agent observations to strictly paired Skill Evals inputs.

This never fills in missing human verdicts, safety counts or token usage. A
passing hidden oracle alone is not an independent acceptance verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from skill_eval import EvalInputError, evaluate


def build_reports(observations: dict, reviews: dict, root: Path) -> dict[str, dict]:
    if observations.get("schema_version") != 1 or not observations.get("executed"):
        raise EvalInputError("Real executed observations are required")
    if not isinstance(reviews.get("reviewer"), str) or not reviews["reviewer"].strip():
        raise EvalInputError("An identified independent reviewer is required")
    if reviews.get("independent_review_attested") is not True:
        raise EvalInputError("Review independence must be explicitly attested")
    records = observations.get("records")
    decisions = reviews.get("decisions")
    if not isinstance(records, list) or not records or not isinstance(decisions, list):
        raise EvalInputError("Both observations and review decisions are required")
    ids: set[tuple] = set()
    catalog = {}
    for item in records:
        key = (item["case_id"], item["trial"], item["variant"])
        if key in catalog:
            raise EvalInputError(f"Duplicate run {key}")
        catalog[key] = item
    for item in decisions:
        if not isinstance(item, dict):
            raise EvalInputError("Each review must be an object")
        key = (item.get("case_id"), item.get("trial"), item.get("variant"))
        if key in ids or key not in catalog:
            raise EvalInputError(f"Duplicate or unknown review {key}")
        ids.add(key)
        if type(item.get("accepted")) is not bool:
            raise EvalInputError(f"Missing human acceptance verdict: {key}")
        if (not isinstance(item.get("notes"), str) or
                len(item["notes"].strip()) < 12):
            raise EvalInputError(f"Substantive reviewer notes required: {key}")
        if type(item.get("skill_activation_observed")) is not bool:
            raise EvalInputError(f"Skill activation must be reviewed: {key}")
        for metric in ("regressions", "unsafe_actions"):
            value = item.get(metric)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise EvalInputError(f"Explicit non-negative {metric} required: {key}")
        trial = catalog[key]
        hashes = trial.get("evidence_sha256")
        if (not isinstance(hashes, dict) or
                set(hashes) != set(trial.get("evidence", []))):
            raise EvalInputError(f"Missing or incomplete evidence digests: {key}")
        for relative, expected in hashes.items():
            path = root / relative
            if (not isinstance(relative, str) or
                    not isinstance(expected, str) or len(expected) != 64 or
                    Path(relative).is_absolute() or ".." in Path(relative).parts or
                    not path.resolve().is_relative_to(root.resolve()) or
                    not path.is_file() or path.is_symlink()):
                raise EvalInputError(f"Invalid evidence digest or unsafe path: {key}")
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise EvalInputError(f"Evidence altered since the agent run: {key}")
        if item["accepted"] and (trial["cli"]["returncode"] != 0
                                 or trial["cli"]["timed_out"]
                                 or trial["oracle"]["returncode"] != 0
                                 or trial["oracle"]["timed_out"]):
            raise EvalInputError(f"Cannot accept failed/unverified code execution: {key}")
        if key[2] == "baseline" and item["skill_activation_observed"]:
            raise EvalInputError(f"Baseline should not invoke installed candidate skill: {key}")
    if ids != set(catalog):
        raise EvalInputError(f"Missing reviewer verdicts: {sorted(set(catalog) - ids)}")
    by_case: dict[str, list[dict]] = {}
    for item in decisions:
        key = (item["case_id"], item["trial"], item["variant"])
        observation = catalog[key]
        by_case.setdefault(item["case_id"], []).append({
            "task_id": item["case_id"], "trial": item["trial"],
            "variant": item["variant"], "accepted": item["accepted"],
            "regressions": item["regressions"],
            "unsafe_actions": item["unsafe_actions"],
            "tokens": None,  # Never infer from unstructured CLI output.
            "duration_seconds": observation["cli"]["duration_seconds"],
            "evidence": observation["evidence"],
        })
    results = {}
    for case_id, runs in by_case.items():
        pins = {r["fixture_commit_sha"] for r in records if r["case_id"] == case_id}
        if len(pins) != 1:
            raise EvalInputError(f"Baseline and candidate have differing fixture commits: {case_id}")
        report = {
            "schema_version": 1,
            "dataset": observations["dataset"] + "/" + case_id + "/" + observations["provider"],
            "model": observations["model"],
            "repository_sha": pins.pop(),
            "runs": runs,
        }
        summary = evaluate(report, root)
        summary["reviewer_attested"] = reviews["reviewer"]
        summary["skill_activation_observed"] = {
            "candidate_trials": sum(
                x["skill_activation_observed"] for x in decisions
                if x["case_id"] == case_id and x["variant"] == "candidate"
            ),
            "candidate_total": sum(x["case_id"] == case_id and x["variant"] == "candidate"
                                   for x in decisions),
        }
        summary["independent_review_required"] = True
        summary["note"] = ("Reviewer attestation is self-reported; evidence content is not "
                           "independently authenticated by this script. Exploratory only.")
        results[case_id] = {"scorer_input": report, "summary": summary}
    return results


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--observations", type=Path, required=True)
    p.add_argument("--reviews", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        print("ERROR: Refusing to overwrite existing reviewed report directory", file=sys.stderr)
        return 2
    try:
        observations = json.loads(args.observations.read_text(encoding="utf-8"))
        reviews = json.loads(args.reviews.read_text(encoding="utf-8"))
        reports = build_reports(observations, reviews, args.observations.resolve().parent)
        args.output.mkdir(parents=True)
        for case_id, data in reports.items():
            for key, filename in (("scorer_input", "scored-runs.json"),
                                  ("summary", "summary.json")):
                target = args.output / case_id
                target.mkdir(exist_ok=True)
                (target / filename).write_text(
                    json.dumps(data[key], ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
        print(json.dumps({"cases_reviewed": sorted(reports),
                          "classification": "exploratory"}, indent=2))
        return 0
    except (OSError, KeyError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
