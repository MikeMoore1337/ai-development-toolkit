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
GATES = {"AWAITING_VISUAL_APPROVAL", "VISUAL_PACKAGE_MISSING", "NEEDS_DESIGN_REVISION",
         "AUDIT_COMPLETE", "OWNER_ACCEPTED", "IMPLEMENTED_NOT_RELEASED"}



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



VISUAL_DECISIONS = {"PRESERVED", "CHANGED", "UNCERTAIN"}
VISUAL_RECOMMENDATIONS = {"KEEP_BASELINE", "REFINE_BASELINE", "PROPOSE_CANDIDATE", "UNDECIDED"}


def validate_visual_lineage(report: dict) -> list[str]:
    """Validate claims of retaining a preferred/approved predecessor.

    This never ranks aesthetics, compares pixels or certifies that links resolve.
    The baseline belongs to the consumer project/chat, never the Toolkit repo.
    """
    record = report.get("visual_lineage")
    ready = report.get("gate") == "AWAITING_VISUAL_APPROVAL"
    if record is None:
        return (["prior preferred visual baseline needs lineage before visual approval"]
                if ready and report.get("prior_visual_baseline") is True else [])
    if not isinstance(record, dict):
        return ["visual lineage must be an object"]
    errors: list[str] = []
    baseline = record.get("baseline")
    candidate = record.get("candidate")
    for label, value in (("baseline", baseline), ("candidate", candidate)):
        if not isinstance(value, dict):
            errors.append(f"visual lineage missing {label}")
            continue
        if not isinstance(value.get("version"), str) or not value["version"].strip():
            errors.append(f"visual lineage {label} version missing")
        refs = value.get("artifact_refs")
        if (not isinstance(refs, list) or not refs
                or any(not isinstance(x, str) or not x.strip() for x in refs)):
            errors.append(f"visual lineage {label} artifact references missing")
    if isinstance(baseline, dict):
        if baseline.get("status") not in {"USER_PREFERRED", "OWNER_ACCEPTED", "PREVIOUS_CANDIDATE"}:
            errors.append("visual lineage baseline status invalid")
        strengths = baseline.get("strengths")
        if not isinstance(strengths, list) or not strengths or any(
                not isinstance(x, str) or not x.strip() for x in strengths):
            errors.append("visual lineage baseline strengths missing")
    if (isinstance(baseline, dict) and isinstance(candidate, dict)
            and baseline.get("version") == candidate.get("version")):
        errors.append("visual lineage baseline and candidate versions must differ")
    review = record.get("visual_review")
    if not isinstance(review, dict) or review.get("status") not in {"REVIEWED", "NOT_REVIEWED"}:
        errors.append("visual lineage review status invalid")
    else:
        comparisons = review.get("comparisons")
        if not isinstance(comparisons, list):
            errors.append("visual lineage comparisons must be a list")
        elif review["status"] == "REVIEWED" and not comparisons:
            errors.append("visual lineage reviewed claim lacks observations")
        else:
            seen = set()
            for i, item in enumerate(comparisons):
                if not isinstance(item, dict):
                    errors.append(f"visual lineage comparison {i} invalid")
                    continue
                aspect = item.get("aspect")
                if not isinstance(aspect, str) or not aspect.strip() or aspect in seen:
                    errors.append(f"visual lineage comparison {i} aspect invalid or duplicate")
                else:
                    seen.add(aspect)
                if item.get("assessment") not in VISUAL_DECISIONS:
                    errors.append(f"visual lineage comparison {i} decision invalid")
                if (not isinstance(item.get("observation"), str)
                        or not item["observation"].strip()):
                    errors.append(f"visual lineage comparison {i} observation missing")
            if review["status"] == "NOT_REVIEWED" and comparisons:
                errors.append("unreviewed visual lineage cannot claim observations")
    technical = record.get("technical_review")
    if not isinstance(technical, dict) or technical.get("status") not in {
            "PASS", "FAIL", "NOT_VERIFIED"}:
        errors.append("visual lineage technical status invalid")
    elif (technical["status"] == "PASS"
          and not isinstance(technical.get("evidence"), str)):
        errors.append("technical PASS needs a separate evidence reference")
    if record.get("recommendation") not in VISUAL_RECOMMENDATIONS:
        errors.append("visual lineage recommendation invalid")
    if record.get("owner_decision") not in {
            "PENDING", "KEEP_BASELINE", "APPROVE_CANDIDATE", "REQUEST_CHANGES"}:
        errors.append("visual lineage owner decision invalid")
    if report.get("mode") != "implement-approved" and record.get("owner_decision") == "APPROVE_CANDIDATE":
        errors.append("design preparation cannot claim owner approved candidate")
    if (ready and record.get("recommendation") == "PROPOSE_CANDIDATE"
            and isinstance(review, dict) and review.get("status") != "REVIEWED"):
        errors.append("candidate replacement needs observed visual comparison")
    return errors


