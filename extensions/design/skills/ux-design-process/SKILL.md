---
name: ux-design-process
description: "Plan user journeys, information architecture, wireframes, prototype behavior and design handoff from an idea, PRD or system specification. Use for UX/UI planning and design-to-developer contracts; not for isolated screenshot comparison, animation fixes or implementing frontend code."
metadata:
  pack: "design"
  version: "1.0.0"
---

# UX/UI design process

**Positive triggers:** "Plan UX flows"; "Design screens and navigation"; "Prepare wireframes"; "Define prototype interactions"; "Make a design handoff"; "Plan responsive UI from requirements"; "Спроектируй UX/UI приложения".

**Negative triggers:** Python fixes, backend APIs, unit tests, production deployment, screenshot-only parity checks (`screenshot-fidelity`), animation-only optimization (`motion-quality`), or direct feature implementation (existing feature controller). Do not replace `make-feature` or `feature-delivery` and never activate competing controllers.

## Inputs and evidence

Accept (A) system specification, (B) PRD without system analysis, (C) natural-language idea, or (D) existing application. Preserve all original R-ID, AC-ID, SR-ID, UC-ID and BR-ID exactly; do not invent source requirements or renumber IDs. Read linked artifacts only if available. Label every research claim USER_PROVIDED, SOURCE_BACKED, OBSERVED, ASSUMPTION or UNKNOWN. An idea without research yields hypotheses, not invented interviews, usability tests, analytics or heatmaps. Unknown rules, permissions, data or error states are open decisions, not confirmed features. An unavailable app cannot be visually audited by imagination.

## Workflow and boundaries

1. **Reuse-first audit.** Inspect the product's actual existing screens, tokens, components, responsive patterns, brand and approvals where available. Prefer `product-discovery` for PRD and `business-system-analysis` for domain/system behavior; their output feeds this skill. See [workflow, reuse matrix and recovery](references/WORKFLOW.md).
2. **Research and hypotheses.** Define user goal, actor, context, entry, expected observable completion, obstacles and alternate/error outcomes. Each falsifiable hypothesis states setup, success evidence, disproof, tool and actual verification status. No interview or observation is claimed without a source.
3. **Flows and information architecture.** Map each source UC/R/AC to actor-focused flow with start, actions, alternate and error/recovery path and reachable end state. Supply navigation/screen inventory using the fewest justified screens. Markdown and Mermaid are optional; neither is proof of an interactive UI.
4. **Wireframes and prototype contract.** For every screen describe regions, hierarchy, actions, states, navigation and mobile behavior; low/mid/high fidelity labels describe scope only. For each interaction define action, from/to/error states, destination, accessibility and AC. Mark TEXT_SPEC, STATIC_RENDER, INTERACTIVE_PROTOTYPE or IMPLEMENTED_UI based on actual evidence, not appearance.
5. **Visual direction and alternative selection.** Keep durable product facts separate from design proposals. Where a substantial design decision is open, compare a small number of variants that differ in navigation, hierarchy, density or interaction model; never produce cosmetic variants just to fill a quota. Preserve existing brand and design tokens. Record proposed typography, hierarchy, spacing, icons, colors, grids, focus, contrast, safe-area and motion decisions. Call `design-system-consistency` for token consistency and `motion-quality` only for substantive animation work. No universal theme, fonts, framework, breakpoints or Liquid Glass.
6. **Component and responsive contracts.** Before promising readiness, propose realistic boundary fixtures: empty/missing data, long but plausible localized strings, invalid input, permissions and network errors, double-submit, high density, mobile keyboard and safe areas. Use the real component input boundary; never report synthetic cases as executed. Handoff to `component-architecture` for component boundaries and real implementation. Specify inputs, outputs, variants, loading/error/empty/disabled states, keyboard/assistive technology and representative viewports. Reuse existing CSS variables/tokens, no duplicate token registry. WCAG 2.2 is a reference for applicable web accessibility criteria, not a blanket compliance certificate.
7. **Handoff and Design QA.** Separate task-clarity critique, technical interaction/accessibility checks and visual consistency review; describe severity, evidence and NOT_TESTED outcomes independently. Follow [design review and stress checks](references/REVIEW_AND_STRESS.md) for optional deep review, and [source adoption/rationale](references/INSPIRATION_REVIEW.md) for provenance and deliberate exclusions. Provide requirement source, flows, reachable screens, optional actual assets, interaction outcomes, tokens, component contracts, responsive and accessibility checks, open decisions and original R/AC/UC/SR/BR links. Use `screenshot-fidelity` and `playwright-testing` for relevant actual implementation comparisons. A render must really exist before RENDERED; an interactive status needs actual interaction evidence. Do not claim pixel-perfect, accessible, 60 FPS, responsive, accepted or deployed without corresponding checks.

## Output and review

For a novice give a concise screen/flow/design proposal in chat without requiring Figma, terminal, wireframe jargon or API keys. For a professional produce a traceable [UX/UI contract](references/UX_UI_CONTRACT.json); use the [synthetic home-expenses example](references/EXAMPLE_EXPENSES.json), [multi-role workflow example](references/EXAMPLE_WORKFLOWS.json), and [manual acceptance checklist](references/MANUAL_ACCEPTANCE.md). The optional read-only `scripts/validate_ux_ui_spec.py` checks structure and references, not attractiveness, usability outcomes or WCAG conformance. Unavailable render/browser/device means NOT_TESTED. Owner approval is never inferred.

**Storage:** All copies of Toolkit used as instructions for another project are read-only. Return designs, diagrams, reports and prototypes **in chat by default**; save in a user's project or explicit external destination only when authorized. Never write another user's artifacts, logs, screenshots or caches into Toolkit. Optional Figma/browser tools require existing access and permission; do not require Figma, a paid API, installation, or a background runtime. Real client activation remains NOT_MEASURED until observed.
