# Design review, alternative exploration and realistic stress checks

This optional checklist extends the UX/UI process. It is not a second controller, mandatory runtime, design-system source of truth, automatic audit tool or substitute for actual screenshots/tests.

## A. Brief first, without needless questions

Capture **stable product facts** (user, job, context, constraints, approved assets, source and acceptance criteria) separately from **proposed visual direction** (layout, density, type, interaction style). A screenshot is evidence of appearance at one state, not evidence of the product's approved intent. Reuse facts already supplied; ask at most one essential blocking question when needed, otherwise draft explicit assumptions.

A concise brief covers: user job, success oracle, primary action, scope and non-goals, real data ranges, important states, existing brand, access/platform requirements and approvals. Do not start coding merely because a brief sounds complete; implementation is a separate authorized task.

## B. Three distinct review lenses

| Lens | Inspect | Evidence for PASS | If evidence absent |
| --- | --- | --- | --- |
| Task clarity and design critique | Hierarchy; first-run orientation; label clarity; affordances; cognitive load; steps to complete user goal; error recovery | Reviewer walkthrough linked to screens, source requirements and stated trade-off; if user-tested include observed recording | REVIEW_OPINION / NOT_TESTED, never 'objective excellence' |
| Measurable technical checks | Action reachability; keyboard/focus; text overflow; contrast; form errors; loading/empty/permission; responsive layout | Reproducible browser/device check at stated viewport and UI state, with result and artifact | PROPOSED_CHECK / NOT_TESTED |
| Visual consistency | Existing tokens, type scale, icon family, spacing rhythm, layout density, approved references; brand modes | Matched-state screenshots or approved source reference, reviewer notes of divergences | REFERENCE_MISSING / NOT_TESTED |

Order findings by **blocker** (can't complete core journey, privacy/access rights, keyboard trap, missing feedback), **high** (errors, overflow, navigation ambiguity), **moderate** (hierarchy inconsistency), then **cosmetic**. Do not assert severity without a described impact. Record observation separately from suggested remedy and verification status.

## C. Realistic boundary inputs, never fictional test results

For each meaningful component, derive boundaries from a schema or plausible user data. Use the **same actual data boundary** (props, fixture or intercepted API response) as the normal UI; never edit DOM/CSS manually just to manufacture a failure. If the backend imposes no known size/format limit, mark it UNKNOWN.

| Dimension | Proposed cases / expected check |
| --- | --- |
| Density/length | Empty and 1 item; realistic upper list limit; one-character and long but plausible full names; long unbroken emails; multiple-line headings |
| Data completeness | Missing avatar/photo, optional description absent, null / unknown values, partial or failed load; no orphan separators or undefined text |
| Numbers and localization | 0, 1, large and negative values when domain allows; decimal separators, currency/units, date/time and pluralization; translated strings and RTL only when relevant |
| Security/permissions | Role without permission, expired login, 403/404, unauthorized button/route, recovery without leaking details |
| Network and concurrency | Slow response, offline, timeout, server error, stale response, duplicated submit, retry without accidental duplicate change |
| Forms and focus | Empty, invalid and corrected input; visible label; non-color-only error; focus return after dialogs; keyboard-only completion |
| Mobile/web | Virtual keyboard, dynamic viewport, notches and safe areas, touch versus hover capabilities, scroll/gesture conflict, reduced motion, 200% zoom and larger text |

**Oracle:** document expected visual/functional outcome, input boundary, device/viewport and evidence per case. Use tags PROPOSED, EXECUTED_PASS, EXECUTED_FAIL, BLOCKED or NOT_TESTED, not "covered" without running anything. Avoid shipping any synthetic-data toggle to production.

## D. Compare real design alternatives only when valuable

Generate 2-3 variants **only if a material decision is open**. Each candidate must address the same source R/AC, while differing on a named design axis (navigation model, hierarchy, information density, interaction sequence) rather than changing minor colors. Record benefits, risks, accessibility, implementation complexity and which goal it optimizes. A screenshot collage is a STATIC_RENDER; if no actual prototypes were built, explicitly state TEXT_SPEC. Do not silently pick a winner when owner approval is required.

| Candidate | Distinguishing decision | Main benefit | Main risk | Verification |
| --- | --- | --- | --- | --- |
| A | Primary action on overview | Low interaction distance | Crowded overview | NOT_TESTED |
| B | Dedicated task screen | More guided flow | Additional navigation | NOT_TESTED |

The table is a **hypothetical example**, not a recommendation for every product.

## E. Developer handoff and approvals

Provide R/AC/UC-to-flow/screen/component links; approved vs proposed tokens; conditional responsive/mobile states; actual assets with provenance; tests to run with the known toolchain; unverified hypotheses; any approval gate. A source can inspire a check without its own CLI, Figma, paid API, extra agent or browser plugin being required.