def validate_exploration(exploration: object) -> list[str]:
    """Optional exploration: no imposed style, composition or number of concepts."""
    if not isinstance(exploration, dict):
        return ["design exploration must be an object"]
    errors: list[str] = []
    directions = exploration.get("directions")
    if not isinstance(directions, list) or not directions:
        return ["design exploration directions must be a nonempty list"]
    ids = set()
    for idx, direction in enumerate(directions):
        if not isinstance(direction, dict):
            errors.append(f"direction {idx}: invalid")
            continue
        for field in ("id", "title"):
            value = direction.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"direction {idx}: missing {field}")
        ident = direction.get("id")
        if isinstance(ident, str) and ident.strip():
            if ident in ids:
                errors.append("design exploration duplicate direction id")
            ids.add(ident)
    selected = exploration.get("selected_id")
    if not isinstance(selected, str) or selected not in ids:
        errors.append("design exploration selected direction missing")
    rejections = exploration.get("rejections", [])
    if not isinstance(rejections, list):
        errors.append("design exploration rejections must be a list")
    else:
        rejected = []
        for i, item in enumerate(rejections):
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or (
                    not isinstance(item.get("reason"), str) or not item["reason"].strip()):
                errors.append(f"design exploration rejection {i}: incomplete")
            else:
                rejected.append(item["id"])
        if len(rejected) != len(set(rejected)) or set(rejected) - (ids - {selected}):
            errors.append("design exploration rejected IDs invalid")
    swap = exploration.get("cross_domain_swap_test")
    if swap is not None and (
            not isinstance(swap, dict)
            or type(swap.get("would_require_structural_redesign")) is not bool):
        errors.append("design exploration optional swap-test declaration invalid")
    comparison = exploration.get("visual_comparison")
    if comparison is not None:
        if not isinstance(comparison, dict) or comparison.get("status") not in ("RENDERED", "MISSING"):
            errors.append("design exploration visual comparison status invalid")
        else:
            frames = comparison.get("frames", [])
            if not isinstance(frames, list):
                errors.append("design exploration visual frames must be a list")
            elif comparison["status"] == "MISSING" and frames:
                errors.append("missing visual comparison cannot claim frames")
            elif comparison["status"] == "RENDERED":
                if len(frames) != len(directions):
                    errors.append("rendered comparison frames must match presented directions")
                frame_ids = []
                evidence_ids = []
                for i, frame in enumerate(frames):
                    if not isinstance(frame, dict) or not isinstance(frame.get("direction_id"), str):
                        errors.append(f"visual frame {i}: invalid")
                        continue
                    frame_ids.append(frame["direction_id"])
                    if not isinstance(frame.get("evidence_id"), str) or not frame["evidence_id"].strip():
                        errors.append(f"visual frame {i}: missing evidence reference")
                    else:
                        evidence_ids.append(frame["evidence_id"])
                if (set(frame_ids) != ids or len(set(frame_ids)) != len(frame_ids)
                        or len(set(evidence_ids)) != len(evidence_ids)):
                    errors.append("visual comparison frame directions/evidence inconsistent")
    return errors


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
    # Visual creativity belongs to the task, user and upstream skills. These
    # declarations only check consistency of *claimed* exploration and evidence.
    exploration = report.get("design_exploration")
    if report.get("design_exploration_required") is True and exploration is None:
        errors.append("explicitly requested design exploration is missing")
    if exploration is not None:
        errors.extend(validate_exploration(exploration))
        if isinstance(exploration, dict):
            comparison = exploration.get("visual_comparison")
            if isinstance(comparison, dict) and comparison.get("status") == "RENDERED":
                rendered_ids = {row.get("id") for row in ledger if isinstance(row, dict)
                                and row.get("status") == "RENDERED"}
                for frame in comparison.get("frames", []) if isinstance(comparison.get("frames"), list) else []:
                    if isinstance(frame, dict) and frame.get("evidence_id") not in rendered_ids:
                        errors.append("visual frame missing rendered evidence")
    quality = report.get("design_quality")
    if quality is not None:
        if not isinstance(quality, dict):
            errors.append("design_quality must be a declaration object")
        else:
            risks = quality.get("generic_template_risks", [])
            if (not isinstance(risks, list) or any(
                    not isinstance(x, str) or not x.strip() for x in risks)):
                errors.append("optional template observations must be nonempty strings")
            source_status = quality.get("impeccable_source_status")
            if source_status is not None and source_status not in SOURCES:
                errors.append("design quality Impeccable source status invalid")
    if mode == "create-design" and report["gate"] == "AUDIT_COMPLETE":
        errors.append("new design cannot claim completed UI audit")
    if mode == "create-design" or report.get("design_exploration_required") is True:
        if report["gate"] == "AWAITING_VISUAL_APPROVAL":
            finals = proposal.get("artifact_refs") if isinstance(proposal, dict) else None
            if (not isinstance(proposal, dict) or proposal.get("visual_status") != "RENDERED"
                    or not isinstance(finals, list) or not finals
                    or any(not isinstance(x, str) or not x.strip() for x in finals)):
                errors.append("visual review requires actual referenced design previews")
    errors.extend(validate_visual_lineage(report))
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
