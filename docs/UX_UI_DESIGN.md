# UX/UI Design - from requirements to developer handoff

[Русская версия](ru/UX_UI_DESIGN.md)

**UX** describes what the user needs to do and whether a journey makes sense; **UI** describes the visible interface and its states. A **wireframe** is a structural sketch, not a reviewed visual design; a beautiful static mockup is not working frontend code. An **interactive prototype** needs functioning actions and real interaction tests.

## Start without technical vocabulary

> Plan an app for household expenses. I need to add entries, see totals and edit or delete them. Describe the screens, navigation and errors first. Do not implement code yet.

An ordinary description is enough. **For text-only user journeys and screen structure**, the optional `ux-design` profile is appropriate. **For a new site, landing page or visual redesign**, start with `ui-orchestra` / `ux-ui-design-orchestra`: follow the available original tool workflows, render the task-appropriate options and request approval of a specific version before implementation. Linking Toolkit in a chat provides guidance but does not grant access to your project. Figma, terminal commands, paid APIs and a chosen frontend framework are not required just to discuss an idea.

## Design journey

1. **Source:** accept a system specification, PRD, plain idea or inspected existing app. Preserve existing R-ID/AC-ID/SR-ID/UC-ID/BR-ID and source labels. Do not invent research or unconfirmed business rules.
2. **Research:** record user task, role, context, entry, obstacles, alternatives, expected result. Hypotheses state setup, success, disproof and verification status; untested means NOT_TESTED.
3. **Flows:** actor actions from entry through choices, errors, recovery and reachable terminal outcomes. Markdown or optional Mermaid works without external rendering.
4. **Information architecture:** justify the fewest screens and map each mandatory action to a reachable role-permitted route.
5. **Wireframes:** record zones, content order, controls, navigation and empty/loading/error states. Text-only output is TEXT_SPEC, not a rendered image.
6. **Prototype:** describe each actionable component's event, initial/result/error state, transition, accessibility and acceptance criterion. Only claim INTERACTIVE_VERIFIED when actual interactions are tested.
7. **Visual design and design system:** existing brand, tokens, fonts, spacing and icons take priority. Use `design-system-consistency`; add minimal tokens only when justified, never a second independent source. Defer motion-specific questions to `motion-quality`.
8. **Component contracts:** stack-neutral inputs, events, variants, validation, disabled/loading/empty/error states, responsive and accessibility constraints. `component-architecture` owns engineering boundaries.
9. **Developer handoff and QA:** source requirements, screens/flows, actual assets if any, design decisions, component contracts, responsive/accessibility criteria, traceability and unresolved questions. For actual implementations use `screenshot-fidelity` and appropriate browser/QA testing. Matching screenshots alone do not prove behavior.

Trace example: `R1 -> UC1 -> FLOW-1 -> SCREEN-2 -> COMP-FORM -> AC1/AC2`. The [expense journal](../extensions/design/skills/ux-design-process/references/EXAMPLE_EXPENSES.json) and [role-aware work console](../extensions/design/skills/ux-design-process/references/EXAMPLE_WORKFLOWS.json) are synthetic design specifications, not implemented or visually verified applications.

## Additional review from three independent sources

Toolkit adopts **methods, not third-party installations**: clarify the product goal before visual choices, run a realistic data/error stress pass on actual UI inputs, compare genuinely different interaction patterns when a design decision is open, and keep critique separate from measured technical checks. Existing design tokens always take priority over another project's look.

Read the [original review/stress checklist](../extensions/design/skills/ux-design-process/references/REVIEW_AND_STRESS.md) for optional concrete cases (long localized text, zero/one/large values, missing records, authorization, offline, duplicate submit, dynamic viewport and keyboard). The [source assessment](../extensions/design/skills/ux-design-process/references/INSPIRATION_REVIEW.md) records the exact upstream revisions, licenses and what was intentionally excluded. No Impeccable binary, third-party skill pack or design-style database is bundled.

## Responsive and accessibility evidence

