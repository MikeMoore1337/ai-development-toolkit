# Original Emil Kowalski skills - selective UX/UI Design Orchestra routing

Source: [emilkowalski/skills](https://github.com/emilkowalski/skills), **MIT** (copyright Emil Kowalski, 2026); reviewed source commit: [`715c1807e08c497cfd1dc4feb450a2a3300ef2a9`](https://github.com/emilkowalski/skills/tree/715c1807e08c497cfd1dc4feb450a2a3300ef2a9). The upstream contains 18 `skills/<name>/SKILL.md` entrypoints. This file is a **routing index**, not a fork, installed bundle, or replacement for any original. Original skill prose, instructions and applicability rules remain authoritative.

## Selection by actual task

| Task / native scope | Original skill(s) | Orchestra stage |
| --- | --- | --- |
| Design engineering craft, interface polish and critique | `emil-design-eng` | `create-design`, `audit-proposal` |
| Apple-inspired interface *when the product brief calls for it*: gestures, spatial consistency, physical motion and typography | `apple-design` | `create-design`, `audit-proposal`; implement only after acceptance |
| Touch UX, PWA, mobile viewport, safe areas, scroll and installed-app feel | `mobile-native` | `audit-proposal`; changes in `implement-approved` |
| Extreme/empty/localized content and rendered-state stress | `break-ui` | Scope-check first: its native fixture/toggle workflow may require writes; do not claim completion during no-write audit |
| Codebase-wide motion improvement plan; opportunities for useful motion; excessive motion | `improve-animations`, `find-animation-opportunities`, `remove-animations` | First two read-only audits; `remove-animations` edits only in `implement-approved` |
| Motion implementation, coordinated transitions, drag/swipe and fluid interactions | `animate`, `choreograph`, `gestures` | `implement-approved` only |
| Dropped frames and animation throughput | `animation-performance` | Diagnose in audit; fixes after acceptance |
| Easing/interaction terminology | `animation-vocabulary` | Planning/brief as needed |
| React Native / Expo animation | `animate-expo` | Only an actual Expo app, `implement-approved` |
| Native Swift implementation | `write-swift` | Only an actual Swift task, `implement-approved` |
| Sonner toast integration | `ask-sonner` | Only a Sonner task, dependencies/changes after acceptance |
| Strict review of an animation diff | `review-animations` | **Explicit invocation only**; original declares `disable-model-invocation: true` |
| Comparing actual rendered UI variants via a picker | `prototype` | **Explicit invocation only**; original declares `disable-model-invocation: true`; respect output and no-write limits |
| Picking a UI component library | `pick-ui-library` | **Explicit invocation only**; original declares `disable-model-invocation: true`; installation requires a separate authorization |

The matrix covers all 18 upstream skills. It does **not** make all 18 necessary. Select at most the specialists relevant to the current screen, stack and request. Do not assume a web app uses Expo, Swift or Sonner. No default aesthetic style is prescribed; the project design contract and user preference win.

## Native source and invocation contract

1. UX/UI Design Orchestra remains the sole task coordinator. Inspect the consumer project's `AGENTS.md`, existing design tokens, accepted visual reference, UI stack, scope and approval gates. The external original leads its selected specialist method; do not rewrite, simulate or truncate it into a Toolkit substitute.
2. Before use, review the `SKILL.md` and referenced files at the pinned commit, including `skills/ask-sonner/API.md` when `ask-sonner` needs API definitions. Verify the actual native client install/discovery surface and review downloads, scripts, hooks, transitive dependencies and license before any allowed setup. Do not blindly run `npx skills@latest add emilkowalski/skills`: it is an **unversioned full-pack installer**, not this pinned selective integration. Do not overwrite existing skills or change user-global settings without permission.
3. Preserve upstream opt-out metadata. In particular, never auto-invoke `review-animations`, `prototype` or `pick-ui-library` where `disable-model-invocation: true`; an owner may explicitly select them. If an upstream method requires writing test fixtures or source changes while Orchestra is in `create-design`/`audit-proposal`/`audit-only`, keep the target read-only, report the blocked native stage, and never mark a partial method `INVOKED`/complete.
4. For every selected specialist, distinguish `REFERENCE_ONLY` (link/documentation), `FILES_PRESENT_UNATTESTED` (unverified client files), `LOADED` (pinned original `SKILL.md` actually read), and `INVOKED` (native skill method actually executed with an observed output/trace). Record `source_repo`, `source_revision`, `skill_name`, `method`, `client`, `status`, `evidence_ref`, and, when applicable, output/viewport. Never infer invocation from files, a citation, a downloaded package or a passing structural test.
5. In `STANDARD` mode this is a task-selected specialist source. In existing `original_design_skills.mode=ALL_THREE`, the required Impeccable / Taste / UI UX Pro Max trio **remains exactly three**, with its own exact-invocation approval gate. Emil specialists may complement the trio, but never satisfy one of its receipts or silently add a fourth mandatory gate.
6. Deliver truthful visual and browser evidence, relevant reduced-motion/keyboard/device checks, and the original coordinator's visual acceptance gate. No automatic paid APIs, production access, new daemon/queue, changes to Toolkit from consumer projects, application edits before approval, PR merge or deployment.

## Status boundary

A source/index change in Toolkit is **routing integration only**. Actual native discovery, installation, method invocation, browser inspection and usefulness are separate per-client/per-project evidence. If no authorized executor or design task exists, record `NATIVE_CLIENT_E2E_NOT_VERIFIED` rather than announcing that a skill was used.
