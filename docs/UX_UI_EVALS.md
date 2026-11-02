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

The optional browser renderer from #486 does not constitute a native invocation of original design skills (#449). Unit test doubles, real Chromium captures, interaction tests and human visual approval are separate evidence categories.

## Optional local Chromium capture (#486)

The existing evaluation checker inspects evidence; it does not render HTML. For a user-approved local prototype, run the separately optional helper scripts/ux_ui_browser_capture.py with an already installed Playwright Chromium. It produces real PNGs, comparison.html, capture_report.json, image SHA256 digests and DOM diagnostics. All outputs must be written to a new folder OUTSIDE Toolkit.

Example capture-plan.json for the specific five-view #486 test (NOT a universal design quota):

~~~json
{
  "schema_version": 1,
  "scenario_id": "new-site",
  "captures": [
    {"purpose": "wireframe:editorial", "source": "editorial.html", "viewport": "400x600"},
    {"purpose": "wireframe:catalog", "source": "catalog.html", "viewport": "400x600"},
    {"purpose": "wireframe:journey", "source": "journey.html", "viewport": "400x600"},
    {"purpose": "winner:desktop", "source": "winner.html", "viewport": "1440x900"},
    {"purpose": "winner:mobile", "source": "winner.html", "viewport": "390x844"}
  ]
}
~~~

Run: python scripts/ux_ui_browser_capture.py --plan /approved/capture-plan.json --source-root /approved/prototype --output /approved/visual-evidence-v1 --chromium-executable /path/to/approved/chromium

Use only authorized local HTML paths or explicit loopback HTTP preview URLs. The local HTML case is loaded into an isolated about:blank document using set_content after strict root, symlink, UTF-8 and 2 MiB checks: Chromium file: navigation cannot safely constrain subresources to the authorized source root. Relative CSS/images/scripts might not load in inline mode; use self-contained HTML or an authorized loopback server for those assets. The helper never installs Playwright/Chromium, enables unrestricted file: access or permits remote HTTP(S)/WebSocket access. Every blocked request requires review. The actual CSS viewport must match the declared screenshot size; overflow over 1 px, targets under 24 px, JavaScript errors, missing text and repeated candidate images are flagged for review.

The output visual_assets entries can be carried into the existing review.json evidence packet, without skipping its human approval process. A single user-requested mobile view is accepted. Sketch count, content and responsive sizes come from the user's requirements. Inspect the actual PNG images, not just report status. An inaccessible browser must be reported as PLAYWRIGHT_UNAVAILABLE or BROWSER_RENDER_FAILED. Source-level tests, an original skill invocation and owner approval are NOT implied.
