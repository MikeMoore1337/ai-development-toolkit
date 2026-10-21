# Create-design - natural-language design from a blank canvas

Use this route when the user wants a **new design** ("Нарисуй лендинг фитнес-клуба", "Make me a stylish website") and the relevant approved UI is absent. The UX/UI Design Orchestra remains a **task-scoped instruction**, not an automatic plugin, renderer or agent service. The model must actually read this guidance to follow it.

## Beginner contract: no special prompt required

1. Determine the design target from plain words. Inspect the active project and its `AGENTS.md`/brand when accessible; if not, say so. The user does not need to know skill names, frameworks, Git, UX terms or any repository contents.
2. Ask **zero questions by default**, **up to two** short everyday-language questions only when the answers materially affect the direction (e.g. new vs existing site; required brand). If unanswered, state non-dangerous, reversible assumptions and proceed; no fabricated brand, business claims or study results.
3. Form a small internal brief: audience; real user goal; one primary action; page sections; content required vs unverified placeholder; mobile/desktop states; accessibility; motion; explicit constraints and unknowns. Do not require a new PRD, Figma, paid API or terminal.
4. Select up to three distinct specialist perspectives: visual/product structure, accessible responsive UX, and motion or concept exploration only when useful. If client subagents are absent, perform reviews sequentially and identify them as `SEQUENTIAL`. Source URL alone is `REFERENCE_ONLY`.
5. Merge into **one chosen concept**, not a collage of specialist preferences. Choose conservative site-specific defaults if no brand exists. Avoid fake testimonials, fabricated memberships/prices, invented photography rights, imaginary booking integrations and generic AI-gradient aesthetics. A sample CTA can be *designed* without claiming the booking flow works.
6. **Visual preview:** if approved browser/image/HTML tooling exists, actually render mobile and desktop views, record their file/attachment references, viewports and origin, and label `RENDERED`. An HTML file is not `INTERACTIVE_VERIFIED` without tested interactions. If tools are unavailable, return a useful structure/layout spec labelled `TEXT_SPEC` and `VISUAL_PACKAGE_MISSING`, not a fake image or approval-ready claim.
7. Summarize in ordinary language: what was designed, key sections, why this hierarchy, previews/provenance, assumptions, adaptation and interaction test plan, and what approval is needed. Default to chat delivery, never Toolkit storage. Do not modify the user's application, scaffold a frontend, write tokens/tests or open PR solely for this preview.
8. Only after explicit acceptance of a **specific visual version** may a separate `implement-approved` task edit the target application and test it. Respect the project's own CI, owner and deployment permissions; acceptance of the look does not authorize deployment.

## Example with no prior project knowledge

**User:** "Хочу красивый сайт для фитнес-клуба."

**Expected assistant behavior:** infer `create-design`; if no brand or files exist, state assumptions such as a generic single-location gym and placeholder copy. Propose hero with a clear trial-class CTA, benefits/facilities, class schedule outline, trainers, location/contact and FAQ; mark actual schedule, address and reviews as unverified. Use a deliberate type scale, mobile-first layout, keyboard-focus and reduced-motion plan. Create actual visual previews *only if tooling exists*, then request visual feedback. Never say "three agents ran" unless execution traces prove it.

## Mode / evidence boundary

- `create-design` = new concept, zero application writes, design assumptions permitted but labelled, no observed defects of a nonexistent UI.
- `audit-proposal` = inspect an existing UI, separate verified defects from hypotheses, zero application writes.
- `audit-only` = diagnose without preparing a replacement concept.
- `implement-approved` = accepted visual evidence and explicit owner decision; still not permission to merge/deploy.
