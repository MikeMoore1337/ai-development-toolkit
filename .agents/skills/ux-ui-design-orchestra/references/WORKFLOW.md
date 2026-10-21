# UX/UI Design Orchestra - bounded workflow

## Modes

- `create-design`: a plain-language request to create a new site/screen, with no applicable approved screen to audit. Discover requirements, synthesize a one-piece design, prepare real previews when authorized tools exist, and stop before application edits. See [create-design](CREATE_DESIGN.md).
- `audit-proposal` **(default for existing UI)**: no target project writes. Produce a prioritized audit, cohesive visual direction and implementation/test plan; explicitly stop before UI edits. Screenshots generated outside the project under an authorized temporary/evidence location are allowed when available and privacy-safe; otherwise return text/evidence status, never invent an image.
- `audit-only`: diagnosis and priorities, no future implementation proposal required.
- `implement-approved`: separate explicitly requested task *after* documented visual approval for a specified design version. Implement only the accepted scope, using the target's existing GitHub/CI/visual-release process. Do not treat this as automatic continuation.

## Mandatory routing precedence

For any visually substantive new website, landing page, app design, UX/UI overhaul or audit, **MUST** enter `ux-ui-design-orchestra` before generic `ux-design-process`, `frontend`, `fullstack`, `make-feature`, `feature-delivery`, or `ui-fix`. The other skills may support the orchestra; they are not equivalent. A request to "build", "test", or "code" a new landing page still starts with `create-design` and the visual approval gate. An already approved isolated CSS/UX bugfix with no new design decision can go directly to `ui-fix`. Missing orchestra instructions means `ORCHESTRA_SOURCE_UNAVAILABLE`, not silent replacement by another skill.

## Natural-language routing

- "Make me a modern fitness-club landing page", "I want a nice website", "нарисуй новый экран" -> `create-design` when no applicable existing UI is supplied; never demand the words "UX", "skills" or "orchestra".
- "Improve this existing dashboard", "audit my current screen", "убери нейрослоп" -> `audit-proposal`; if explicitly requesting diagnosis without proposals -> `audit-only`.
- "Implement the design I approved" -> `implement-approved` **only** when the accepted visual version and owner evidence are available; otherwise stay read-only and request the missing approval.
- "Build my website" without an existing approved mockup is **not** permission to skip the visual gate. Start with `create-design`, show the proposal and request approval before application code changes.
- When a target repository exists, inspect it before selecting. If none is accessible, deliver a self-contained proposal in chat without pretending to inspect files. Ask at most two short, consequential beginner questions; prefer clearly stated defaults over a long questionnaire.

## Scope discipline

Target `AGENTS.md` and any active design brief outrank Toolkit; no skill can expand permissions. Inspect real UI states where possible and identify which observations came from code only, synthetic browser, authenticated target, or a provided reference image. Do not log secrets, personal notes or OAuth sessions. Do not make a demo screen look like production proof.

Coordinate with the existing target role instead of creating a second issue, task controller, daemon or persistent queue.

## Review assignment order (maximum three parallel)

1. Product design: Impeccable `shape`/`distill` for a new concept, `critique`/`polish` for existing UI; use the actual brand if available. Report hierarchy, usability and generic-template risks in this specific product.
2. Technical UX: UI Skills + current accessibility/browser QA; focus, text, responsiveness, empty/error/loading, input flow. Report objective defects with route/viewport.
3. Optional motion specialist: Emil's `review-animations` / `improve-animations` + project motion guidance. If no motion issue, choose design system consistency or product-specific flow reviewer instead. Taste / UI UX Pro Max only for user-authorized concept exploration and comparative ideas, not automatic reskinning.

Give all workers the **same** input digest: repository revision, product UX, approved brand decisions, viewports, task/out-of-scope, allowed tools, non-write gate and evidence references. Workers should return findings keyed by stable local IDs and an explicit no-write affirmation. The coordinator must inspect actual outputs and can reject a recommendation.

## Three distinct design hypotheses before selection

For `create-design` and substantial redesign proposals, the coordinator **must** explore three options with different information architecture, section hierarchy, spatial grids, image language, and major interaction. Keep cost low: three short briefs **plus three genuine low-fidelity rendered wireframes**, not three coded sites and not necessarily three independent agents. The wireframes must be viewed side by side at matching scale before choosing; record one visual frame per direction with source/provenance and an ordered layout signature. A text comparison is insufficient for visual signoff. Test each against the same project evidence and core user goal. Rank product/task fit, compositional differentiation, responsive/a11y feasibility, implementation cost and template-swap risk; document why one won and why the other two lost. If swapping the logo, product photography and color allows the same design to sell a gym membership, mango and B2B SaaS, the direction is insufficiently specific; revise instead of proceeding. Only the selected direction is polished as a desktop/mobile mockup, **but the approval package must also include the three preliminary wireframes and a visible comparison**; if no renderer is available, return `VISUAL_COMPARISON_MISSING` and `VISUAL_PACKAGE_MISSING`, not visual approval. Follow [CREATE_DESIGN.md](CREATE_DESIGN.md) and [HANDOFF.md](HANDOFF.md); never claim creative quality is machine verified.

## Product-specific quality gate

For substantial new work, require brand-fit, authentic audience/CTA, editorial hierarchy, distinctive visual rhythm, considered imagery and mobile composition. Use actual Impeccable methodology where its sources are readable; otherwise report its source status honestly. Before proposing an approval-ready concept, identify **at least three distinct generic-template risks** and correct them or explain why they suit this product. The dark-SaaS template with repetitive cards and synthetic proof is not an acceptable automatic fallback; neither the palette nor an accessibility PASS proves original art direction. Iterate until the design is not interchangeable with an unrelated business. See [create-design](CREATE_DESIGN.md).

## Merge algorithm

Group by affected user action and underlying cause; create one issue per problem, not one issue per model suggestion. Rank safety/blocked task then accessibility/clarity then performance then style; a stylistic issue cannot erase necessary medical/legal copy, permission warnings or visual owner acceptance. Require a causal explanation for any proposed change. Reconcile motion with reduced-motion and render cost. Separate **confirmed** defects from unverified hypotheses.

Output: design authority and version; actual worker trace; three visually evidenced wireframes before a selection for new/substantial design; for `audit-proposal`, evidence-linked issue table (severity, route/state/viewport, impact, cause, fix); for `create-design`, brief, assumptions, audience/CTA, page/interaction structure and decision rationale; single selected direction and discarded alternatives; concrete component/state/layout tokens plan; real visual artifact links or `TEXT_SPEC`; executable test plan; explicit human decisions; status.

## Stop conditions

Any of: missing user authorization for target read, no project design source, private-data boundary, worker collision, attempted UI write before approval, external binary wanting automatic download, missing concrete source or live status incorrectly claimed PASS -> stop that operation and state the limitation. Continue a **read-only** partial audit where evidence supports it, never fake a completed result.

### Minimal example prompt

"В моём открытом проекте используй UX/UI Design Orchestra: проверь мобильный экран X, привлеки Impeccable, доступность и motion по необходимости, подготовь один дизайн-проект с визуальными материалами и планом. Код приложения до моего 'Принимаю' не изменяй."