For each important screen propose representative mobile/desktop viewports (tablet when relevant), focus and keyboard access, zoom, long localized text, virtual keyboard, safe-area, overflow, errors and empty states. Proposed layout does not prove responsiveness. Apply relevant [WCAG 2.2](https://www.w3.org/TR/WCAG22/) criteria with their exceptions: focus, keyboard, labels, feedback, contrast, target size and reduced motion. Distinguish automatic checks, manual checks and assistive-technology trials. Never claim compliance from a checklist.

| Artifact | Honest readiness |
| --- | --- |
| Written screen/flow | TEXT_SPEC / PREPARED |
| Real static image | STATIC_RENDER / RENDERED with saved evidence |
| Working clickable prototype | INTERACTIVE_VERIFIED only with real observed actions |
| Production code | IMPLEMENTED; RUNTIME_VERIFIED requires runtime evidence |
| Owner-approved direction | OWNER_ACCEPTED only after explicit decision |

For professional teams see the [UX/UI contract](../extensions/design/skills/ux-design-process/references/UX_UI_CONTRACT.json), [manual acceptance](../extensions/design/skills/ux-design-process/references/MANUAL_ACCEPTANCE.md), and [read-only validator](../scripts/validate_ux_ui_spec.py). Structural PASS is not a browser or aesthetic test.

## Optional installation for text-only flow planning

The commands below install **`ux-design` for nonvisual planning only**. Run Python 3.12+ from the Toolkit root and replace `/path/to/project` with an existing project directory.

```bash
python scripts/skill_manager.py catalog --profile ux-design
python scripts/skill_manager.py install --target /path/to/project --profile ux-design
```

Check the proposed file list first. Only if it is correct, run installation and the illustrative validation separately:

```bash
python scripts/skill_manager.py install --target /path/to/project --profile ux-design --apply
python scripts/validate_ux_ui_spec.py extensions/design/skills/ux-design-process/references/EXAMPLE_EXPENSES.json
```

For visual design, start with `ui-orchestra` and follow the [new-design workflow](../.agents/skills/ux-ui-design-orchestra/references/CREATE_DESIGN.md). Copying files does not demonstrate live skill activation.

Preview writes nothing and install requires explicit `--apply`. Toolkit copies referenced for another person's task stay **read-only**; return their designs and reports in chat unless another destination is explicitly authorized. Actual AI-client skill activation, render, owner review and usability trials remain NOT_MEASURED / NOT_TESTED until performed.


## UX/UI Design Orchestra - native methods and preferred visuals

**Tool-native creative freedom:** the coordinator does not ban any styles, patterns or media by default. Use the original design skills as their authors intended; the product, user's stated taste and real project rules determine layout, typography, photography, gradients, cards, hero sections, SaaS/e-commerce patterns and animation. One direction, several quick drafts or a deeper comparison are all valid. A familiar pattern is not a defect merely because it is popular.

For new visual design, inspect relevant references, use the available original tool workflow and create real viewable previews before requesting owner approval. When alternatives are offered, compare the actual rendered images; never fabricate extra options or claim a tool ran because its documentation was consulted. A mobile-only screen can be reviewed on mobile; a responsive storefront may benefit from mobile and desktop captures.

When the owner prefers or has approved an earlier result, **retain a versioned visual baseline** (image refs and strengths) in the user's project/chat. A candidate replacement should be reviewed next to it at comparable viewport/state: composition, typography, imagery, visual expression and ease of completing the task. Keep/refine the earlier result if a revision offers no established benefit. Technical browser QA is separate from aesthetic review: CI and zero-overflow do not prove beauty.

No application edits before explicit approval of the particular design version. No original skill, rendering engine or specialist can be claimed active without actual invocation evidence. For explicit `ALL_THREE` policy see #449.

## Original design skills - explicit ALL_THREE mode (#449)

The existing `ui-orchestra` can use three **original, unmodified upstream skills** together when the user opts in to `original_design_skills.mode=ALL_THREE`. Toolkit does not bundle these external originals. The host checks active project/ancestor/user skill directories, installs missing required originals and tools after source/license/pin/file review within granted permissions, then verifies setup and invokes them. Prefer user scope and preserve existing files. Honor explicit no-install requests; if required setup is blocked, report the concrete reason rather than substituting reference methods. Do not infer invocation from a GitHub reference, local files, or a structurally passing report. See [task setup](INSTALLATION.md#automatic-setup-for-the-current-task).

Original upstream installation examples, **requiring source, license, version/file and hooks review before host execution** (choose the actual client's user scope where supported):

- [Impeccable](https://github.com/pbakaus/impeccable) - Apache-2.0 (preserve LICENSE/NOTICE): `npx impeccable install --providers=codex --scope=project`. Its launcher may download the engine on first use; native hooks can require a separate trust decision.
- [Taste Skill](https://github.com/leonxlnx/taste-skill) - MIT: `npx skills add https://github.com/Leonxlnx/taste-skill --skill design-taste-frontend`. Needs Node 22+ and Chrome, Edge or Chromium, and can use the network for image research.
- [UI UX Pro Max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) - MIT: `npm install -g ui-ux-pro-max-cli` then `uipro init --ai codex`. Needs Python 3.x for local design search.

These are upstream commands, **not actions automatically executed by Toolkit**. They do not invoke Codex CLI or Claude CLI, but still require installation/network review. Reproducible package identity requires an independently verified version pin and source file digests; latest npm/npx alone does not prove an immutable upstream source.

After installation, inspect local Codex-shaped skill folders without executing third-party scripts:

```text
python scripts/validate_ux_ui_orchestra.py --inspect-originals /path/to/project
```

Expected directories: `.agents/skills/impeccable`, `.agents/skills/design-taste-frontend`, `.agents/skills/ui-ux-pro-max`. `FILES_PRESENT_UNATTESTED` includes a local tree checksum but proves neither upstream provenance nor actual discovery and invocation by Codex Desktop. On an ALL_THREE design request, the coordinator requires three actual, evidence-backed invocations. If one is unavailable, it cannot claim the whole design package is ready for approval. Honest task-appropriate visual evidence and explicit owner approval remain required.
