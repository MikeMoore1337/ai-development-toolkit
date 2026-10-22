#!/usr/bin/env python3
"""Offline UX/UI evaluation evidence audit. Never certifies visual quality or approval."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

MAX_ASSETS = 12
MAX_ASSET_BYTES = 8 * 1024 * 1024
KINDS = {"PNG_CAPTURE", "SVG_SOURCE", "HTML_SOURCE"}
CASES = {"new-site", "substantial-redesign", "minor-ui-fix", "responsive-accessibility"}
CRITERIA = {
    "product-fit", "task-hierarchy", "compositional-originality",
    "mobile-desktop", "states", "accessibility", "motion",
    "cross-domain-swap", "design-authority",
}
MANUAL = {"NOT_REVIEWED", "ACCEPT", "REVISE"}


class EvidenceError(ValueError):
    pass


def catalog(root: Path) -> dict[str, dict]:
    source = root / "fixtures" / "ux_ui_eval_cases.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {"schema_version", "cases"} or data["schema_version"] != 1:
        raise EvidenceError("Invalid UX/UI scenario catalog")
    cases = data["cases"]
    if not isinstance(cases, list) or len(cases) != 4:
        raise EvidenceError("Exactly four scenario types required")
    result = {}
    for row in cases:
        if (not isinstance(row, dict) or set(row) !=
                {"id", "request_en", "request_ru", "needs_three", "criteria", "expected_gate"}):
            raise EvidenceError("Invalid scenario fields")
        if (row["id"] not in CASES or row["id"] in result
                or type(row["needs_three"]) is not bool):
            raise EvidenceError("Unknown or duplicate scenario")
        if any(not isinstance(row[k], str) or not row[k].strip() for k in
               ("request_en", "request_ru", "expected_gate")):
            raise EvidenceError("Missing bilingual prompt or gate")
        if (not isinstance(row["criteria"], list)
                or len(row["criteria"]) != len(set(row["criteria"]))
                or not set(row["criteria"]) <= CRITERIA
                or not {"design-authority", "accessibility"} <= set(row["criteria"])):
            raise EvidenceError("Missing or duplicate audit criterion")
        if row["needs_three"] != (row["id"] in {"new-site", "substantial-redesign"}):
            raise EvidenceError("Incorrect three-concept gate")
        if row["expected_gate"] != "HUMAN_VISUAL_REVIEW_REQUIRED":
            raise EvidenceError("Scenario cannot bypass visual review")
        result[row["id"]] = row
    if set(result) != CASES:
        raise EvidenceError("Scenario inventory incomplete")
    return result


def asset_record(entry: object, root: Path) -> dict:
    if (not isinstance(entry, dict) or set(entry) !=
            {"id", "purpose", "path", "kind", "viewport"}):
        raise EvidenceError("Malformed visual asset record")
    for key in ("id", "purpose", "path", "viewport"):
        if not isinstance(entry[key], str) or not entry[key].strip() or len(entry[key]) > 240:
            raise EvidenceError("Empty or oversized visual evidence field")
    if entry["kind"] not in KINDS:
        raise EvidenceError("Unknown visual asset kind")
    path = entry["path"]
    posix = PurePosixPath(path)
    if (posix.is_absolute() or "\\" in path or ":" in path or "\x00" in path
            or any(x in ("..", ".", "") for x in path.split("/"))):
        raise EvidenceError("Unsafe artifact path")
    base = root.resolve()
    target = base.joinpath(*posix.parts)
    if target.is_symlink() or any(parent.is_symlink() for parent in target.parents if parent != base):
        raise EvidenceError("Symlink visual evidence not accepted")
    resolved = target.resolve()
    if not resolved.is_relative_to(base) or not resolved.is_file():
        raise EvidenceError("Visual artifact missing or outside authorized root")
    size = resolved.stat().st_size
    if not 16 <= size <= MAX_ASSET_BYTES:
        raise EvidenceError("Empty or oversized visual artifact")
    ext = resolved.suffix.lower()
    required = {"PNG_CAPTURE": ".png", "SVG_SOURCE": ".svg", "HTML_SOURCE": ".html"}
    if ext != required[entry["kind"]]:
        raise EvidenceError("Visual extension disagrees with evidence kind")
    blob = resolved.read_bytes()
    if entry["kind"] == "PNG_CAPTURE" and (
            not blob.startswith(b"\x89PNG\r\n\x1a\n") or blob[12:16] != b"IHDR"):
        raise EvidenceError("Unrecognized PNG capture")
    if entry["kind"] == "SVG_SOURCE" and b"<svg" not in blob[:2048].lower():
        raise EvidenceError("Not an SVG drawing")
    if entry["kind"] == "HTML_SOURCE" and (
            b"<html" not in blob[:2048].lower()
            and b"<!doctype html" not in blob[:2048].lower()):
        raise EvidenceError("Not an HTML design source")
    return {
        "id": entry["id"],
        "purpose": entry["purpose"],
        "viewport": entry["viewport"],
        "kind": entry["kind"],
        "sha256": hashlib.sha256(blob).hexdigest(),
        "verification": ("CAPTURE_FILE_PRESENT_NOT_VISUALLY_INSPECTED"
                         if entry["kind"] == "PNG_CAPTURE"
                         else "SOURCE_FILE_PRESENT_RENDER_NOT_OBSERVED"),
    }


def audit(payload: object, asset_root: Path, definitions: dict[str, dict]) -> dict:
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version", "scenario_id", "design_authority",
        "directions", "chosen_direction", "rejected_directions", "visual_assets",
        "template_risks", "manual_reviews", "owner_approval",
        "implementation_status",
    } or payload["schema_version"] != 1:
        raise EvidenceError("Invalid UX/UI audit packet")
    scenario = definitions.get(payload["scenario_id"])
    if scenario is None:
        raise EvidenceError("Unknown scenario")
    if not isinstance(payload["design_authority"], str) or not payload["design_authority"].strip():
        raise EvidenceError("Project design authority must be identified")
    if payload["implementation_status"] != "NOT_STARTED":
        raise EvidenceError("Audit cannot claim UI implementation")
    if payload["owner_approval"] not in ("PENDING", "NOT_REQUESTED"):
        raise EvidenceError("Do not infer owner approval from offline audit")
    assets = payload["visual_assets"]
    if not isinstance(assets, list) or len(assets) > MAX_ASSETS:
        raise EvidenceError("Too many visual evidence entries")
    actual = [asset_record(item, asset_root) for item in assets]
    if len({x["id"] for x in actual}) != len(actual):
        raise EvidenceError("Duplicate visual evidence IDs")
    purposes = {x["purpose"]: x for x in actual}
    if len(purposes) != len(actual):
        raise EvidenceError("Duplicate visual evidence purposes")
    directions = payload["directions"]
    chosen = payload["chosen_direction"]
    rejected = payload["rejected_directions"]
    comparable = False
    if scenario["needs_three"]:
        if (not isinstance(directions, list) or len(directions) != 3
                or any(not isinstance(item, dict) or set(item) !=
                       {"id", "layout_signature", "information_architecture"}
                       for item in directions)):
            raise EvidenceError("New designs require exactly three composition hypotheses")
        identities = [x["id"] for x in directions]
        signatures = [x["layout_signature"] for x in directions]
        architectures = [x["information_architecture"] for x in directions]
        if (len(set(identities)) != 3 or chosen not in identities
                or not isinstance(rejected, list)
                or set(rejected) != (set(identities) - {chosen})
                or len(rejected) != 2):
            raise EvidenceError("Winner/rejection identities inconsistent")
        if (any(not isinstance(s, str) or len(s.strip()) < 5 for s in signatures + architectures)
                or len(set(signatures)) != 3 or len(set(architectures)) != 3):
            raise EvidenceError("Palette-only or incomplete layout hypotheses")
        wire = [purposes.get("wireframe:" + identity) for identity in identities]
        if all(wire):
            comparable = (
                len({x["sha256"] for x in wire}) == 3
                and len({x["viewport"] for x in wire}) == 1
            )
        risks = payload["template_risks"]
        if (not isinstance(risks, list) or len(risks) != 3
                or any(not isinstance(x, str) or len(x.strip()) < 8 for x in risks)
                or len({x.casefold().strip() for x in risks}) != 3):
            raise EvidenceError("Three distinct product-specific generic-template risks required")
    else:
        if directions not in ([], None) or chosen is not None or rejected not in ([], None):
            raise EvidenceError("Small fix/accessibility check must not fabricate three designs")
        if not isinstance(payload["template_risks"], list):
            raise EvidenceError("Invalid risk ledger")
    reviews = payload["manual_reviews"]
    if (not isinstance(reviews, list)
            or any(not isinstance(x, dict) or set(x) != {"id", "status", "rationale"} for x in reviews)):
        raise EvidenceError("Invalid manual-review checklist")
    review_ids = [x["id"] for x in reviews]
    if set(review_ids) != set(scenario["criteria"]) or len(review_ids) != len(set(review_ids)):
        raise EvidenceError("Required manual review criteria missing or duplicated")
    for item in reviews:
        if item["status"] not in MANUAL or not isinstance(item["rationale"], str):
            raise EvidenceError("Invalid manual-review status")
        if item["status"] != "NOT_REVIEWED" and len(item["rationale"].strip()) < 12:
            raise EvidenceError("Manual decision requires a specific rationale")
        if item["status"] == "NOT_REVIEWED" and item["rationale"].strip():
            raise EvidenceError("Unreviewed criterion cannot carry fabricated rationale")
    desktop_mobile = "winner:desktop" in purposes and "winner:mobile" in purposes
    if scenario["needs_three"]:
        preview_complete = comparable and desktop_mobile
    else:
        preview_complete = desktop_mobile
    if any(item["status"] == "REVISE" for item in reviews):
        gate = "NEEDS_DESIGN_REVISION"
    elif not preview_complete:
        gate = "VISUAL_PACKAGE_MISSING"
    else:
        gate = "AWAITING_HUMAN_VISUAL_REVIEW"
    return {
        "classification": "OFFLINE_VISUAL_EVIDENCE_PRECHECK",
        "scenario_id": payload["scenario_id"],
        "gate": gate,
        "comparable_three_artifacts": comparable,
        "desktop_mobile_present": desktop_mobile,
        "asset_digests": actual,
        "manual_review_pending": sum(x["status"] == "NOT_REVIEWED" for x in reviews),
        "manual_review_declared": sum(x["status"] != "NOT_REVIEWED" for x in reviews),
        "independent_visual_quality": "NOT_VERIFIED",
        "accessibility_conformance": "NOT_TESTED",
        "working_interactions": "NOT_TESTED",
        "owner_approval": payload["owner_approval"],
        "implementation_status": "NOT_STARTED",
        "limitations": (
            "Files/hashes and declared layout structure checked only. Not proof of three "
            "visually distinct compositions, manual inspection, WCAG, approval or live UI."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog-only", action="store_true")
    parser.add_argument("--packet", type=Path)
    parser.add_argument("--asset-root", type=Path)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    try:
        cases = catalog(args.root)
        if args.catalog_only and args.packet is None and args.asset_root is None:
            output = {"cases": len(cases), "scenario_ids": sorted(cases),
                      "visual_quality": "NOT_TESTED"}
        elif args.packet and args.asset_root and not args.catalog_only:
            packet = json.loads(args.packet.read_text(encoding="utf-8"))
            output = audit(packet, args.asset_root, cases)
        else:
            raise EvidenceError("Pass --catalog-only OR --packet and --asset-root")
        print(json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True))
    except (EvidenceError, OSError, ValueError, TypeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
