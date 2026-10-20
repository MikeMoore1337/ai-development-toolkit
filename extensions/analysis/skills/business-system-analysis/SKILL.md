---
name: business-system-analysis
description: "Translate a PRD, stakeholder needs or plain product request into business rules, use cases, domain boundaries, measurable system requirements, NFRs and acceptance traceability. Use for business/system specifications and contradictions, not bug fixing, UI design, API implementation or unit tests."
metadata:
  pack: "analysis"
  version: "1.0.0"
---

# Business & System Analysis

**Positive triggers:** "Turn this PRD into system requirements"; "Identify business rules"; "Describe use cases and process states"; "Find contradictory requirements"; "Write a system specification"; "Trace acceptance criteria back to product needs".

**Negative triggers:** fix Python bugs, write unit tests, implement an API, design the UI, deploy an app, or merely edit prose. Use engineering, QA, UX, editorial or release skills instead. A combined analyse-and-implement request belongs to the existing feature controller; this skill only supplies analytical input and is **not** a workflow controller.

## Inputs and truth labels

Accept (A) PRD, (B) PRD plus Delivery Plan, (C) ordinary-language idea, or (D) existing project code and documentation. Neither a PRD nor GitHub URL is mandatory. Preserve existing original R-ID, AC-ID, goals, inclusions/exclusions, decisions, dependencies and constraints. Never silently renumber; link refinements by parent R-ID. In case of conflicting PRD and plan, log both sources and request the owner's decision rather than assuming precedence.

For existing projects distinguish REQUIRED, OBSERVED (from inspected implementation), PROPOSED and UNKNOWN; proposed behavior is not already implemented. Use source labels USER_PROVIDED, SOURCE_BACKED, OBSERVED, ASSUMPTION or UNKNOWN; label assumptions conspicuously. Do not claim interviews, system behavior, verified dependencies or approvals without evidence.

## Procedure

1. **Reuse before adding process.** Product Discovery owns problem, hypotheses and PRD. Project Delivery Management owns task dependencies, progress and approvals. Reuse task-scoping for boundaries, QA requirement-analysis for testability, QA requirements-traceability for test-to-execution links, architecture-decisions for architectural ADRs, backend api-design for exact HTTP/RPC/event contracts, and contract-testing for consumer verification. Do not clone these systems.
2. **Stakeholders and scope.** Identify only relevant actual or hypothetical actors, their goals, sources, constraints and decision owners if known. Map goals to source R-ID/AC-ID. Explicitly list MVP inclusions, exclusions and unverified dependencies.
3. **Rules and scenarios.** Describe each business rule by stable BR-ID, applicability, exceptions, violation and observable reaction, linked to R-ID and AC-ID and labelled CONFIRMED / ASSUMPTION / UNRESOLVED. Never invent refunds, authorization, financial behavior or policy defaults. For each critical UC-ID include actor, goal, preconditions, main path, alternative/error path, observable result and check.
4. **Processes and domain.** Model start, actors, actions, decision branches, errors/cancellation and end. Text, Markdown or Mermaid flowchart is sufficient; do not call a generic flowchart validated BPMN 2.0. Identify entities, relationships, lifecycle, ownership if known, invariants and bounded responsibilities; a domain model is not a physical database schema.
5. **System requirements.** Refine sourced R-ID into SR-ID preserving its parent. Include preconditions, inputs, output, errors, related rules/UCs and original ACs. Use CONFIRMED, PROPOSED, UNKNOWN honestly. Detect requirements without sources/AC, inconsistent rules, duplicated meanings, scope expansion and untestable behavior.
6. **Selective NFRs and integration needs.** Only include applicable categories; specify condition, metric and verification method, or mark UNKNOWN. Never fabricate latency, SLA or real performance. For integrations record provider, consumer, data, error paths, security, compatibility, provenance; exact API unknown means CONTRACT_PENDING. api-design owns concrete endpoints.
7. **Trace and hand off.** Build Product goal -> original R-ID -> BR/UC -> SR -> needed interface/data -> original AC-ID -> planned test -> execution evidence. Test design, execution and PASS are distinct: defer to requirements-traceability rather than creating a second QA registry. Resolve no decision silently: use PROPOSED/APPROVED/REJECTED/UNRESOLVED and require evidence to claim APPROVED. Pass user journeys/states/errors to UX/UI; invariants/data to Backend; validation/states to Frontend; R/AC/rules/UC/NFR and missing coverage to QA. A handoff is not implementation or acceptance.

## Output size and recovery

For a simple idea, return a compact MVP specification: goal, real/hypothetical users, a few core use cases/rules, requirements, selective NFR, original or locally assigned R/AC identifiers, open decisions and next handoff. For a complex system use the full typed [System Specification Contract](references/SYSTEM_SPEC_CONTRACT.json), with references, process models, domain boundaries, integration needs, conflict log, decision log and traceability. See [workflow and reuse table](references/WORKFLOW.md), [synthetic R1-R3 example](references/EXAMPLES.md) and [negative manual acceptance](references/MANUAL_ACCEPTANCE.md).

On missing PRD return DRAFT_WITH_GAPS, on unknown interface CONTRACT_PENDING, unverified external service UNVERIFIED_DEPENDENCY, on contradiction UNRESOLVED_CONFLICT with both sources, and on scope creep PROPOSED_OUT_OF_SCOPE. Never make up metrics or mark a test PASS without verifiable execution evidence. The optional offline validator (scripts/validate_system_spec.py) checks structural links/statuses, not semantic truth, live implementation, CI authenticity or AI-client activation.

**Storage boundary:** All copies of Toolkit are strictly read-only when used on another project. Return user-specific specifications **in chat by default**; create files in the user's target project or external destination only with explicit authorization. Never write generated user files, diagrams, logs, caches or tests into Toolkit. Real-client skill discovery and activation remain NOT_MEASURED without separate real-client trials. No paid API, BPMN engine, runtime service or mandatory framework is required.
