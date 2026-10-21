# Create-design - natural-language design from a blank canvas

Use this route when the user wants a **new design** ("Нарисуй лендинг фитнес-клуба", "Make me a stylish website") and the relevant approved UI is absent. The UX/UI Design Orchestra remains a **task-scoped instruction**, not an automatic plugin, renderer or agent service. The model must actually read this guidance to follow it.

## Beginner contract: no special prompt required

1. Determine the design target from plain words. Inspect the active project and its `AGENTS.md`/brand when accessible; if not, say so. The user does not need to know skill names, frameworks, Git, UX terms or any repository contents.
2. Ask **zero questions by default**, **up to two** short everyday-language questions only when the answers materially affect the direction (e.g. new vs existing site; required brand). If unanswered, state non-dangerous, reversible assumptions and proceed; no fabricated brand, business claims or study results.
3. Form a small internal brief: audience; real user goal; one primary action; page sections; content required vs unverified placeholder; mobile/desktop states; accessibility; motion; explicit constraints and unknowns. Do not require a new PRD, Figma, paid API or terminal.
4. **Develop three different structural design hypotheses** before committing to visual assets or code. Use different page architectures, grid and editorial rhythm, product interaction and imaging metaphors; palette-only or copy-only variants count as the same concept. For mango retail, for example, explore (a) a tactile produce market, (b) a culinary magazine, and (c) a botanical field guide, each with genuinely different flows. Never mechanically copy these three archetypes into unrelated projects. Generate three concise concept briefs, not three functioning sites; label product facts as assumptions. Next, select up to three distinct specialist perspectives: visual/product structure, accessible responsive UX, and motion or concept exploration only when useful. If client subagents are absent, perform reviews sequentially and identify them as `SEQUENTIAL`. Source URL alone is `REFERENCE_ONLY`.
5. Compare all three hypotheses with a documented decision matrix: product fit, primary user task and information hierarchy, spatial/layout originality, image and typography treatment, mobile viability, accessibility and implementation risk. Challenge whether the layout can be relabelled from mango to fitness to SaaS without changing its structure (`cross-domain swap test`). If it can, return `NEEDS_DESIGN_REVISION` and revise the candidates. Record why two designs lost and select only one. Merge into **one chosen concept**, not a collage of specialist preferences. Use a considered art direction, typography, image framing and layout rhythm that could not trivially be reskinned into a SaaS landing. Choose conservative site-specific defaults if no brand exists. Avoid fake testimonials, fabricated memberships/prices, invented photography rights, imaginary booking integrations and generic AI-gradient aesthetics. A sample CTA can be *designed* without claiming the booking flow works.
6. **Visual preview:** if approved browser/image/HTML tooling exists, actually render mobile and desktop views, record their file/attachment references, viewports and origin, and label `RENDERED`. An HTML file is not `INTERACTIVE_VERIFIED` without tested interactions. If tools are unavailable, return a useful structure/layout spec labelled `TEXT_SPEC` and `VISUAL_PACKAGE_MISSING`, not a fake image or approval-ready claim.
7. Summarize in ordinary language: what was designed, key sections, why this hierarchy, previews/provenance, assumptions, adaptation and interaction test plan, and what approval is needed. Default to chat delivery, never Toolkit storage. Do not modify the user's application, scaffold a frontend, write tokens/tests or open PR solely for this preview.
8. Only after explicit acceptance of a **specific visual version** may a separate `implement-approved` task edit the target application and test it. Respect the project's own CI, owner and deployment permissions; acceptance of the look does not authorize deployment.

## Anti-SaaS-slop design-quality gate

A project-specific graphic language matters more than a fashionable palette. Dark graphite and lime can suit a fitness brand, but using those colors over generic metrics, cards and three default pricing tiers remains interchangeable SaaS styling.

Before presenting any new or substantively revised design, record **the three structurally different candidates, a comparative decision and cross-domain swap test**; then (a) whom the design serves and its distinguishing product/venue positioning; (b) typography, grid, visual narrative, image treatment and mobile rhythm; (c) why the actual CTA, content and section order follow user needs; (d) **three specific generic-template risks** discovered during critique and how they were eliminated or justified; and (e) one meaningfully different considered direction with the reason for choosing the final one. The alternative is for internal critique, not another incoherent final mockup.

A fitness club might call for training atmosphere, credible staff/team details, bold editorial photography, class discovery and physical-location cues rather than app-dashboard cards, invented growth statistics and arbitrary pricing tiles. Do not turn this example into another mandatory template; honor real brand rules and do not fabricate timetable, prices, benefits or licensed media.

Actual Impeccable `shape` / `distill` (or relevant named specialist method) should be **read** from a real source when available. If not, label `REFERENCE_ONLY` or `UNAVAILABLE`; never claim that external experts ran solely because their names appear in an output. Passing browser tests and responsive rendering do not validate originality. If the concept remains generic, return `NEEDS_DESIGN_REVISION` and redesign before owner visual review.

## Three-direction comparison contract

Use **three concise distinct concepts**; they may be explored sequentially without paid API, subagents or external design services. Each candidate must have:
- unique `id` and descriptive name;
- distinct `information_architecture`, `composition`, `typography_and_imagery`, `primary_interaction` and `product_story`;
- an honest `tradeoff` (what it loses, not just what it wins).

Compare them using the same product goals and available evidence. Include `selected_id`, `selection_rationale`, and two documented `rejections` keyed to the nonselected candidates. The `cross_domain_swap_test` must state what breaks if the same structure is relabelled for a different domain; if nothing meaningful breaks, revise. The test is a declared critique, **not** a guarantee of human visual originality.

Only the winning direction proceeds to optional rendered mobile/desktop previews. Present a compact explanation of the discarded approaches when helpful; do **not** force an inexperienced user through three full mockups or require them to choose without context. Do not turn "three different directions" into three competing final websites. If there is an approved existing design contract, use it as the shared constraint across all candidates, and preserve it unless the user explicitly authorizes reconsideration.

## Example with no prior project knowledge

**User:** "Хочу красивый сайт для фитнес-клуба."

**Expected assistant behavior:** infer `create-design`; if no brand or files exist, state assumptions such as a generic single-location gym and placeholder copy. Propose hero with a clear trial-class CTA, benefits/facilities, class schedule outline, trainers, location/contact and FAQ; mark actual schedule, address and reviews as unverified. Use a deliberate type scale, mobile-first layout, keyboard-focus and reduced-motion plan. Create actual visual previews *only if tooling exists*, then request visual feedback. Never say "three agents ran" unless execution traces prove it.

## Mode / evidence boundary

- `create-design` = new concept, zero application writes, design assumptions permitted but labelled, no observed defects of a nonexistent UI.
- `audit-proposal` = inspect an existing UI, separate verified defects from hypotheses, zero application writes.
- `audit-only` = diagnose without preparing a replacement concept.
- `implement-approved` = accepted visual evidence and explicit owner decision; still not permission to merge/deploy.
