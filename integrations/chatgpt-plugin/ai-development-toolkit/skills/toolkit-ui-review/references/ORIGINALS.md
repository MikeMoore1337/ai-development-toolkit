# Original design skills in ordinary ChatGPT

This is an adapter for the existing Orchestra, not a second design workflow. Keep each selected original's source, applicability, methods and fallback unchanged.

## Resolve the user's existing choice before drawing

Read [packaged user preferences](../../toolkit-task-router/references/USER_PREFERENCES.json). The document uses the existing `scripts/toolkit_preferences.py` schema. The public package leaves it empty; a private, owner-edited package may persist `skills.design_originals=ALL_THREE`. Never copy a personal value into the public default.

Treat an observed packaged personal choice or an explicit standing user instruction as a user-layer preference. Preserve explicit project/task overrides and the current user's request; a directly selected original controller still takes precedence over Toolkit coordination. An absent preference file or a preview value whose source is `defaults` is not an explicit `STANDARD` opt-out. Do not silently erase a known standing choice because the current sandbox has no local user configuration. Do not claim to have read Windows/local settings when the source was the plugin. The existing resolver accepts a packaged JSON via `--user-config` when a real host runner is available; reading these instructions does not execute it.

For `ALL_THREE`, an ordinary substantial design request, including "нарисуй макет" or "design a mockup", already selects the originals. Do not ask the user to list their names or repeat the setting. Without an observed choice, keep the public `STANDARD` route. A routing preference does not authorize installation, binaries, hooks, paid APIs, project edits, merge or deployment.

## Load, check applicability, then use the originals

Before the final image/render, obtain and read each selected original's complete `SKILL.md` and the references needed by its own workflow. Prefer an actually discovered installed skill. Otherwise inspect the canonical source, pin one immutable revision, review license/files/runtime, and perform task-required setup within existing permissions. Do not end discovery after reading only Toolkit's coordinator or an upstream README summary.

| Exact original | Canonical source | Skill entry to verify at the selected revision |
| --- | --- | --- |
| `impeccable` | `https://github.com/pbakaus/impeccable` | `.agents/skills/impeccable/SKILL.md` |
| `design-taste-frontend` | `https://github.com/Leonxlnx/taste-skill` | `skills/taste-skill/SKILL.md` |
| `ui-ux-pro-max` | `https://github.com/nextlevelbuilder/ui-ux-pro-max-skill` | `.claude/skills/ui-ux-pro-max/SKILL.md` |

Verify the actual entry paths and declared names; upstream layouts may change. No originals or executables are embedded by this adapter. Preserve licenses/NOTICE and relative references when installing. A URL is `REFERENCE_ONLY`; a full source read is `LOADED`; files do not prove native client discovery.

Check each original's own scope against the requested **surface and deliverable**, not the product name alone. If it explicitly excludes that surface, record `NOT_APPLICABLE_NATIVE_SCOPE`, its immutable source reference and the concrete reason. Do not force it, silently substitute another skill from the same repository, or count the exclusion as `INVOKED`. Continue the applicable work and identify the incomplete all-three result. The existing strict all-three approval gate still requires three actual invocations.

For a static image request, execute the original's applicable research, shaping and concept steps before rendering. A missing HTML application is not by itself a reason to skip these steps. If a command requires a working directory, use an authorized isolated design workspace with only the real supplied brief and explicitly stated assumptions; do not invent existing product documents. Preserve an image-only request's scope. Browser/DOM/build stages requiring an implementation remain unperformed, not successful.

Use available original scripts for the required stages after runtime/source review. If an original permits a launcher-failure fallback, follow its exact disclosure and remaining playbook. Record the applied playbook and its task-specific output separately from an engine that did not run. "Recommendations considered" without the actual steps/output is not evidence of a completed original workflow. A required engine invocation cannot be satisfied by that fallback.

## Render and report the real contribution

The final rendering may use the host's image generator when the request and original workflow permit it. Attribute that rendering separately; it does not establish original-skill invocation. Before final rendering, account for every selected original: applicable work completed, a sourced native exclusion, or a concrete setup/execution blocker. Do not silently shortcut an applicable required original to image generation.

Report briefly for each original: source/revision actually read, applicability, work/output that informed this design, and script/engine status with observed evidence. Keep loaded guidance, applied instructions, actual script invocation, full original workflow, browser verification and the user's visual approval distinct. Context discovery, `--help`, structural validation and a generated picture alone cannot establish a full all-three design run.

The optional Orchestra receipt supports `NOT_APPLICABLE_NATIVE_SCOPE` only with `loaded=true`, a pinned `source_revision`, nonempty `applicability_reason` and `applicability_source`, and no `invocation_evidence`. Such a receipt documents an incomplete result; it does not make the all-three approval gate pass. Source-contract tests cannot prove that a new ChatGPT conversation will select and apply the skills: verify that separately with the ordinary request and actual trace.
