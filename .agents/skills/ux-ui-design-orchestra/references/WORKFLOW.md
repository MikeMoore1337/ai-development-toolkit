# UX/UI Design Orchestra - bounded workflow

## Modes

- `create-design`: a plain-language request to create a new site/screen, with no applicable approved screen to audit. Discover requirements, synthesize a one-piece design, prepare real previews when authorized tools exist, and stop before application edits. See [create-design](CREATE_DESIGN.md).
- `audit-proposal` **(default for existing UI)**: no target project writes. Produce a prioritized audit, cohesive visual direction and implementation/test plan; explicitly stop before UI edits. Screenshots generated outside the project under an authorized temporary/evidence location are allowed when available and privacy-safe; otherwise return text/evidence status, never invent an image.
- `audit-only`: diagnosis and priorities, no future implementation proposal required.
- `implement-approved`: separate explicitly requested task *after* documented visual approval for a specified design version. Implement only the accepted scope, using the target's existing GitHub/CI/visual-release process. Do not treat this as automatic continuation.

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

## Merge algorithm

Group by affected user action and underlying cause; create one issue per problem, not one issue per model suggestion. Rank safety/blocked task then accessibility/clarity then performance then style; a stylistic issue cannot erase necessary medical/legal copy, permission warnings or visual owner acceptance. Require a causal explanation for any proposed change. Reconcile motion with reduced-motion and render cost. Separate **confirmed** defects from unverified hypotheses.

Output: design authority and version; actual worker trace; for `audit-proposal`, evidence-linked issue table (severity, route/state/viewport, impact, cause, fix); for `create-design`, brief, assumptions, audience/CTA, page/interaction structure and decision rationale; single selected direction and discarded alternatives; concrete component/state/layout tokens plan; real visual artifact links or `TEXT_SPEC`; executable test plan; explicit human decisions; status.

## Stop conditions

Any of: missing user authorization for target read, no project design source, private-data boundary, worker collision, attempted UI write before approval, external binary wanting automatic download, missing concrete source or live status incorrectly claimed PASS -> stop that operation and state the limitation. Continue a **read-only** partial audit where evidence supports it, never fake a completed result.

### Minimal example prompt

"В моём открытом проекте используй UX/UI Design Orchestra: проверь мобильный экран X, привлеки Impeccable, доступность и motion по необходимости, подготовь один дизайн-проект с визуальными материалами и планом. Код приложения до моего 'Принимаю' не изменяй."
