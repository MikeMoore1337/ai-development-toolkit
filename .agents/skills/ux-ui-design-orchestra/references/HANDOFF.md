# Specialist handoff and consolidated report

This is a coordination protocol, not a source of role authority. The final report is in **one coherent language matching the user**.

## Input to each independent reviewer

Provide: mandatory routing decision (`ui-orchestra` or justified minor-fix exemption); user goal; chosen mode (`create-design`, `audit-proposal`, etc.); target route/component if one exists (otherwise `NOT_APPLICABLE`); immutable review revision (SHA or `UNKNOWN`); applicable `AGENTS.md` and design-system source; task type `audit-proposal`; read-only constraint; any observed before screenshots (with route/state/viewport and synthetic/live origin); no secrets; excluded surfaces; accepted fonts, palettes and accessibility rules.

Ask for (a) 1-5 findings with stable `F` IDs and evidence IDs, (b) verified observation versus hypothesis, (c) severity/impact and plausible corrective approach, (d) constraints that forbid proposed cosmetics, (e) contradiction with other recommendations, (f) evidence sources and tools **actually** used. Never ask workers to edit UI. Spawn only when a real delegation tool is available.

## Status vocabulary

- `ACTUAL_SUBAGENT`: the client exposed a named role and actual creation/return; include tool evidence, ID.
- `GENERIC_SUBAGENT`: a real spawned generic worker executed the role brief; include ID; do **not** call it named Impeccable agent unless that skill was actually read.
- `SEQUENTIAL`: a single assistant switched perspectives; not independent subagent results.
- `REFERENCE_ONLY` or `UNAVAILABLE`: the external method was not locally activated.
- `RENDERED`: a genuinely retrieved/generated PNG/HTML or actual browser capture; include accessible artifact reference, viewport, source.
- `SOURCE_ONLY`: code inspected without rendered browser state.
- `NOT_OBSERVED`: not examined, no claim of browser or human review.
- `NOT_REQUESTED`, `PENDING`, `OWNER_ACCEPTED`: approval statuses. `OWNER_ACCEPTED` needs explicit prior owner decision for specific version, never inferred.

## Final report order

1. **Boundaries**: chosen mode, project, baseline SHA, visual contract, no-write affirmation.
2. **Evidence ledger**: observed URL/route if available (not required for brand-new concepts), viewport, data provenance, screenshots/QA, missing evidence; each `E#`.
3. **Synthesis**: existing UI - 3-7 deduplicated prioritized issues linked to `E#` or clearly `HYPOTHESIS`; new UI - concise brief, explicit assumptions, page and interaction structure, rationale and discarded alternatives. Do not invent observed defects of a page that does not exist.
4. **Exploration + one design**: for new/substantive designs list three distinct candidate briefs (not just palette variants), comparison criteria and decision, two rejection reasons, and the cross-domain swap test; then detail only the winning concept. Behavior and screen structure, current versus proposed layout, typography/tokens from existing brand, responsive states, accessibility and motion. Include the visual identity rationale, at least three concrete template risks and their remedies, plus a genuinely different considered alternative and why the selected concept is more suitable. Optional alternatives must not become mixed composition.
5. **Visual package**: actual PNG/HTML images and comparison if available; else `TEXT_SPEC` and `VISUAL_PACKAGE_MISSING` when owner needs visual approval.
6. **Implementation plan**: exact components/files *suggested* for a later task, dependencies, risks, acceptance checks, test design, non-goals and no code mutations.
7. **Worker receipt**: source skills loaded vs references; real parallel calls or sequential fallback; unresolved conflicts. Specifically say if Impeccable source was actually read or was only a reference; do not equate a named skill with execution evidence.
8. **Gate**: `AWAITING_VISUAL_APPROVAL` only when a three-direction comparison passes for new designs and a real referenced visual artifact exists. `NEEDS_DESIGN_REVISION` requires renewed exploration, not an implementation. `AWAITING_VISUAL_APPROVAL` only with a real, accessible visual package where the task calls for one; otherwise `VISUAL_PACKAGE_MISSING`. Explicitly `implementation: NOT_STARTED`. Visual approval is not a merge/deploy approval. Do not claim pass from a draft.

## Optional machine-readable contract

A deterministic **declaration linter** is in `scripts/validate_ux_ui_orchestra.py`; sample in `fixtures/ux_ui_orchestra_valid.json`. A PASS means consistent labels and references, not actual visual correctness, provenance or active multi-agent support. Do not require this JSON file for chat-only use.
