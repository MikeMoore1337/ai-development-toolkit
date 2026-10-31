# UX/UI Evals - evidence, not stylistic censorship

[Русская версия](ru/UX_UI_EVALS.md)

The optional `scripts/ux_ui_evals.py` is an **offline visual evidence receipt checker** for the existing [UX/UI Design Orchestra](../.agents/skills/ux-ui-design-orchestra/SKILL.md). It cannot create renderings, judge artistic quality, verify accessibility compliance or approve an implementation.

## Tool-native creative freedom

No fixed number of creative directions, no automatic bans on card layouts, hero sections, photography, typography, gradients, familiar SaaS/e-commerce patterns or other aesthetics. The upstream specialist tools and the user's brief determine how many options to explore. The historical `needs_three` field in `fixtures/ux_ui_eval_cases.json` describes **that particular synthetic test's explicit request**, not a default policy or a production gate.

Use the relevant actual visual previews. An isolated mobile design can have one `winner:mobile` PNG and still be eligible for human review. A complete responsive site commonly benefits from `winner:desktop` and `winner:mobile`. If multiple `wireframe:<id>` assets exist, the report notes whether all claimed alternatives were captured distinctly and at matching viewport sizes; a mismatched or repeated sketch does not make the final preview aesthetically wrong, but cannot serve as proof of a distinct comparison.

Run:

```bash
python scripts/ux_ui_evals.py --catalog-only
python scripts/ux_ui_evals.py --packet review.json --asset-root /approved/local/design-preview
```

The `review.json` schema remains `schema_version=1` with `scenario_id`, `design_authority`, `directions` (possibly empty), `chosen_direction` (null with no directions), `rejected_directions` (possibly empty), `template_risks` (optional observations, including an empty list), `visual_assets`, `manual_reviews`, `owner_approval=PENDING` and `implementation_status=NOT_STARTED`. IDs and file paths must be consistent and safe. User assets and reports belong in the target project/authorized evidence folder, not Toolkit.

## Evidence checks versus artistic judgment

The tool verifies file existence, relative path safety, size, SHA-256 and PNG dimensions. SVG and HTML sources are not proof of a browser rendering. `winner_visual_present` states whether any actual winner PNG exists; `desktop_mobile_present` is descriptive and not a mandatory viewport quota. `comparable_three_artifacts` is a legacy receipt indicating whether the *explicitly requested* alternatives have matching viewports and distinct bytes; it cannot prove artistic diversity.

Manual `visual-appeal` reviews are human judgments, not code scores. Other manual criteria may include product-fit, task-hierarchy, responsive behavior, states, accessibility and motion. The checker cannot verify who reviewed the art, keyboard operation, independent design originality, user preference or WCAG conformance. A `TECH_PASS` is never evidence that a new visual direction is more beautiful.

When an earlier version was preferred/approved, keep its images and strengths as a baseline in the consumer project's context. Compare baseline with a proposed replacement at similar viewports and keep/refine the preferred version unless the owner agrees to another. The optional `visual_lineage` declaration in `scripts/validate_ux_ui_orchestra.py` records version refs, a qualitative comparison, separate technical QA and a decision; it does not inspect pixels or replace owner approval.

The offline outcome may be `VISUAL_PACKAGE_MISSING`, `NEEDS_DESIGN_REVISION` or `AWAITING_HUMAN_VISUAL_REVIEW`. It **never** means `OWNER_ACCEPTED`, automatic aesthetic superiority or permission to modify/deploy a user application.

All example assets and unit tests are synthetic. Browser-backed UX/UI evidence is separately implemented in #486/PR #487; native activation of original design skills is independently tracked in #449.
