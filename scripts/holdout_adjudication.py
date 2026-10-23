#!/usr/bin/env python3
"""Prepare and audit blinded human holdout reviews; no AI, API or skill execution."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from skill_routing_eval import ROOT, RoutingInputError, load_holdout, read_catalog

SCHEMA = 1
REVIEW_KEYS = frozenset({
    "id", "kind", "query", "decision", "proposed_targets",
    "proposed_avoid_top1", "reviewer_id", "rationale",
})


def classify_label_difference(reference_targets: list[str], reviewer_targets: list[str],
                              reference_forbidden: list[str],
                              reviewer_forbidden: list[str]) -> str:
    """Classify label-set differences; this does not measure router accuracy."""
    reference = set(reference_targets)
    reviewed = set(reviewer_targets)
    # Called only for disagreements. If targets agree, only negative controls differ.
    if reference == reviewed:
        return "forbidden_only"
    if not reference & reviewed:
        return "disjoint_targets"
    if reviewed < reference:
        return "reviewer_subset"
    if reference < reviewed:
        return "reviewer_superset"
    return "partial_overlap"


def canonical_digest(catalog: dict[str, str]) -> str:
    serialized = json.dumps(catalog, sort_keys=True, ensure_ascii=False,
                            separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def catalog_for_reviewer(root: Path) -> dict:
    """Show the skill choices without holdout labels or router predictions."""
    catalog = read_catalog(root)
    return {
        "schema_version": SCHEMA,
        "purpose": "blinded_review_skill_catalog",
        "catalog_sha256": canonical_digest(catalog),
        "source": "declared_SKILL.md_frontmatter_name_and_description_only",
        "skill_count": len(catalog),
        "skills": [
            {"name": name, "description": description}
            for name, description in sorted(catalog.items())
        ],
        "reviewer_independence": "NOT_VERIFIED",
        "client_effectiveness": "NOT_TESTED",
    }


def prepare(root: Path, holdout_file: Path) -> dict:
    """Suppress original labels and model predictions to reduce reviewer anchoring."""
    catalog = read_catalog(root)
    cases = load_holdout(holdout_file, catalog)
    return {
        "schema_version": SCHEMA,
        "purpose": "blinded_holdout_review_not_a_model_evaluation",
        "source_sha256": hashlib.sha256(holdout_file.read_bytes()).hexdigest(),
        "catalog_sha256": canonical_digest(catalog),
        "review_status": "PENDING_HUMAN_REVIEW",
        "independence": "REVIEWER_DECLARATION_NOT_VERIFIED",
        "cases": [
            {
                "id": case["id"], "kind": case["kind"], "query": case["query"],
                "decision": "PENDING", "proposed_targets": [],
                "proposed_avoid_top1": [], "reviewer_id": "", "rationale": "",
            }
            for case in cases
        ],
    }


def audit(root: Path, holdout_file: Path, packet: dict) -> dict:
    """Check reviewer-declared decisions and reference disagreements, not independence."""
    template = prepare(root, holdout_file)
    if not isinstance(packet, dict) or set(packet) != set(template) or (
        any(packet.get(k) != template[k]
            for k in template if k not in ("cases", "review_status"))
    ):
        raise RoutingInputError("Review packet schema or immutable source digest mismatch")
    cases = packet.get("cases")
    if not isinstance(cases, list) or len(cases) != len(template["cases"]):
        raise RoutingInputError("Review case count mismatch")
    catalog = read_catalog(root)
    reference = load_holdout(holdout_file, catalog)
    counts = {"pending": 0, "accepted": 0, "challenged": 0,
              "agreement": 0, "disagreement": 0}
    disagreements = []
    breakdown = dict.fromkeys((
        "reviewer_subset", "reviewer_superset", "partial_overlap",
        "disjoint_targets", "forbidden_only",
    ), 0)
    # IDs make an incomplete or disputed packet actionable without exposing
    # frozen reference labels or changing the independently reviewed input.
    pending_case_ids = []
    challenged_case_ids = []
    for row, original, blank in zip(cases, reference, template["cases"]):
        if (not isinstance(row, dict) or set(row) != REVIEW_KEYS
                or any(row.get(k) != blank[k] for k in ("id", "kind", "query"))):
            raise RoutingInputError("Missing, reordered or modified review case")
        decision = row["decision"]
        if decision not in ("PENDING", "ACCEPT", "CHALLENGE"):
            raise RoutingInputError("Invalid reviewer decision")
        if not isinstance(row["proposed_targets"], list) or not isinstance(
                row["proposed_avoid_top1"], list):
            raise RoutingInputError("Invalid reviewer labels")
        proposed = row["proposed_targets"]
        forbidden = row["proposed_avoid_top1"]
        for values in (proposed, forbidden):
            if (len(values) != len(set(map(str, values)))
                    or any(not isinstance(v, str) or v not in catalog for v in values)):
                raise RoutingInputError("Unknown or duplicated reviewed target")
        if set(proposed) & set(forbidden):
            raise RoutingInputError("Reviewed allowed and forbidden skills overlap")
        if original["kind"] != "negative" and forbidden:
            raise RoutingInputError("Forbidden top-1 only applies to negative cases")
        if not isinstance(row["reviewer_id"], str) or not isinstance(
                row["rationale"], str):
            raise RoutingInputError("Invalid reviewer identity or rationale")
        if decision == "PENDING":
            if (proposed or forbidden or row["reviewer_id"].strip()
                    or row["rationale"].strip()):
                raise RoutingInputError("Pending decision cannot contain reviewer evidence")
            counts["pending"] += 1
            pending_case_ids.append(original["id"])
            continue
        if (not row["reviewer_id"].strip() or len(row["rationale"].strip()) < 12):
            raise RoutingInputError("Reviewed decision requires reviewer and rationale")
        if decision == "CHALLENGE":
            if proposed or forbidden:
                raise RoutingInputError("Challenged reference cannot contain approved labels")
            counts["challenged"] += 1
            challenged_case_ids.append(original["id"])
            continue
        if not proposed or (original["kind"] == "negative" and not forbidden):
            raise RoutingInputError("Accepted review requires independent target labels")
        counts["accepted"] += 1
        agreed = (set(proposed) == set(original["expected"])
                  and set(forbidden) == set(original.get("avoid_top1", [])))
        if agreed:
            counts["agreement"] += 1
        else:
            counts["disagreement"] += 1
            kind = classify_label_difference(
                original["expected"], proposed, original.get("avoid_top1", []), forbidden,
            )
            breakdown[kind] += 1
            disagreements.append({
                "id": original["id"],
                "difference_kind": kind,
                "reference_targets": original["expected"],
                "reviewer_targets": proposed,
                "reference_only_targets": sorted(set(original["expected"]) - set(proposed)),
                "reviewer_only_targets": sorted(set(proposed) - set(original["expected"])),
                "reference_forbidden": original.get("avoid_top1", []),
                "reviewer_forbidden": forbidden,
                "forbidden_changed": set(forbidden) != set(original.get("avoid_top1", [])),
            })

    if packet["review_status"] != (
            "PENDING_HUMAN_REVIEW" if counts["pending"] else "REVIEWER_DECLARED_COMPLETE"):
        raise RoutingInputError("Incorrect review_status relative to pending cases")
    return {
        "classification": "offline_label_review_audit",
        "reference_unchanged": True,
        "source_sha256": template["source_sha256"],
        "catalog_sha256": template["catalog_sha256"],
        "reviewer_independence": "NOT_VERIFIED",
        "reviewer_identity": "SELF_DECLARED_ONLY",
        "client_effectiveness": "NOT_TESTED",
        "ready_for_independent_accuracy_claim": False,
        "status": "REVIEW_INCOMPLETE" if counts["pending"] else "DECLARATIONS_COMPLETE_UNVERIFIED",
        "cases": len(cases),
        **counts,
        "pending_case_ids": pending_case_ids,
        "challenged_case_ids": challenged_case_ids,
        "disagreement_breakdown": breakdown,
        "disagreements": disagreements,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "catalog", "audit"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--holdout", type=Path,
                        default=ROOT / "fixtures/skill_routing_holdout.json")
    parser.add_argument("--packet", type=Path, help="Saved and completed review JSON for audit")
    parser.add_argument("--output", type=Path, help="New file to write; existing files are never overwritten")
    args = parser.parse_args(argv)
    try:
        if args.action == "audit" and args.packet is None:
            raise RoutingInputError("Audit requires --packet")
        if args.action in {"prepare", "catalog"} and args.packet is not None:
            raise RoutingInputError("Review preparation does not accept --packet")
        if args.action == "prepare":
            result = prepare(args.root.resolve(), args.holdout)
        elif args.action == "catalog":
            result = catalog_for_reviewer(args.root.resolve())
        else:
            result = audit(args.root.resolve(), args.holdout,
                           json.loads(args.packet.read_text(encoding="utf-8")))
        output = json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(output)
        else:
            print(output, end="")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
