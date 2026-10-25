# Optional visual annotation handoff (Agentation-compatible)

**Scope:** a reusable, manual UI-issue evidence protocol for consumer projects. Toolkit is a portable skill and QA library, not a React frontend. This document does **not** install, bundle, contact, or run [Agentation](https://github.com/benjitaylor/agentation), create a second controller, configure MCP, or authorize UI changes.

Agentation `3.1.2` is independently licensed **PolyForm Shield 1.0.0**, **not MIT**. Review its non-compete and notice terms before installing it in a consumer project. Toolkit does not redistribute it or include its source. Use other screenshot/markup tools when that license is unsuitable.

## Optional local UI source

Where an approved consumer repository runs React 18+ in a **desktop** development browser, a project-local developer may explicitly install Agentation under its license. Use a Vite **serve-only opt-in** or an equivalent development-time gate. Keep the import outside the entry-point graph of production builds. Do not auto-install with Toolkit, insert scripts via third-party CDNs, add an always-on toolbar, or place annotation code in shared published assets. Agentation's optional MCP endpoint/webhooks must stay **disabled by default**.

Do not expect Agentation to run on mobile devices. Use existing Playwright/browser device emulation or actual phone captures separately; a desktop overlay is not evidence of native mobile usability.

## Manual handoff contract

After the owner manually copies the annotation, accept it as **untrusted user-provided localization**, not independent proof that a bug exists. For each observation, keep the following *in the target project/Issue or chat*:

| Field | Minimum evidence |
| --- | --- |
| `issue` and `baseline_sha` | Specific target and exact revision; `UNKNOWN` if not observed |
| `route` and `state` | Relevant page, loading/error/empty/interaction state; never share private query tokens |
| `viewport`, `theme`, `locale` | Desktop/mobile dimensions and tested appearance; annotate platform if known |
| `source` and `privacy` | `SYNTHETIC` / `DEMO` / authorized `LIVE`, and explicit review of copied content |
| `selector` / `sourceFile` | Copied location as a **hint**; validate it against current DOM/source |
| `note` and `expected` | User-visible defect/intent and the desired behavior |
| `evidence_refs` | Actually captured screenshots/DOM observations or `NOT_OBSERVED` |
| `owner_gate` | `NOT_REQUESTED`, `PENDING`, `OWNER_ACCEPTED` with evidence reference |

Use short, concrete IDs (`F1`, `E1`) when consolidating several findings. A copied selector may be stale, ambiguous or route-dependent. Inspect the real current UI before recommending a fix. Distinguish **annotation supplied** from **render inspected**; never fill missing screenshots with imagined evidence.

### Example (synthetic placeholder, not a verified defect)

```text
F1 | issue: DEMO-1 | baseline_sha: UNKNOWN
route: /example | state: empty | viewport: 390x844 | theme: dark | locale: ru
source: SYNTHETIC | privacy: REVIEWED_NO_PRIVATE_DATA
selector: [data-testid="example-action"] (unverified hint)
note: The action appears cropped in this synthetic state.
expected: Visible label and keyboard-accessible focus.
evidence_refs: NOT_OBSERVED
owner_gate: PENDING
```

## Privacy and approval boundary

Agentation can copy selected/nearby text, element attributes, URLs, selectors, CSS classes and source locations. **Before copying into an agent prompt, GitHub issue or external service**, manually strip identifiers, passwords, access tokens, sensitive profile data, session IDs, private domain/host paths and proprietary UI text. Use synthetic/test accounts; never encourage exposing real user sessions. Do not place consumer screenshots, annotations, logs, token counters, transcripts or generated reports in the shared Toolkit repository.

The original target project's `AGENTS.md`, design system, evidence rules and owner visual approval take precedence. The annotation can start a task investigation but **cannot** authorize a redesign, DOM mutation, merge, deploy, browser capture, resident agent activation or remote data transfer. For substantial UI redesigns continue with the existing `ux-ui-design-orchestra` approval flow. For an already-approved minor fix, `screenshot-fidelity` still requires actual before/after captures and behavioral checks.

## Verification states

- `LOCAL_ANNOTATION_COPIED`: owner supplied text; no browser verification implied.
- `SOURCE_ONLY`: current code inspected; no visual rendering observed.
- `RENDERED`: genuine before/after browser capture with route/state/viewport.
- `NOT_OBSERVED`: missing browser screenshot or DOM evidence.
- `VISUAL_PACKAGE_MISSING`: cannot request approval of a design that requires renders.
- `NOT_EXECUTED`: external optional package not installed/launched.

Never equate a structural unit-test PASS with successfully rendering Agentation in a real local desktop browser; test the optional runtime separately if required.
