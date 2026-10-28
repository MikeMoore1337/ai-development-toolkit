# Selective adoption of external methods (October 2026)

This policy complements `SOURCE_EVALUATION.md`, `SKILL_EVALS.md`, `SKILL_ROUTING_EVALS.md`, the `external-skill-review` skill, and `MANIFEST.json`. It installs **no skills** and does not grant write access to Toolkit when used by somebody else's project.

## Source decisions

| Sources | Adopt in Toolkit | Gate |
|---|---|---|
| `obra/superpowers` | Evidence-before-completion, systematic debugging and scoped review methods | No parallel controller or universal TDD mandate |
| `anthropics/skills` | Apache-2.0 `skill-creator` paired evaluation and activation ideas | Inspect licenses **per skill**: `docx/pdf/pptx/xlsx` have restrictive terms against outside copying and derivatives |
| `daymade/claude-code-skills/frontend-visual-qa` | Observable route/state/viewport and real-browser outcome criteria for existing QA skills | Stored screenshots alone are not proof of correct UX |
| `benjitaylor/agentation` | Optional local element annotations routed into the existing UI orchestra and screenshot-fidelity | **PolyForm Shield 1.0.0, not MIT**; no auto-install, remote submission, source redistribution or production widget |
| `vercel-labs/agent-browser` | Optional isolated pilot only if Playwright cannot solve a specific task | No cookie exports, production sessions, default CI dependency |
| `coreyhaines31/marketingskills`, `wondelai/skills` | Reference CRO/SEO, JTBD and customer research methods | No marketing agent runtime, paid API or duplicate roles |
| `199-biotechnologies/claude-deep-research-skill` | Claim-level provenance, DOI/source checks and independent corroboration | No paid search providers, search-cli or research controller added |
| `pbakaus/impeccable`, `nextlevelbuilder/ui-ux-pro-max-skill`, `Leonxlnx/taste-skill`, `ibelick/ui-skills`, `iart-ai/web-animation-skills`, `LottieFiles/motion-design-skill` | Selective design, accessibility, motion and screenshot review practices | Product-approved visual contracts override stylistic preferences; no upstream hooks |
| `antfu/skills` | Versioned Vite/Vitest documentation-reference approach | Check current versions and official docs |
| `shadcn-ui/ui`, `starc007/ui-components`, `cosscom/coss` | Component design concepts only; note `cosscom/coss` is a communications platform | Per-directory licensing (AGPL/MIT), accessibility and dependency audit |
| `motiondivision/motion`, `greensock/GSAP`, `airbnb/lottie-web` | Runtime dependency comparison, not agent skill copying | Evaluate license, bundle, reduced-motion and maintenance per project |
| `heygen-com/hyperframes`, `remotion-dev/remotion`, `remotion-dev/skills` | Video tooling only for an explicit deliverable | Evaluate Remotion's special license, local rendering cost and paid-service independence |
| `ailabs-393/ai-labs-claude-skills` | Reject package install | `postinstall` may copy skills into host project; value not established |

## Adoption protocol

1. Define the missing capability, owning project's Issue, existing competing workflow, original source URL and provenance SHA if content is imported.
2. Review file-level licenses; all scripts, postinstall hooks, binaries, network calls and possible access to tokens, cookies and private data. `reject` is a valid outcome.
3. Define positive, negative and collision activation prompts (novice and expert). Record expected routing before running tests. Never install globally for an evaluation.
4. For actual effectiveness testing, use repeated paired baseline/candidate trials with the same pinned repository SHA, model, tools and permissions. Alternate run order where possible. Keep evidence outside Toolkit. Score with `python scripts/skill_eval.py <dataset.json>`.
5. Independent review records accepted criteria, regressions, unsafe actions, false success claims, missing data and actual limitations. Synthetic fixture success must not be passed off as model performance.
6. Choose `reuse existing`, `reference only`, `adapt`, `isolated install`, or `reject`. For adaptation author original minimal instructions instead of copying content with incompatible terms.
7. Update manifests, tests and bilingual documentation in the normal PR if a real skill changes. Never persist other users' reports, logs or code inside Toolkit.

## Applying selected Superpowers methods (#400)

See [evidence, worktrees and session diagnosis](SUPERPOWERS_EVIDENCE.md). Existing `feature-delivery`, `code-review` and `release-safety` skills reference the methodology without a new execution controller. Host-native isolation, target-repository leases, actual test evidence and release authorization prevail. Session token/retry observations must not become automatic telemetry collection.

## UI primitives and effects (#408)

The [portable shadcn/ui and Magic UI selection gate](UI_COMPONENT_SELECTION.md) supports the existing frontend and design skills. Prefer the consumer's current primitives before any external package. Verify component-specific source/license revision, Tailwind/Radix/Motion dependency cost, actual keyboard/reduced-motion checks and the owner's exact visual approval. `PROPOSAL_ONLY` does not imply `OWNER_ACCEPTED`. `scripts/validate_ui_component_adoption.py` is an optional offline structural check, not a package installer or proof of deployment.

## ECC as a source for standalone Toolkit (#431, #446)

**External ECC installation is superseded.** Toolkit is a standalone product: adopt only verified missing capabilities by properly attributed licensed source port or integrate native equivalents into existing Toolkit modules. Do not require `ecc-universal`, ECC plugin/MCP/CLI, separate hook bootstrap or sidecar. Already merged upstream source CI smokes are comparative evidence, **not built-in Toolkit functionality**. [Current architecture](ECC_NATIVE_CODEX.md); obsolete [external plugin issue #424](https://github.com/MikeMoore1337/ai-development-toolkit/issues/424) is closed `NOT_PLANNED`. The [601-component gap catalogue #435](https://github.com/MikeMoore1337/ai-development-toolkit/issues/435) remains selection evidence, not permission to copy all source.

## Applying methods across project types

- **User-facing application:** improve visual QA, accessibility, animation and performance while respecting its established design system and approval workflow.
- **Agent-based service:** verify signal provenance, evidence and action constraints. Do not insert interface skills into resident processes by default.
- **Application with private data:** preserve access boundaries, explicit authorization for external actions and data-handling constraints.
- **Tool and skill library:** prioritize reproducible evaluations and accurate skill routing over catalog size.

This document does not install any external tool or establish real-agent performance. Representative original repositories: https://github.com/obra/superpowers · https://github.com/anthropics/skills · https://github.com/daymade/claude-code-skills/tree/main/frontend-visual-qa.
