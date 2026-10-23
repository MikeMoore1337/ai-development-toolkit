# Selective adoption of external methods (October 2026)

This policy complements `SOURCE_EVALUATION.md`, `SKILL_EVALS.md`, `SKILL_ROUTING_EVALS.md`, the `external-skill-review` skill, and `MANIFEST.json`. It installs **no skills** and does not grant write access to Toolkit when used by somebody else's project.

## Source decisions

| Sources | Adopt in Toolkit | Gate |
|---|---|---|
| `obra/superpowers` | Evidence-before-completion, systematic debugging and scoped review methods | No parallel controller or universal TDD mandate |
| `anthropics/skills` | Apache-2.0 `skill-creator` paired evaluation and activation ideas | Inspect licenses **per skill**: `docx/pdf/pptx/xlsx` have restrictive terms against outside copying and derivatives |
| `daymade/claude-code-skills/frontend-visual-qa` | Observable route/state/viewport and real-browser outcome criteria for existing QA skills | Stored screenshots alone are not proof of correct UX |
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

## Routing by task type

- **Product UI:** verify user journeys, responsive states, accessibility and performance; retain approved visual contracts rather than imposing a generic style.
- **Agent infrastructure:** separate interface development from resident runtime permissions, model budgets and service activation gates.
- **Privacy-sensitive applications:** respect local data boundaries and require explicit confirmation before state-changing operations.
- **Toolkit:** prioritize real skill quality measurement and activation routing over catalog size.

This document does not install any external tool or establish real-agent performance. Representative original repositories: https://github.com/obra/superpowers · https://github.com/anthropics/skills · https://github.com/daymade/claude-code-skills/tree/main/frontend-visual-qa.
