# Workflow: source -> analysis -> engineering/QA

## Reuse-first decision

| Capability | Owner / reusable Skill | Analysis addition |
| --- | --- | --- |
| PRD, MVP scope | product-discovery | Preserve R-ID, AC-ID, scope |
| Delivery tasks, blockers | project-delivery-management | Link task-to-R/AC, never fake task status |
| Acceptance testability | requirement-analysis | Refine behavior and identify unresolved rules |
| Test execution trace | requirements-traceability | Supply product-to-system mapping, not QA executions |
| API schema and evolution | api-design | Describe integration need, or CONTRACT_PENDING |
| Consumer contract validation | contract-testing | Record test need, not fake evidence |
| Architecture ADR | architecture-decisions | Keep small analytical decision log |
| Stakeholder goals, BR, UC, process, domain, NFR | business-system-analysis | New, bounded analysis |

## Four input routes

- PRD: respect original IDs, goals, constraints and decisions.
- PRD + Delivery Plan: cross-check task scope and AC, log competing sources when inconsistent.
- Natural-language goal: small draft with clearly identified ASSUMPTION/UNKNOWN; do not block on a formal PRD.
- Existing code/project: inspect and separately mark OBSERVED versus REQUIRED and PROPOSED; never assert source presence without inspection.

## Output

Compact: problem, users, a few scenarios/rules, R -> SR -> AC, relevant NFR, uncertainties and handoff.

Full: stakeholder needs; start/decision/error/end process; UC happy and failure paths; BR invariant; domain bounded entities; SR; selective NFR; integration provider/consumer/data/error semantics; decisions; unresolved conflicts; traceability and UX/UI, Backend, Frontend, QA handoffs. Text process diagrams are **not verified BPMN 2.0**.

For a textual process: start -> user enters expense -> validate sum? -> (valid: store -> update totals -> end) / (invalid: show rejection -> no mutation -> end); cancellation must have an explicit end path when relevant.

## Checks and caveats

Before handoff: all sourced R have AC or an open acceptance gap; every SR references its parent R; BR/UC/trace references exist; critical UC has an alternative or error path; conflicts retain both origin sources; proposed NFR has a proposed measurement; missing integration format remains CONTRACT_PENDING. Use QA requirements-traceability for actual test implementation and execution status.

An optional local read-only command is available for an authorized JSON document **outside** Toolkit:

    python scripts/validate_system_spec.py /path/to/spec.json

The script cannot check genuine user interviews, independently verify real business rules, authenticate GitHub actions or prove that an AI client activated this skill.
