#!/usr/bin/env python3
"""Read-only structural checker for an optional UX/UI Design Orchestra receipt."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

MODES = {"create-design", "audit-proposal", "audit-only", "implement-approved"}
WORKERS = {"ACTUAL_SUBAGENT", "GENERIC_SUBAGENT", "SEQUENTIAL"}
SOURCES = {"LOADED", "REFERENCE_ONLY", "UNAVAILABLE"}
EVIDENCE = {"RENDERED", "SOURCE_ONLY", "NOT_OBSERVED"}
GATES = {"AWAITING_VISUAL_APPROVAL", "VISUAL_PACKAGE_MISSING", "AUDIT_COMPLETE",
         "OWNER_ACCEPTED", "IMPLEMENTED_NOT_RELEASED"}



# Optional exact-original mode. These are client invocation *claims*, not proof
# that a browser, a model, or any external binary actually ran.
ORIGINALS = ("impeccable", "design-taste-frontend", "ui-ux-pro-max")


def inspect_originals(project: Path) -> list[dict]:
    """Non-executing local file inventory. No downloads, hooks or skill activation."""
    import hashlib

    result = []
    base = project / ".agents" / "skills"
    for name in ORIGINALS:
        root = base / name
        chain = (project, project / ".agents", base, root)
        if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
               for p in chain):
            result.append({"name": name, "status": "UNSAFE_LINK"})
            continue
        if not root.is_dir() or not (root / "SKILL.md").is_file():
            result.append({"name": name, "status": "MISSING"})
            continue
        paths = sorted(root.rglob("*"))
        if any(p.is_symlink() or (hasattr(p, "is_junction") and p.is_junction())
               for p in paths):
            result.append({"name": name, "status": "UNSAFE_LINK"})
            continue
        try:
            text = (root / "SKILL.md").read_text(encoding="utf-8")
            frontmatter = text.split("---", 2)
            declared = None
            if len(frontmatter) == 3 and not frontmatter[0].strip():
                for line in frontmatter[1].splitlines():
                    if line.startswith("name:"):
                        declared = line.partition(":")[2].strip().strip("'\\\"")
            if declared != name or not (root / "scripts").is_dir():
                result.append({"name": name, "status": "INCOMPLETE"})
                continue
            digest = hashlib.sha256()
            for file in paths:
                if file.is_file():
                    digest.update(file.relative_to(root).as_posix().encode() + b"\0")
                    digest.update(hashlib.sha256(file.read_bytes()).digest())
            result.append({"name": name, "status": "FILES_PRESENT_UNATTESTED",
                           "local_tree_sha256": digest.hexdigest()})
        except (OSError, UnicodeError):
            result.append({"name": name, "status": "UNREADABLE"})
    return result


def validate_originals(report: dict) -> list[str]:
    config = report.get("original_design_skills")
    if config is None:
        return []
    if not isinstance(config, dict) or config.get("mode") not in ("STANDARD", "ALL_THREE"):
        return ["invalid original design skills mode"]
    if config["mode"] == "STANDARD":
        return [] if not config.get("invocations") else ["standard mode has unexpected invocations"]
    rows = config.get("invocations")
    if not isinstance(rows, list) or len(rows) != 3:
        return ["all-three originals require exactly three receipts"]
    errors, seen = [], set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("invalid original skill receipt")
            continue
        name = row.get("name")
        if name not in ORIGINALS or name in seen:
            errors.append("unknown or duplicate original skill")
            continue
        seen.add(name)
        status = row.get("status")
        if status not in ("INVOKED", "NOT_VERIFIED", "UNAVAILABLE"):
            errors.append(f"{name}: invalid invocation status")
        if status == "INVOKED":
            revision = row.get("source_revision")
            evidence = row.get("invocation_evidence")
            if (row.get("loaded") is not True or not isinstance(revision, str)
                    or len(revision) != 40
                    or any(c not in "0123456789abcdef" for c in revision.lower())
                    or not isinstance(evidence, str) or not evidence.strip()):
                errors.append(f"{name}: invocation lacks source or trace")
        elif row.get("invocation_evidence"):
            errors.append(f"{name}: unverified invocation claims evidence")
    if seen != set(ORIGINALS):
        errors.append("all-three originals incomplete")
    if report.get("gate") in ("AWAITING_VISUAL_APPROVAL", "OWNER_ACCEPTED",
                              "IMPLEMENTED_NOT_RELEASED"):
        if errors or any(not isinstance(x, dict) or x.get("status") != "INVOKED"
                         for x in rows):
            errors.append("all-three approval requires three actual invocations")
    return errors


def validate(report: object) -> list[str]:
    """Fail closed on contradictory claims; does not independently verify screenshots."""
    if not isinstance(report, dict):
        return ["report must be object"]
    errors: list[str] = []
    for key in ("mode", "project", "baseline", "design_authority", "workers",
                "evidence", "findings", "proposal", "implementation", "gate"):
        if key not in report:
            errors.append(f"missing {key}")
    if errors:
        return errors
    mode = report["mode"]
    if mode not in MODES:
        errors.append("invalid mode")
    for name in ("project", "baseline", "design_authority"):
        if not isinstance(report[name], str) or not report[name].strip():
            errors.append(f"invalid {name}")
    workers = report["workers"]
    if not isinstance(workers, list) or not workers:
        errors.append("workers must be nonempty list")
        workers = []
    if len(workers) > 3:
        errors.append("too many workstreams (maximum 3)")
    selected = set()
    for i, worker in enumerate(workers):
        if not isinstance(worker, dict):
            errors.append(f"worker {i}: invalid")
            continue
        name = worker.get("name")
        if not isinstance(name, str) or not name.strip() or name in selected:
            errors.append(f"worker {i}: missing or duplicate name")
        else:
            selected.add(name)
        if worker.get("execution") not in WORKERS:
            errors.append(f"worker {i}: invalid execution")
        if worker.get("source_status") not in SOURCES:
            errors.append(f"worker {i}: invalid source status")
        if worker.get("execution") in {"ACTUAL_SUBAGENT", "GENERIC_SUBAGENT"} and not worker.get("trace"):
            errors.append(f"worker {i}: subagent missing actual trace")
        if worker.get("execution") == "SEQUENTIAL" and worker.get("trace"):
            errors.append(f"worker {i}: sequential work cannot claim agent trace")
        if worker.get("source_status") == "UNAVAILABLE" and worker.get("execution") != "SEQUENTIAL":
            errors.append(f"worker {i}: unavailable skill cannot be claimed loaded by subagent")
    if report.get("max_concurrent_workers", 3) not in (1, 2, 3):
        errors.append("max_concurrent_workers must be 1..3")
    actual_concurrent = report.get("observed_peak_workers", 1)
    if type(actual_concurrent) is not int or not 1 <= actual_concurrent <= report.get("max_concurrent_workers", 3):
        errors.append("observed_peak_workers invalid")
    if actual_concurrent > 1 and not any(w.get("execution") != "SEQUENTIAL" for w in workers if isinstance(w, dict)):
        errors.append("parallel claim without subagents")
    ledger = report["evidence"]
    if not isinstance(ledger, list):
        errors.append("evidence must be list")
        ledger = []
    evidence_ids = set()
    for i, row in enumerate(ledger):
        if not isinstance(row, dict):
            errors.append(f"evidence {i}: invalid")
            continue
        identity = row.get("id")
        if not isinstance(identity, str) or not identity or identity in evidence_ids:
            errors.append(f"evidence {i}: missing or duplicate id")
        else:
            evidence_ids.add(identity)
        if row.get("status") not in EVIDENCE:
            errors.append(f"evidence {i}: invalid status")
        if row.get("status") == "RENDERED" and not all(isinstance(row.get(x), str) and row[x].strip() for x in ("artifact_ref", "route", "viewport", "provenance")):
            errors.append(f"evidence {i}: rendered claim lacks proof details")
        if row.get("status") == "NOT_OBSERVED" and row.get("artifact_ref"):
            errors.append(f"evidence {i}: not observed but artifact claimed")
    findings = report["findings"]
    if not isinstance(findings, list):
        errors.append("findings must be list")
        findings = []
    for i, row in enumerate(findings):
        if not isinstance(row, dict) or row.get("status") not in ("OBSERVED", "HYPOTHESIS"):
            errors.append(f"finding {i}: invalid")
            continue
        references = row.get("evidence_ids")
        if not isinstance(references, list) or any(x not in evidence_ids for x in references):
            errors.append(f"finding {i}: invalid evidence refs")
        if row["status"] == "OBSERVED" and not references:
            errors.append(f"finding {i}: observed without evidence")
        if not row.get("problem") or not row.get("recommendation"):
            errors.append(f"finding {i}: incomplete problem or fix")
    proposal = report["proposal"]
    if not isinstance(proposal, dict) or not isinstance(proposal.get("selected_direction"), str) or not proposal["selected_direction"].strip():
        errors.append("missing selected design direction")
    else:
        if proposal.get("visual_status") not in ("TEXT_SPEC", "RENDERED", "NOT_PREPARED"):
            errors.append("invalid proposal visual status")
        if proposal.get("visual_status") == "RENDERED" and not proposal.get("artifact_refs"):
            errors.append("proposal claims rendered visuals without artifacts")
    implementation = report["implementation"]
    if not isinstance(implementation, dict) or implementation.get("status") not in ("NOT_STARTED", "IMPLEMENTED"):
        errors.append("invalid implementation status")
    if report["gate"] not in GATES:
        errors.append("invalid gate")
    if mode != "implement-approved":
        if report.get("changed_ui") is not False:
            errors.append("audit must explicitly affirm no UI changes")
        if isinstance(implementation, dict) and implementation.get("status") != "NOT_STARTED":
            errors.append("audit must not claim implementation")
        if report["gate"] in {"OWNER_ACCEPTED", "IMPLEMENTED_NOT_RELEASED"}:
            errors.append("audit cannot claim owner acceptance or implementation")
    else:
        if not isinstance(report.get("owner_approval_evidence"), str) or not report["owner_approval_evidence"].strip():
            errors.append("implementation requires explicit owner approval evidence")
        if report["gate"] == "AWAITING_VISUAL_APPROVAL" and report.get("changed_ui"):
            errors.append("cannot implement before visual approval")
    if mode == "audit-proposal" and report["gate"] == "AWAITING_VISUAL_APPROVAL" and isinstance(proposal, dict) and proposal.get("visual_status") == "NOT_PREPARED":
        errors.append("approval requested without design proposal")
    if mode == "create-design" or (mode == "audit-proposal" and report.get("design_exploration_required") is True):
        exploration = report.get("design_exploration")
        if not isinstance(exploration, dict):
            errors.append("new/substantial design requires three-direction exploration")
        else:
            directions = exploration.get("directions")
            ids = set()
            compositions = set()
            architectures = set()
            if not isinstance(directions, list) or len(directions) != 3:
                errors.append("design exploration requires exactly three directions")
                directions = []
            for idx, direction in enumerate(directions):
                if not isinstance(direction, dict):
                    errors.append(f"direction {idx}: invalid")
                    continue
                for field in ("id", "title", "product_story", "information_architecture",
                              "composition", "typography_and_imagery", "primary_interaction", "tradeoff"):
                    value = direction.get(field)
                    if not isinstance(value, str) or not value.strip():
                        errors.append(f"direction {idx}: missing {field}")
                identity = direction.get("id")
                if isinstance(identity, str) and identity.strip():
                    if identity in ids:
                        errors.append("design exploration duplicate direction id")
                    ids.add(identity)
                for field, seen in (("composition", compositions), ("information_architecture", architectures)):
                    value = direction.get(field)
                    if isinstance(value, str) and value.strip():
                        normalized = " ".join(value.casefold().split())
                        if normalized in seen:
                            errors.append(f"design exploration repeated {field} (palette swap only)")
                        seen.add(normalized)
            selected = exploration.get("selected_id")
            if not isinstance(selected, str) or selected not in ids:
                errors.append("design exploration selected direction missing")
            rationale = exploration.get("selection_rationale")
            if not isinstance(rationale, str) or not rationale.strip():
                errors.append("design exploration missing selection rationale")
            rejections = exploration.get("rejections")
            rejected = set()
            if not isinstance(rejections, list) or len(rejections) != 2:
                errors.append("design exploration requires two rejected directions")
            else:
                for i, rejection in enumerate(rejections):
                    if not isinstance(rejection, dict):
                        errors.append(f"design exploration rejection {i}: invalid")
                        continue
                    rid, reason = rejection.get("id"), rejection.get("reason")
                    if not isinstance(rid, str) or not isinstance(reason, str) or not reason.strip():
                        errors.append(f"design exploration rejection {i}: incomplete")
                    else:
                        rejected.add(rid)
                if not isinstance(selected, str) or selected in rejected or rejected != (ids - {selected}):
                    errors.append("design exploration rejected IDs must match unselected directions")
            swap = exploration.get("cross_domain_swap_test")
            if not isinstance(swap, dict):
                errors.append("design exploration requires cross-domain swap test")
                swap_passes = False
            else:
                swap_passes = swap.get("would_require_structural_redesign") is True
                if not isinstance(swap.get("test_domain"), str) or not swap["test_domain"].strip():
                    errors.append("design exploration missing swap target")
                if not isinstance(swap.get("explanation"), str) or not swap["explanation"].strip():
                    errors.append("design exploration missing swap explanation")
                if type(swap.get("would_require_structural_redesign")) is not bool:
                    errors.append("design exploration swap result invalid")
            comp_status = exploration.get("status")
            if comp_status not in ("COMPARED", "NEEDS_REVISION"):
                errors.append("design exploration comparison status invalid")
            if report["gate"] == "AWAITING_VISUAL_APPROVAL" and (len(directions) != 3 or comp_status != "COMPARED" or not swap_passes):
                errors.append("cannot request visual approval without distinct compared directions and passing swap test")
            comparison = exploration.get("visual_comparison")
            if not isinstance(comparison, dict) or comparison.get("status") not in ("RENDERED", "MISSING"):
                errors.append("design exploration requires honest visual comparison status")
                comparison = {}
            frames = comparison.get("frames")
            if not isinstance(frames, list):
                errors.append("design exploration visual frames must be a list")
                frames = []
            if comparison.get("status") == "MISSING" and frames:
                errors.append("missing visual comparison cannot claim frame artifacts")
            if comparison.get("status") == "RENDERED":
                if len(frames) != 3:
                    errors.append("visual comparison requires exactly three rendered frames")
                frame_ids = set()
                frame_refs = set()
                layout_signatures = set()
                viewports = set()
                rendered_evidence = {
                    row["id"]: row for row in ledger if isinstance(row, dict)
                    and isinstance(row.get("id"), str) and row.get("status") == "RENDERED"
                }
                for idx, frame in enumerate(frames):
                    if not isinstance(frame, dict):
                        errors.append(f"visual frame {idx}: invalid")
                        continue
                    direction_id = frame.get("direction_id")
                    if not isinstance(direction_id, str) or direction_id not in ids or direction_id in frame_ids:
                        errors.append(f"visual frame {idx}: unknown or duplicate direction")
                    else:
                        frame_ids.add(direction_id)
                    evidence_id = frame.get("evidence_id")
                    evidence_row = rendered_evidence.get(evidence_id) if isinstance(evidence_id, str) else None
                    if evidence_row is None:
                        errors.append(f"visual frame {idx}: missing rendered evidence")
                    else:
                        source_ref = evidence_row.get("artifact_ref")
                        if source_ref in frame_refs:
                            errors.append("visual comparison reuses same unsegmented artifact")
                        frame_refs.add(source_ref)
                        viewports.add(evidence_row.get("viewport"))
                    signature = frame.get("layout_signature")
                    if (not isinstance(signature, list) or not 3 <= len(signature) <= 12
                            or any(not isinstance(item, str) or not item.strip() for item in signature)):
                        errors.append(f"visual frame {idx}: invalid ordered layout signature")
                    else:
                        normalized = tuple(" ".join(item.casefold().split()) for item in signature)
                        if normalized in layout_signatures:
                            errors.append("visual comparison repeats same composition signature")
                        layout_signatures.add(normalized)
                if frame_ids != ids:
                    errors.append("visual comparison frame directions do not match three candidates")
                if len(viewports) > 1:
                    errors.append("visual comparison frames must use matching viewport scale")
            if report["gate"] == "AWAITING_VISUAL_APPROVAL":
                if comparison.get("status") != "RENDERED" or len(frames) != 3:
                    errors.append("cannot request visual approval before three rendered visual sketches")
                if isinstance(proposal, dict):
                    finals = proposal.get("artifact_refs")
                    if (proposal.get("visual_status") != "RENDERED" or not isinstance(finals, list)
                            or len(set(x for x in finals if isinstance(x, str) and x.strip())) < 2):
                        errors.append("cannot request visual approval without winner desktop and mobile previews")
    if mode == "create-design":
        quality = report.get("design_quality")
        if not isinstance(quality, dict):
            errors.append("create-design requires design_quality declaration")
        else:
            for key in ("product_specific_direction", "selected_over_alternative"):
                value = quality.get(key)
                if not isinstance(value, str) or not value.strip():
                    errors.append(f"design quality missing {key}")
            risks = quality.get("generic_template_risks")
            if (not isinstance(risks, list) or len(risks) < 3
                    or any(not isinstance(x, str) or not x.strip() for x in risks)
                    or len({x.strip().casefold() for x in risks if isinstance(x, str)}) != len(risks)):
                errors.append("design quality requires three distinct generic template risks")
            if quality.get("impeccable_source_status") not in SOURCES:
                errors.append("design quality missing honest Impeccable source status")
            if quality.get("quality_status") not in ("READY_FOR_VISUAL_REVIEW", "NEEDS_DESIGN_REVISION"):
                errors.append("design quality invalid status")
            if report["gate"] == "AWAITING_VISUAL_APPROVAL" and quality.get("quality_status") != "READY_FOR_VISUAL_REVIEW":
                errors.append("cannot request visual approval before design quality revision")
        if report["gate"] == "AUDIT_COMPLETE":
            errors.append("new design cannot claim completed UI audit")
        if report["gate"] == "AWAITING_VISUAL_APPROVAL" and isinstance(proposal, dict) and proposal.get("visual_status") != "RENDERED":
            errors.append("new design cannot request visual approval without rendered visuals")
    errors.extend(validate_originals(report))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, nargs="?")
    parser.add_argument("--inspect-originals", type=Path)
    args = parser.parse_args()
    if args.inspect_originals is not None:
        print(json.dumps({"skills": inspect_originals(args.inspect_originals),
                          "upstream_identity": "NOT_ATTESTED",
                          "client_invocation": "NOT_VERIFIED"}, indent=2))
        return 0
    if args.report is None:
        parser.error("report is required unless --inspect-originals is used")
    try:
        payload = json.loads(args.report.read_text(encoding="utf-8"))
        errors = validate(payload)
    except (OSError, ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print("FAIL:", error)
    if not errors:
        print("PASS: structure consistent; evidence and agent execution NOT independently verified")
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
