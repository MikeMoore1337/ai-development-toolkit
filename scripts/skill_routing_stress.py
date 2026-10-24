#!/usr/bin/env python3
"""Zero-cost diagnostic on a frozen RU/EN stress fixture; NOT model accuracy."""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

import skill_routing_eval as router

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES = ROOT / "fixtures" / "skill_routing_stress_20261024.json"
KINDS = frozenset({"single", "compound", "negative", "ambiguous", "missing_skill"})
CASE_KEYS = frozenset({"id", "kind", "query", "expected_primary",
                       "acceptable_auxiliary", "forbidden", "expect_abstain"})


def load_stress(path: Path, catalog: dict[str, str]) -> dict:
    """Fail closed on unreviewed schema drift and unknown catalog references."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "description", "label_author", "reviewer_independence",
        "scoring", "baseline_sha", "cases"
    }:
        raise router.RoutingInputError("Invalid frozen stress metadata")
    if (payload["schema_version"] != 1 or
            payload["label_author"] != "AI_ASSISTANT" or
            payload["reviewer_independence"] != "NOT_VERIFIED" or
            payload["scoring"] != "DIAGNOSTIC_NON_GATING" or
            not isinstance(payload["description"], str) or
            not isinstance(payload["baseline_sha"], str) or
            len(payload["baseline_sha"]) != 40 or
            not isinstance(payload["cases"], list) or
            not payload["cases"]):
        raise router.RoutingInputError("Invalid stress provenance")
    ids: set[str] = set()
    prompts: set[str] = set()
    for row in payload["cases"]:
        if not isinstance(row, dict) or set(row) != CASE_KEYS:
            raise router.RoutingInputError("Invalid stress case fields")
        ident, kind, query = row["id"], row["kind"], row["query"]
        if (not isinstance(ident, str) or ident in ids or
                not (ident.startswith("s296-ru-") or ident.startswith("s296-en-"))):
            raise router.RoutingInputError("Invalid/duplicate stress id")
        ids.add(ident)
        if kind not in KINDS or not isinstance(query, str) or not query.strip() or len(query) > 1000:
            raise router.RoutingInputError("Invalid stress query/kind")
        if router.prompt_language(query) != ident[5:7]:
            raise router.RoutingInputError("Stress language ID mismatch")
        if query in prompts:
            raise router.RoutingInputError("Duplicate stress query")
        prompts.add(query)
        for key in ("expected_primary", "acceptable_auxiliary", "forbidden"):
            labels = row[key]
            if (not isinstance(labels, list) or len(labels) > 5 or
                    any(not isinstance(x, str) or x not in catalog for x in labels) or
                    len(labels) != len(set(labels))):
                raise router.RoutingInputError("Unknown/duplicate stress skill in " + key)
        positive = row["expected_primary"] + row["acceptable_auxiliary"]
        if set(positive) & set(row["forbidden"]):
            raise router.RoutingInputError("Expected/forbidden label overlap")
        if not isinstance(row["expect_abstain"], bool):
            raise router.RoutingInputError("Invalid stress abstention marker")
        if kind in ("ambiguous", "missing_skill"):
            if not row["expect_abstain"] or positive or row["forbidden"]:
                raise router.RoutingInputError("Abstention case contains a positive label")
        elif row["expect_abstain"] or not row["expected_primary"]:
            raise router.RoutingInputError("Actionable case missing proposed primary")
        if kind == "negative" and not row["forbidden"]:
            raise router.RoutingInputError("Negative case lacks forbidden targets")
    return payload


def evaluate_stress(catalog: dict[str, str], aliases: dict[str, list[str]],
                    manifest: dict, fixture: dict) -> dict:
    """Observe candidate positions separately from proposed, non-exhaustive labels."""
    observations = []
    for case in fixture["cases"]:
        output = router.recommend(case["query"], catalog, aliases, manifest)
        decision = output["routing_decision"]
        primary = decision["primary_skills"]
        auxiliary = decision["auxiliary_skills"]
        selected = set(primary + auxiliary)
        required = set(case["expected_primary"])
        optional = set(case["acceptable_auxiliary"])
        forbidden = sorted(set(case["forbidden"]) & selected)
        is_abstain = not selected
        observations.append({
            "id": case["id"], "kind": case["kind"],
            "language": router.prompt_language(case["query"]),
            "expected_primary": case["expected_primary"],
            "acceptable_auxiliary": case["acceptable_auxiliary"],
            "forbidden": case["forbidden"],
            "primary": primary, "auxiliary": auxiliary,
            "status": output["status"],
            "primary_overlap": sorted(required & set(primary)),
            "auxiliary_overlap": sorted((required | optional) & set(auxiliary)),
            "supported_required": sorted(required & selected),
            "all_required_supported": bool(required) and required <= selected,
            "forbidden_selected": forbidden,
            "abstained": is_abstain,
            "expected_abstention_met": case["expect_abstain"] and is_abstain,
            "unexpected_abstention": bool(required) and is_abstain,
            "unexpected_suggestion": case["expect_abstain"] and not is_abstain,
        })

    def metrics(rows: list[dict]) -> dict:
        return {
            "cases": len(rows),
            "primary_label_overlap": sum(bool(row["primary_overlap"]) for row in rows),
            "auxiliary_label_overlap": sum(bool(row["auxiliary_overlap"]) for row in rows),
            "all_required_supported": sum(row["all_required_supported"] for row in rows),
            "abstained": sum(row["abstained"] for row in rows),
            "expected_abstention_met": sum(row["expected_abstention_met"] for row in rows),
            "unexpected_abstention": sum(row["unexpected_abstention"] for row in rows),
            "unexpected_suggestion": sum(row["unexpected_suggestion"] for row in rows),
            "forbidden_selected_cases": sum(bool(row["forbidden_selected"]) for row in rows),
        }

    return {
        "classification": "offline_lexical_stress_diagnostic",
        "dataset_author": fixture["label_author"],
        "reviewer_independence": fixture["reviewer_independence"],
        "baseline_sha": fixture["baseline_sha"],
        "scoring": "DIAGNOSTIC_NON_GATING",
        "calibrated_semantic_accuracy": "NOT_MEASURED",
        "client_discovery": "NOT_OBSERVED",
        "client_effectiveness": "NOT_TESTED",
        "ranker_modified_for_cases": False,
        "count": len(observations),
        "summary": metrics(observations),
        "by_kind": {kind: metrics([r for r in observations if r["kind"] == kind])
                    for kind in sorted(KINDS)},
        "by_language": {lang: metrics([r for r in observations if r["language"] == lang])
                        for lang in ("ru", "en")},
        "limitations": (
            "Assistant-authored, non-exhaustive labels are not an independently "
            "adjudicated oracle. Overlaps and abstentions are diagnostics, not "
            "validated semantic correctness, false positive rates or client performance."
        ),
        "observations": observations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--summary-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = args.root.resolve()
        catalog = router.read_catalog(root)
        aliases = router.read_aliases(root / "fixtures/skill_routing_aliases.json", catalog)
        manifest = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
        fixture = load_stress(args.cases, catalog)
        report = evaluate_stress(catalog, aliases, manifest, fixture)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 2
    if args.summary_only:
        report = {key: value for key, value in report.items() if key != "observations"}
    print(json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
