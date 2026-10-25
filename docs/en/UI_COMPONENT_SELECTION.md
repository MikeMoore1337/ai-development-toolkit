# Component selection: shadcn/ui and Magic UI (portable reference, #408)

This is a **task-scoped decision aid**, not an installer, React runtime, visual approval, or standalone UI design controller. It applies to any consumer application through the existing `component-architecture`, `motion-quality` and `ux-ui-design-orchestra` skills. The target project's own design system and `AGENTS.md` take precedence.

## Original sources and boundary

- [shadcn-ui/ui](https://github.com/shadcn-ui/ui): registry-based React component patterns; many variants assume Tailwind and accessibility primitives such as Radix/Base UI. Check the license **per copied component and dependencies**, not a global label.
- [magicuidesign/magicui](https://github.com/magicuidesign/magicui): illustrative React visual/motion treatments. Individual patterns may depend on Motion, Tailwind or other packages; assess bundle delta and reduced motion.
- No upstream installer, component source, CSS or third-party package is included in Toolkit. A URL is `REFERENCE_ONLY`, not evidence an external project was run. No paid API or remote model invocation is required.

## Decision tree

1. Define the **observed** user problem on a real page, including current revision, route, state, viewport and screenshot. If not observed, label `HYPOTHESIS`, not a defect.
2. Inspect the consumer's existing design tokens, component primitives, typography, focus/hover/selected behavior, PWA/mobile constraints and CSS/JS animation patterns. Prefer `REUSE_EXISTING` if the capability already exists.
3. If still missing, shortlist a concrete component/interaction, not a whole library. Record original file URL, immutable revision, SPDX/other license conditions and any required notices. Unknown license or missing upstream pin = **do not copy**.
4. List additions to CSS, Tailwind, Radix, Base UI, Motion or other runtime dependencies. Compare component implementation against native browser elements, existing React patterns, local CSS and Web Animations API. Reject extra dependencies without a measurable UX advantage.
5. For proposed visual or compositional changes, provide actual separate Dark/Light and relevant desktop/mobile artifact links; state which screenshots are synthetic, before and after, and reduced-motion variants. `PROPOSAL_ONLY` is never equivalent to `OWNER_ACCEPTED`.
6. Implement *only an approved concrete version* in the consumer repository, preserving theme, semantics, accessible names, focus, keyboard, contrast, reduced-motion and touch sizing. Measure bundle before/after when dependencies are added and test against the affected states.
7. Verify current exact-head CI, owner release gates and post-release smoke where required. A source-only reference or fixture PASS never proves a working React component.

## Optional offline structural checklist

Toolkit includes an **advisory, fail-closed** local packet linter. It does not run a browser, install packages or write results. A structural PASS is **not** authorization to implement:

```sh
python scripts/validate_ui_component_adoption.py /path/to/local-ui-candidate.json
```

The input is an explicit JSON dictionary with exact keys: `schema_version`, `candidate`, `source`, `decision`, `consumer_revision`, `observed_problem`, `reuse_evidence`, `license`, `source_revision`, `new_dependencies`, `performance`, `accessibility`, `reduced_motion`, `visual_evidence`, `owner_approval`, `tests`, `remote_services`. For example, a synthetic proposal uses `source="shadcn-ui/ui"`, `decision="PROPOSAL_ONLY"`, `consumer_revision="UNKNOWN"`, `license="MIT_REVIEWED"` after a real license review, and a full upstream SHA; empty `new_dependencies`, `visual_evidence` and `remote_services`; untested evidence values remain `NOT_TESTED` and `NOT_EXECUTED`.

Only `IMPLEMENT_APPROVED` can pass with an exact 40-character consumer SHA, actual owner approval reference, at least one real linked visual artifact, accessibility and reduced-motion testing, `PASS_EXACT_SHA` and measured before/after bundle bytes **if adding a dependency**. Even then this is only consistent assertions, **not independently verified evidence**. Do not place consumer evidence, file paths, screenshots or tokens inside the Toolkit repository.

A component selection can legitimately end with `REUSE_EXISTING`; this is a completed decision **only with evidence** that the current primitive solves the original problem. Otherwise keep a specific owner-gated proposal open and do not invent a product change.
