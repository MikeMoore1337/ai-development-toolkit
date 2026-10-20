# Workflow and reuse-first matrix

| Need | Existing responsibility | Gap addressed here | Decision |
| --- | --- | --- | --- |
| Discovery, research sourcing, PRD | product-discovery / research-verification | UX task hypotheses and design implications | REUSE + REFINE |
| Business rules and use cases | business-system-analysis | Journey mapping and screen decisions | REUSE + REFINE |
| User flows, IA, wireframes, prototype | No single cross-stage design contract | Traceable, navigable interaction plan | NEW orchestration guidance, not controller |
| Visual direction and design system | design-system-consistency | Choosing when and what to delegate | REUSE |
| Motion | motion-quality | Connect to prototype states only | REUSE |
| Screenshot comparison | screenshot-fidelity | Handoff reference conditions | REUSE |
| Component API and architecture | component-architecture | Stack-neutral design contract | REUSE + REFINE |
| Forms/validation | forms-validation | Capture states before implementation | REUSE |
| Browser/responsive/QA | playwright-testing, e2e-testing, qa-strategy | Evidence/acceptance mapping | REUSE |
| Implementation | implementation / feature-delivery / make-feature | No auto-implementation | DELEGATE |
| Developer handoff | scattered source contracts | One traceable UX/UI package | NEW contract |

## 4 inputs

- **System contract:** preserve all original R/AC/SR/UC/BR identifiers and inherit confirmed errors, NFRs, constraints. Do not guess behavior.
- **PRD only:** map original R/AC, mark any inferred rule or new UC as ASSUMPTION, and request system analysis when critical rules block correctness.
- **Idea only:** make a small proposed structure with explicit local identifiers, source labels and testable hypotheses; no PRD or Figma prerequisite.
- **Existing app:** inspect real files/screens and state before assessment; absent inspection = NOT_TESTED, not a visual audit. Existing approved brand prevails.

## Lifecycle

1. Research notes: actor, task, context, evidence/source, falsifiable hypothesis and honest testing status.
2. Traceable flow: start node, actions, branches, error and recovery paths; each required outcome must be reachable.
3. Information architecture: minimal sections and permission-aware navigation where needed; each flow enters a real screen.
4. Wireframes: screen regions, priority, controls, states, language/zoom/keyboard/safe-area considerations.
5. Prototype: low/mid/high is detail; INTERACTIVE only after real working interactions. Record component, event, from/to/error, destination, accessibility, AC and artifact evidence.
6. Visual: reuse existing tokens and family of icons; record alternatives and open approval decisions; do not call a prose plan RENDERED.
7. Developer handoff: exact links source R -> UC -> FLOW -> SCREEN -> COMPONENT -> AC, assets (real or absent), design decisions, responsive, accessibility, QA cases, status and unresolved assumptions.
8. Design QA: when an implementation exists, compare same viewport and state, real screenshots/interaction and keyboard behavior. Evidence-gated: SOURCE_VALIDATED, CONTRACT_VALIDATED, RENDERED, INTERACTION_TESTED, VISUAL_REVIEWED, OWNER_ACCEPTED, IMPLEMENTED, RUNTIME_VERIFIED are independent milestones, not an automatic ladder.

## Conditional design-quality review

- Form a minimal brief before visuals: stable product truth, goal, user context, source constraints and acceptance oracle separately from proposed visual choices.
- Only when a material design trade-off exists, compare alternatives that differ in navigation, hierarchy, density or interaction. Do not require a prototype switcher, a new design-system, or automatic root files.
- For technical readiness, challenge the real data interface with domain-plausible extreme values, missing properties, localization/long text, permission errors, network/race failures and mobile touch/keyboard constraints.
- Evaluate qualitative critique, objective technical failures and visual consistency separately. State what was actually reviewed versus planned. Evidence from code inspection is not evidence of observed device behavior.
- Use [review/stress scenarios](REVIEW_AND_STRESS.md) and [upstream adoption decisions](INSPIRATION_REVIEW.md) as optional references. Do not add their vendors, generated assets, dependencies or execution environments.

## Failure recovery

- No source => DRAFT_WITH_GAPS, not SOURCE_VALIDATED.
- No output artifact => TEXT_SPEC and PREPARED/NOT_TESTED, not RENDERED.
- Static screenshot => STATIC_RENDER only, not INTERACTIVE_VERIFIED.
- Missing Figma => provide Markdown/Mermaid screen flows and contracts, no account requirement.
- Unreachable flow or missing error handling => BLOCKED for handoff, repair flow first.
- Unknown responsive breakpoints => specify representative test widths as proposals, not verified behavior.
- Missing approved tokens/assets => retain UNKNOWN; do not invent a design baseline.
- Before real change, respect owner visual-approval and deployment gates. Never create generated files in Toolkit copies.
