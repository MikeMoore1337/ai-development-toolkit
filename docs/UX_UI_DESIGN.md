# UX/UI Design - from requirements to developer handoff

[Русская версия](ru/UX_UI_DESIGN.md)

**UX** describes what the user needs to do and whether a journey makes sense; **UI** describes the visible interface and its states. A **wireframe** is a structural sketch, not a reviewed visual design; a beautiful static mockup is not working frontend code. An **interactive prototype** needs functioning actions and real interaction tests.

## Start without technical vocabulary

> Plan an app for household expenses. I need to add entries, see totals and edit or delete them. Describe the screens, navigation and errors first. Do not implement code yet.

An ordinary idea is enough. Use the optional `ux-design` profile with a capable AI client or reference Toolkit in a chat. Figma, terminal commands, paid APIs and a chosen frontend framework are not requirements. Default output is in chat.

## Design journey

1. **Source:** accept a system specification, PRD, plain idea or inspected existing app. Preserve existing R-ID/AC-ID/SR-ID/UC-ID/BR-ID and source labels. Do not invent research or unconfirmed business rules.
2. **Research:** record user task, role, context, entry, obstacles, alternatives, expected result. Hypotheses state setup, success, disproof and verification status; untested means NOT_TESTED.
3. **Flows:** actor actions from entry through choices, errors, recovery and reachable terminal outcomes. Markdown or optional Mermaid works without external rendering.
4. **Information architecture:** justify the fewest screens and map each mandatory action to a reachable role-permitted route.
5. **Wireframes:** record zones, content order, controls, navigation and empty/loading/error states. Text-only output is TEXT_SPEC, not a rendered image.
6. **Prototype:** describe each actionable component's event, initial/result/error state, transition, accessibility and acceptance criterion. Only claim INTERACTIVE_VERIFIED when actual interactions are tested.
7. **Visual design and design system:** existing brand, tokens, fonts, spacing and icons take priority. Use `design-system-consistency`; add minimal tokens only when justified, never a second independent source. Defer motion-specific questions to `motion-quality`.
8. **Component contracts:** stack-neutral inputs, events, variants, validation, disabled/loading/empty/error states, responsive and accessibility constraints. `component-architecture` owns engineering boundaries.
9. **Developer handoff and QA:** source requirements, screens/flows, actual assets if any, design decisions, component contracts, responsive/accessibility criteria, traceability and unresolved questions. For actual implementations use `screenshot-fidelity` and appropriate browser/QA testing. Matching screenshots alone do not prove behavior.

Trace example: `R1 -> UC1 -> FLOW-1 -> SCREEN-2 -> COMP-FORM -> AC1/AC2`. The [expense journal](../extensions/design/skills/ux-design-process/references/EXAMPLE_EXPENSES.json) and [role-aware work console](../extensions/design/skills/ux-design-process/references/EXAMPLE_WORKFLOWS.json) are synthetic design specifications, not implemented or visually verified applications.

## Additional review from three independent sources

Toolkit adopts **methods, not third-party installations**: clarify the product goal before visual choices, run a realistic data/error stress pass on actual UI inputs, compare genuinely different interaction patterns when a design decision is open, and keep critique separate from measured technical checks. Existing design tokens always take priority over another project's look.

Read the [original review/stress checklist](../extensions/design/skills/ux-design-process/references/REVIEW_AND_STRESS.md) for optional concrete cases (long localized text, zero/one/large values, missing records, authorization, offline, duplicate submit, dynamic viewport and keyboard). The [source assessment](../extensions/design/skills/ux-design-process/references/INSPIRATION_REVIEW.md) records the exact upstream revisions, licenses and what was intentionally excluded. No Impeccable binary, third-party skill pack or design-style database is bundled.

## Responsive and accessibility evidence

