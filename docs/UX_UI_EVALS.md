# UX/UI Evals - visual evidence, not style by checklist

[Русская версия](ru/UX_UI_EVALS.md)

Issue [#192](https://github.com/MikeMoore1337/ai-development-toolkit/issues/192) adds an **optional offline evidence precheck** to the established [UX/UI Design Orchestra](../.agents/skills/ux-ui-design-orchestra/SKILL.md). It is not another orchestration framework, renderer, design generator, screenshot comparison engine, WCAG conformance test, or owner-approval service.

## Scenario catalog

Four bilingual task fixtures in `fixtures/ux_ui_eval_cases.json`: new site, substantial redesign, previously approved minor UI fix, and responsive/accessibility audit. All include manual criteria and project-specific authority. Three directions are required for new/substantial designs, not for minor fixes. Color palettes and existing brand fonts are **not** penalized as signs of generic SaaS design.

```bash
python scripts/ux_ui_evals.py --catalog-only
```

The fixture list tests that the *criteria exist*. It does not demonstrate aesthetic quality or rendered assets.

## Checking a real review package

```bash
python scripts/ux_ui_evals.py --packet review.json --asset-root /approved/local/design-preview
```

`review.json` needs `schema_version=1`, a `scenario_id`, a named `design_authority`, `directions` (three genuinely different layout-signature and information-architecture statements for new/substantial designs), `chosen_direction`, two `rejected_directions`, `template_risks` (three specific observed/prospective generic-template risks), `visual_assets`, `manual_reviews`, `owner_approval=PENDING` and `implementation_status=NOT_STARTED`. The review is a **separate evidence supplement**; the [existing Orchestra receipt validator](../scripts/validate_ux_ui_orchestra.py) remains the source of structural checks for full design coordination.

For a new/substantially redesigned site include three distinct local `wireframe:<direction_id>` assets of matching declared viewport and selected `winner:desktop` and `winner:mobile` PNG captures. The checker validates local file existence, path safety, size limits, hashes and reported PNG dimensions. SVG drawings can serve as sketches but they are **source files**, not proof that the team viewed the result. HTML source does **not** count as a captured winning screen; use real screenshots. Distinct SHA-256 hashes do not prove meaningful spatial originality.

Manual review IDs come from the scenario, e.g. `product-fit`, `task-hierarchy`, `compositional-originality`, `cross-domain-swap`, `mobile-desktop`, `states`, `accessibility`, `motion`, `design-authority`. Give each status `NOT_REVIEWED`, `ACCEPT` or `REVISE`; any non-pending decision needs a specific explanation. The checker cannot verify human identity, browser interaction, accessible focus, real reduced-motion preferences, font loading, or the owner's actual approval.

A visual result may report `VISUAL_PACKAGE_MISSING`, `NEEDS_DESIGN_REVISION`, or `AWAITING_HUMAN_VISUAL_REVIEW`. It **never** returns `OWNER_ACCEPTED` or authorizes changes in any target application. Any stated manual approvals remain self-declared and actual visual quality is `NOT_VERIFIED`.

## Real evaluation procedure

On an owner-authorized working copy, use the project's own visual contract and capture desktop/mobile screens with actual viewports and representative interaction states (loading, error, completed, keyboard focus, scrolling, reduced-motion where applicable). Compare three **visibly** different sketches side by side on a consistent scale for major work, with one winning direction and two documented reasons for rejection. Audit product specificity using a cross-domain swap test without banning brand colors or reusable components. Have a human examine the files, log actual observations versus hypotheses, then request approval of a specific visual version **before** implementation. The offline precheck is only an evidence-format quality filter.

All examples and unit tests are synthetic. No real project's UI was changed, no browser or external paid API was invoked and there is no measured visual usability improvement yet.

## Optional local Chromium screenshot capture (#486)

The existing evidence precheck does **not render HTML**. For an approved local prototype, an additional **opt-in** helper creates actual browser PNGs and layout diagnostics using a previously installed Playwright Chromium (no automated package/browser download, paid API or external upload):

```json
{
  "schema_version": 1,
  "scenario_id": "new-site",
  "captures": [
    {"purpose": "wireframe:editorial", "source": "editorial.html", "viewport": "400x600"},
    {"purpose": "wireframe:catalog", "source": "catalog.html", "viewport": "400x600"},
    {"purpose": "wireframe:guide", "source": "guide.html", "viewport": "400x600"},
    {"purpose": "winner:desktop", "source": "winner.html", "viewport": "1440x900"},
    {"purpose": "winner:mobile", "source": "winner.html", "viewport": "390x844"}
  ]
}
```

Save this as `capture-plan.json` **outside Toolkit**. Place the four HTML views in the permitted prototype folder, or use explicit `http://127.0.0.1:PORT/path` sources from an already-running local development server. Run from the Toolkit checkout:

```bash
python scripts/ux_ui_browser_capture.py --plan /approved/capture-plan.json --source-root /approved/prototype --output /approved/visual-evidence-v1
```

The output directory must be new, existing parent, **outside Toolkit**. If a local system Chromium is already installed, `--chromium-executable /path/to/chromium` selects it; this command never installs a browser. Only local files and explicit loopback HTTP origins are accepted; remote HTTP(S) and WebSockets are blocked. A prototype depending on remote fonts, images or APIs may render incompletely; blocked requests appear in diagnostics and must be resolved before review. Never capture or share confidential sessions without authorization.

The output also includes `comparison.html`, a local side-by-side contact sheet for the three sketches and responsive winner. Inspect the actual PNGs there, not only the report; equal hashes for different wireframe captures trigger `NEEDS_LAYOUT_REVIEW` but unequal hashes alone do not prove structural originality.

The generated `capture_report.json` contains `visual_assets` in the shape accepted by the existing `review.json` evidence packet, plus PNG SHA-256, viewports, DOM overflow, small interactive targets, script errors and blocked requests. Copy its `visual_assets` into that packet before running `ux_ui_evals.py`; source labels, design authority, three distinct content hierarchies, manual review and approval gate still come from the existing workflow. `NEEDS_LAYOUT_REVIEW` requires inspection and recapture to a versioned folder, while `AWAITING_HUMAN_VISUAL_REVIEW` **is not acceptance or aesthetic verification**. This tool cannot assess originality, visual polish, WCAG compliance or actual interactions, and CI unit tests use synthetic browser doubles, not live client proof. If Playwright/Chromium or local navigation is unavailable, report `PLAYWRIGHT_UNAVAILABLE` / `BROWSER_RENDER_FAILED`, retain `VISUAL_PACKAGE_MISSING`, and do not fabricate a screenshot.
