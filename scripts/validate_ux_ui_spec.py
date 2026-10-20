#!/usr/bin/env python3
"""Issue #56: read-only structural UX/UI contract validation.

Checks relationships and evidence claims, not aesthetics, real usability,
browser/device behavior, AI-client activation, or WCAG conformance.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads((ROOT / "extensions/design/skills/ux-design-process"
                       "/references/UX_UI_CONTRACT.json").read_text(encoding="utf-8"))
LABELS = set(CONTRACT["source_labels"])
CHECKED = {"AUTO_CHECKED", "MANUALLY_CHECKED", "ASSISTIVE_TECH_CHECKED"}


def _objects(document: dict, section: str, errors: list[str]) -> dict[str, dict]:
    rows = document.get(section)
    found: dict[str, dict] = {}
    if not isinstance(rows, list):
        errors.append(f"{section}: expected list")
        return found
    required = CONTRACT["required_fields"].get(section, [])
    for index, row in enumerate(rows):
        context = f"{section}[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{context}: expected object")
            continue
        if missing := set(required) - set(row):
            errors.append(f"{context}: missing {sorted(missing)}")
            continue
        ident = row.get("screen_id" if section in {"wireframes", "responsive"} else
                        "requirement_id" if section == "traceability" else "id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"{context}: missing ID")
        elif ident in found:
            errors.append(f"{section}: duplicate ID {ident}")
        else:
            found[ident] = row
    return found


def _refs(row: dict, field: str, valid: set[str],
          context: str, errors: list[str], *, nonempty: bool = True) -> None:
    value = row.get(field)
    if (not isinstance(value, list) or (nonempty and not value)
            or any(not isinstance(v, str) or v not in valid for v in value)
            or len(value) != len(set(value))):
        errors.append(f"{context}: invalid {field} references")


def _text(row: dict, field: str, context: str, errors: list[str]) -> None:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{context}: missing {field}")


def _flow_path(flow: dict, screens: set[str], errors: list[str]) -> None:
    context = f"flow {flow.get('id')}"
    nodes = flow.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append(f"{context}: missing nodes")
        return
    node_map: dict[str, dict] = {}
    for node in nodes:
        if not isinstance(node, dict):
            errors.append(f"{context}: invalid node")
            continue
        ident = node.get("id")
        if not isinstance(ident, str) or not ident or ident in node_map:
            errors.append(f"{context}: duplicate or missing node ID")
            continue
        node_map[ident] = node
        if node.get("screen_id") not in screens:
            errors.append(f"{context}: missing screen for node {ident}")
        _text(node, "action", context, errors)
        if not isinstance(node.get("next"), list):
            errors.append(f"{context}: missing next list for {ident}")
    start = flow.get("start_node")
    ends = flow.get("end_nodes")
    bad = flow.get("error_nodes")
    if (start not in node_map or not isinstance(ends, list) or not ends
            or any(e not in node_map for e in ends)):
        errors.append(f"{context}: invalid start/end nodes")
        return
    if not isinstance(bad, list) or any(e not in node_map for e in bad):
        errors.append(f"{context}: invalid error_nodes")
        return
    edges: dict[str, list[str]] = {}
    for ident, node in node_map.items():
        neighbors = node.get("next", [])
        if not isinstance(neighbors, list) or any(n not in node_map for n in neighbors):
            errors.append(f"{context}: dangling transition from {ident}")
            return
        edges[ident] = neighbors
    reachable = {start}
    pending = [start]
    while pending:
        for nxt in edges[pending.pop()]:
            if nxt not in reachable:
                reachable.add(nxt)
                pending.append(nxt)
    if not set(ends) <= reachable:
        errors.append(f"{context}: unreachable end state")
    if not set(bad) <= reachable:
        errors.append(f"{context}: unreachable error state")
    can_finish = set(ends)
    while True:
        extra = {ident for ident, neighbors in edges.items()
                 if ident not in can_finish and any(n in can_finish for n in neighbors)}
        if not extra:
            break
        can_finish.update(extra)
    if any(ident not in can_finish for ident in reachable):
        errors.append(f"{context}: node without path to terminal state")
    if any(edges[e] for e in ends):
        errors.append(f"{context}: end state has outgoing transitions")
    if bad and not isinstance(flow.get("recovery"), str):
        errors.append(f"{context}: error path without recovery")


def validate(document: object) -> list[str]:
    """Deterministically validate schema, references, reachable outcomes and evidence."""
    errors: list[str] = []
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        return ["Expected UX/UI schema_version=1 object"]
    if (document.get("document_type") != CONTRACT["document_type"]
            or document.get("artifact_status") != CONTRACT["artifact_status"]):
        errors.append("Invalid document_type or artifact_status: design is not implemented UI")
    missing = set(CONTRACT["required_sections"]) - set(document)
    if missing:
        errors.append(f"Missing sections {sorted(missing)}")
        return errors
    _text(document, "goal", "document", errors)
    r = _objects(document, "source_requirements", errors)
    ac = _objects(document, "acceptance_criteria", errors)
    uc = _objects(document, "use_cases", errors)
    flows = _objects(document, "flows", errors)
    screens = _objects(document, "screens", errors)
    frames = _objects(document, "wireframes", errors)
    components = _objects(document, "components", errors)
    responsive = _objects(document, "responsive", errors)
    a11y = _objects(document, "accessibility", errors)
    traces = _objects(document, "traceability", errors)
    if not r or not ac or not uc or not flows or not screens or not components or not traces:
        errors.append("Incomplete source / journey / component / traceability inventory")
    for ident, item in r.items():
        if item.get("source") not in LABELS:
            errors.append(f"requirement {ident}: invalid source")
        _text(item, "behavior", f"requirement {ident}", errors)
    for ident, item in ac.items():
        _refs(item, "requirement_ids", set(r), f"AC {ident}", errors)
    for ident, item in uc.items():
        _refs(item, "requirement_ids", set(r), f"UC {ident}", errors)
        _refs(item, "acceptance_ids", set(ac), f"UC {ident}", errors)
    for ident, item in flows.items():
        context = f"flow {ident}"
        for field, allowed in (("requirement_ids", r), ("acceptance_ids", ac),
                               ("use_case_ids", uc)):
            _refs(item, field, set(allowed), context, errors)
        for uc_id in item.get("use_case_ids", []):
            if uc_id in uc and not set(item.get("requirement_ids", [])) <= set(uc[uc_id].get("requirement_ids", [])):
                errors.append(f"{context}: broken UC-to-R mapping")
        _flow_path(item, set(screens), errors)
        _text(item, "verification", context, errors)
    ia = document["information_architecture"]
    if not isinstance(ia, dict) or not isinstance(ia.get("sections"), list):
        errors.append("information_architecture: missing sections")
    elif not isinstance(ia.get("navigation"), list):
        errors.append("information_architecture: missing navigation")
    else:
        for route in ia["navigation"]:
            if not isinstance(route, dict) or route.get("from") not in screens or route.get("to") not in screens:
                errors.append("information_architecture: invalid navigation route")
    for ident, item in screens.items():
        _text(item, "goal", f"screen {ident}", errors)
        for field, allowed in (("flow_ids", flows), ("requirement_ids", r),
                               ("actions", components)):
            _refs(item, field, set(allowed), f"screen {ident}", errors)
        if not isinstance(item.get("states"), list) or not item["states"]:
            errors.append(f"screen {ident}: missing UI states")
        if ident not in frames:
            errors.append(f"screen {ident}: missing wireframe")
        if ident not in responsive:
            errors.append(f"screen {ident}: missing responsive contract")
    for ident, item in frames.items():
        if ident not in screens or item.get("representation") not in {"TEXT_SPEC", "ASCII", "MERMAID", "STATIC_RENDER", "FIGMA"}:
            errors.append(f"wireframe {ident}: invalid screen/representation")
        if not item.get("regions"):
            errors.append(f"wireframe {ident}: missing regions")
    for ident, item in components.items():
        for field, allowed in (("screen_ids", screens), ("requirement_ids", r),
                               ("acceptance_ids", ac)):
            _refs(item, field, set(allowed), f"component {ident}", errors)
        for field in ("states", "actions", "outputs", "accessibility", "responsive"):
            if not item.get(field):
                errors.append(f"component {ident}: missing {field}/interaction outcome")
        for field in ("variants", "inputs", "validation", "error_states",
                      "loading_states", "empty_states", "disabled_states"):
            if not isinstance(item.get(field), list):
                errors.append(f"component {ident}: invalid {field}")
    for ident, item in responsive.items():
        if ident not in screens:
            errors.append(f"responsive {ident}: unknown screen")
        if not isinstance(item.get("viewports"), list) or not item["viewports"]:
            errors.append(f"responsive {ident}: no viewports")
            continue
        for viewport in item["viewports"]:
            if not isinstance(viewport, dict) or not isinstance(viewport.get("width"), int) or viewport["width"] <= 0:
                errors.append(f"responsive {ident}: invalid width")
                continue
            if viewport.get("tested") is True and not viewport.get("evidence"):
                errors.append(f"responsive {ident}: unverified responsive claim")
        for field in ("navigation", "overflow", "long_text", "forms",
                      "empty_error_states", "verification"):
            _text(item, field, f"responsive {ident}", errors)
    for ident, item in a11y.items():
        _refs(item, "screen_ids", set(screens), f"accessibility {ident}", errors)
        if item.get("status") not in CONTRACT["a11y_statuses"]:
            errors.append(f"accessibility {ident}: invalid status")
        if item.get("status") in CHECKED and not item.get("evidence"):
            errors.append(f"accessibility {ident}: WCAG/accessibility claimed without evidence")
        _text(item, "criterion", f"accessibility {ident}", errors)
    research = document["research"]
    if not isinstance(research, dict) or not isinstance(research.get("sources"), list):
        errors.append("research: missing sources")
    else:
        for source in research["sources"]:
            if not isinstance(source, dict) or source.get("type") not in LABELS:
                errors.append("research: invalid source label")
            elif source["type"] == "OBSERVED" and not source.get("evidence"):
                errors.append("research: invented observed findings")
        hypotheses = research.get("hypotheses")
        if not isinstance(hypotheses, list):
            errors.append("research: missing hypotheses")
        else:
            for h in hypotheses:
                if not isinstance(h, dict) or any(not h.get(k) for k in
                        ("id", "claim", "setup", "success", "disproof", "tool", "status")):
                    errors.append("research: incomplete hypothesis")
                elif h["status"] not in {"NOT_TESTED", "TESTED", "BLOCKED"}:
                    errors.append("research: invalid hypothesis status")
                elif h["status"] == "TESTED" and not h.get("evidence"):
                    errors.append("research: unverified usability hypothesis")
    prototype = document["prototype"]
    if not isinstance(prototype, dict):
        errors.append("prototype: expected object")
    else:
        level, status, kind = (prototype.get(k) for k in ("level", "status", "artifact_kind"))
        if level not in CONTRACT["prototype_levels"] or status not in CONTRACT["prototype_statuses"]:
            errors.append("prototype: invalid level/status")
        if kind not in {"TEXT_SPEC", "STATIC_RENDER", "INTERACTIVE_PROTOTYPE"}:
            errors.append("prototype: invalid artifact kind")
        if status in {"RENDERED", "INTERACTIVE_VERIFIED"} and not (
                prototype.get("artifact_ref") and prototype.get("evidence")):
            errors.append("prototype: claimed verified output without artifact/evidence")
        if status == "INTERACTIVE_VERIFIED" and (kind != "INTERACTIVE_PROTOTYPE" or level != "INTERACTIVE"):
            errors.append("prototype: static PNG/text claimed interactive")
        for action in prototype.get("interactions", []):
            if not isinstance(action, dict) or action.get("component_id") not in components or action.get("target_screen") not in screens:
                errors.append("prototype: invalid interaction links")
            elif (not action.get("action") or not action.get("to_state")
                  or not action.get("error_state") or not action.get("accessibility")):
                errors.append("prototype: interaction missing state/behavior")
            else:
                _refs(action, "acceptance_ids", set(ac), "prototype interaction", errors)
    visual = document["visual_design"]
    if not isinstance(visual, dict) or visual.get("source") not in LABELS:
        errors.append("visual_design: source missing")
    elif visual.get("approval") == "OWNER_ACCEPTED" and not visual.get("approval_evidence"):
        errors.append("visual_design: owner acceptance unverified")
    tokens = document["design_tokens"]
    if not isinstance(tokens, dict) or tokens.get("strategy") not in {"REUSE_IF_EXISTING", "REUSE_EXISTING", "PROPOSE_MINIMAL"}:
        errors.append("design_tokens: missing reuse strategy")
    handoff = document["handoff"]
    if not isinstance(handoff, dict) or handoff.get("implementation_status") not in {"NOT_IMPLEMENTED", "IMPLEMENTED_VERIFIED"}:
        errors.append("handoff: missing implementation status")
    elif handoff["implementation_status"] == "IMPLEMENTED_VERIFIED" and not handoff.get("implementation_evidence"):
        errors.append("handoff: design claimed implemented UI without code evidence")
    for ident, item in traces.items():
        if ident not in r:
            errors.append(f"trace {ident}: unknown requirement")
        for field, allowed in (("acceptance_ids", ac), ("use_case_ids", uc),
                               ("flow_ids", flows), ("screen_ids", screens),
                               ("component_ids", components)):
            _refs(item, field, set(allowed), f"trace {ident}", errors)
        for field in ("acceptance_ids", "use_case_ids", "flow_ids", "screen_ids", "component_ids"):
            for link in item.get(field, []):
                target = {"acceptance_ids": ac, "use_case_ids": uc,
                          "flow_ids": flows, "screen_ids": screens,
                          "component_ids": components}[field].get(link)
                if target and ident not in target.get("requirement_ids", []):
                    errors.append(f"trace {ident}: broken R-to-{field} link {link}")
        _text(item, "verification", f"trace {ident}", errors)
    if set(r) != set(traces):
        errors.append("traceability: source R-ID coverage missing or extra")
    covered_ac = {key for row in traces.values() for key in row.get("acceptance_ids", [])}
    if set(ac) != covered_ac:
        errors.append("traceability: AC-ID coverage missing or extra")
    if not isinstance(document["open_decisions"], list):
        errors.append("open_decisions: expected list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSON UX/UI specification to check without modifications")
    args = parser.parse_args()
    try:
        data = json.loads(args.source.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"FAIL: could not read JSON: {type(exc).__name__}")
        return 2
    errors = validate(data)
    for item in errors:
        print("FAIL: " + item)
    print("PASS: UX/UI structural references (NOT a visual/browser/accessibility test)"
          if not errors else f"FAIL: {len(errors)} UX/UI issues")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