For each important screen propose representative mobile/desktop viewports (tablet when relevant), focus and keyboard access, zoom, long localized text, virtual keyboard, safe-area, overflow, errors and empty states. Proposed layout does not prove responsiveness. Apply relevant [WCAG 2.2](https://www.w3.org/TR/WCAG22/) criteria with their exceptions: focus, keyboard, labels, feedback, contrast, target size and reduced motion. Distinguish automatic checks, manual checks and assistive-technology trials. Never claim compliance from a checklist.

| Artifact | Honest readiness |
| --- | --- |
| Written screen/flow | TEXT_SPEC / PREPARED |
| Real static image | STATIC_RENDER / RENDERED with saved evidence |
| Working clickable prototype | INTERACTIVE_VERIFIED only with real observed actions |
| Production code | IMPLEMENTED; RUNTIME_VERIFIED requires runtime evidence |
| Owner-approved direction | OWNER_ACCEPTED only after explicit decision |

For professional teams see the [UX/UI contract](../extensions/design/skills/ux-design-process/references/UX_UI_CONTRACT.json), [manual acceptance](../extensions/design/skills/ux-design-process/references/MANUAL_ACCEPTANCE.md), and [read-only validator](../scripts/validate_ux_ui_spec.py). Structural PASS is not a browser or aesthetic test.

## Optional preview and installation

```bash
python scripts/skill_manager.py catalog --profile ux-design
python scripts/skill_manager.py install --target /path/to/project --profile ux-design
python scripts/skill_manager.py install --target /path/to/project --profile ux-design --apply
python scripts/validate_ux_ui_spec.py extensions/design/skills/ux-design-process/references/EXAMPLE_EXPENSES.json
```

Preview writes nothing and install requires explicit `--apply`. Toolkit copies referenced for another person's task stay **read-only**; return their designs and reports in chat unless another destination is explicitly authorized. Actual AI-client skill activation, render, owner review and usability trials remain NOT_MEASURED / NOT_TESTED until performed.


## UX/UI Design Orchestra - ordinary idea to one reviewed design

**Three-direction visual concept search:** substantial design work explores three *structurally different* hypotheses and **renders three low-fidelity, comparably sized concept wireframes before selecting a winner**. Three descriptions or differently colored versions of one grid do not count. Compare information architecture, spatial rhythm, imagery, domain-specific shopping/booking task, responsive behavior, accessibility and feasibility. Record selected versus two discarded directions and a cross-domain swap test; only the winning concept gets full polished desktop/mobile mockups, **but all three preliminary sketches must be visually reviewed and attached to the approval package**. If tools cannot render the sketches, report `VISUAL_COMPARISON_MISSING` / `VISUAL_PACKAGE_MISSING` and do not ask for approval. New unrelated projects must not inherit YFC, Hermes or other clients' palettes, typography or layout as implicit defaults. The structural validator checks declared visual references and distinct ordered layouts, not real pixels or artistic originality. Mobile review checks readable labels and usable navigation, not only overflow. This remains a critique protocol, not an automated human visual-quality certificate.

**Visual-first routing is mandatory when Toolkit guidance is active:** substantive new sites, landing pages, UI redesign and anti-slop requests begin with `ux-ui-design-orchestra`. Generic `ux-design-process`, `frontend` and implementation skills are supporting methods, not replacement coordinators. A first request to "make a website" does not count as acceptance of a not-yet-seen design. Require an Impeccable-informed art-direction critique, authentic product positioning and at least three specific generic-template risks before proposing visual approval. Preserve the client's chosen brand; reject interchangeable SaaS structure rather than banning dark/lime by default.


Users may simply ask **"Make me a beautiful fitness club website"** or **"Improve my existing UI"**. When Toolkit guidance is available, the client selects the optional `ui-orchestra` profile or [`ux-ui-design-orchestra`](../.agents/skills/ux-ui-design-orchestra/SKILL.md) based on intent, not on magic skill words. `create-design` is for a new site/screen, `audit-proposal` for improving an existing UI, `audit-only` for diagnosis, and `implement-approved` only after specific visual acceptance. Questions are optional and limited to two consequential beginner-friendly clarifications. Existing project rules/brand always prevail; if there is no project, state assumptions rather than inventing its content.

In the read-only design modes, assign up to three complementary specialist reviews (Impeccable concept or critique, accessibility/responsive UX, and motion only when material), reconcile one concept and provide a post-approval component/test plan. Produce **actual mobile and desktop visual references** where authorized rendering tools exist. Without them return `TEXT_SPEC` / `VISUAL_PACKAGE_MISSING` rather than fictional screenshots. Even "build a website" does not permit frontend writes before visual approval. If custom/named subagents are unavailable, use generic spawned agents honestly or sequential perspectives, never claim fake parallelism. Reports stay in chat or an expressly requested target location, **never inside Toolkit**. User visual approval and release gates cannot be bypassed.

[New-design workflow](../.agents/skills/ux-ui-design-orchestra/references/CREATE_DESIGN.md) · [Orchestra workflow](../.agents/skills/ux-ui-design-orchestra/references/WORKFLOW.md) · [Specialist routing](../.agents/skills/ux-ui-design-orchestra/references/SPECIALISTS.md) · [Optional read-only report checker](../scripts/validate_ux_ui_orchestra.py). This is portable client guidance, not proof that live client multi-agent execution has been tested.
