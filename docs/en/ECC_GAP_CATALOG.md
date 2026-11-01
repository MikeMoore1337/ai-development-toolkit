# Full original ECC 2.2.3 gap catalogue (#435)

Source is pinned to affaan-m/ECC commit 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b. The read-only scripts/ecc_gap_catalog.py report generator inventories ALL tracked skills, agents, commands and rules from the original Git tree. The read-only catalogue generator does not copy ECC source; seven separately approved native skills are bundled in Toolkit; the historical October batch of four and the November addition are described below. Each component has source path, content digest, description and trigger, license claim, registered component and dependency/host declarations, Toolkit analogue, reasoned status, benefit and a test case.

GitHub Actions ecc-gap-catalog.yml publishes the reproducible ecc-full-gap-matrix artifact: ecc-gap-full.csv, ecc-gap-full.json, and ecc-gap-summary.json. Headline marketing counts may differ from the pinned source: use the measured inventory. Unassessed items are explicitly HOLD_REVIEW, not silently skipped. Root MIT license assertions do not independently attest transitive dependency rights or source security.

## Native Toolkit delivery vs historical ECC installer

**Already included in Toolkit (28 October 2026):** `contract-first`, `api-connector-builder` and `code-tour` were merged via [PR #448](https://github.com/MikeMoore1337/ai-development-toolkit/pull/448), and `windows-desktop-e2e` via [PR #453](https://github.com/MikeMoore1337/ai-development-toolkit/pull/453). They are now `ALREADY_PRESENT` in the reviewed catalogue, with exact local paths. The first three retain original pinned MIT `SKILL.md` files; Windows UIA has a compact native entry and complete unchanged licensed upstream reference. Installation uses Toolkit Skill Manager alone, not ECC CLI, shared modules, plugin, MCP or sidecar. Source CI passed; real Codex Desktop activation and native Windows GUI E2E remain `NOT_VERIFIED` (#450).

## Original selective installation route (historical upstream test, not the product path)

Upstream already ships catalog.js and install-plan.js --skills. Our CI tests the original read-only plan for windows-desktop-e2e with --target codex, in a disposable HOME. That upstream-only result was `ADOPT_AS_IS_CANDIDATE` / `HOLD_SHARED_MODULES`, due to shared modules and possible AGENTS/config changes. It does **not** apply to Toolkit's merged and separately tested native selective installer; ECC installation is neither required nor recommended.

Two original skills have now completed functional comparison against existing native Toolkit mechanisms (reviewed batch #435, 28 October 2026):

- **`skills/change-impact` - ALREADY_PRESENT after native uplift**: `extensions/qa/skills/change-impact-analysis/SKILL.md` plus `scripts/qa_change_impact.py` already cover code, caller, contract, data and regression risk surfaces. The existing `feature-delivery` controller now includes explicit *planned impact vs actual diff* reconciliation, without modifying the SHA-bound protected QA source; it explicitly flags scope drift and unverified boundaries. No second impact controller or force-created document tree.
- **`skills/tdd-workflow` - ALREADY_PRESENT after native uplift**: `.agents/skills/feature-delivery/SKILL.md` now supports an opt-in RED / minimal GREEN / refactor evidence cycle within the existing feature controller. We deliberately reject upstream's universal 80% coverage mandate, all-layer testing, automatic checkpoint commits and package-manager detector as global requirements.
- **`skills/continuous-learning` v1 - HOLD_UNSUPPORTED**: ECC marks it deprecated. Its v2 successor remains separately under #436.

These two classifications are *functional workflow coverage*, not byte-identical ports, observed model improvements, or a claim that all ECC components have been reviewed. Original source: `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, paths `skills/change-impact/SKILL.md` and `skills/tdd-workflow/SKILL.md`. The older gap-matrix artifact has superseded statuses until rerun against the reviewed catalog; it does not reflect current native delivery. See `catalog_review.json` for tested scenarios and evidence limits.

No Codex or Claude CLI, paid API, automatic client installation, resident hooks, session ingestion or production change is authorized. Official targets for other users remain optional with separate consent. Passing a source-only CI is not verified Windows Codex Desktop or Hermes runtime activation. Rollback: remove the optional CI and report generator in a reviewed PR.

To reproduce using trusted local checkouts: python scripts/ecc_gap_catalog.py --ecc-root /isolated/ECC --toolkit-root . --source-revision 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b --output-dir /tmp/ecc-gap

Manual comparison of original ECC api-design, database-migrations and e2e-testing with the actual Toolkit skills confirms their core functions are ALREADY_PRESENT, with exact analogue paths in the matrix. The upstream --skills windows-desktop-e2e plan expands to FOUR modules (platform-configs, skill-unified-memory, workflow-quality, shared-script-utils); the *original ECC installer* therefore remains `HOLD_SHARED_MODULES`. Toolkit's built-in Windows UIA skill can be installed independently with its Skill Manager; real Windows app execution still needs authorization and live verification.

## Source review and native batch (1 November 2026)

Original pinned MIT `skills/module-regression` is bundled as optional `native-module-regression`: byte-exact source, REGRESSION.example.md template and license. Existing change-impact guidance identifies risks; this skill links affected modules to executable, permission-gated acceptance commands and actual exit codes. Offline tests establish source identity/installer behavior, not live client routing (NOT_VERIFIED).

Other source-read decisions: `skills/verification-loop` and `skills/production-audit` are `ALREADY_PRESENT` via existing feature/release controls; do not impose universal 80% coverage or arbitrary numerical release scoring. `skills/repo-scan` is `HOLD_UNSUPPORTED` because it installs another external repository; `agents/build-error-resolver.md` stays `HOLD_CONFLICT` owing to Claude-only delegation and destructive command defaults. Five decisions here do not imply all 601 original components have been semantically audited. The GitHub Actions full matrix artifact needs a separate rerun; other entries retain review/conflict holds.

## Additional ECC source decisions (1 November 2026)

Four pinned original ECC skills were examined. `architecture-decision-records` is `ALREADY_PRESENT`: Toolkit's existing `architecture-decisions` covers durable choices and optional ADRs; a numbered template alone does not prove a new capability. `ai-regression-testing` is `HOLD_CONFLICT` because it couples Next.js/Vitest with a Claude-specific bug-check and blanket advice not to test new code without previous bugs; Toolkit preserves risk-based tests for new critical functionality. `codebase-onboarding` is `HOLD_CONFLICT` because it proposes host-specific CLAUDE.md writes without a separate owner permission; knowledge-map and code-tour already provide source discovery. `test-collaboration` remains `HOLD_REVIEW`: its TESTS.md and TEST-ID registry might help, but incremental benefit over existing requirement traceability and test management has not been measured. No source was imported or installed. The maintained semantic decision count is now 19/601, not a complete audit.

## Error handling and related source review (1 November 2026)

The original pinned `skills/error-handling` MIT SKILL.md is bundled unchanged as optional `native-error-handling` through existing Skill Manager, with no ECC runtime. Its concrete TypeScript/Python/Go error classes, response handling, retries and user-error examples add specialized guidance beyond Toolkit's general API design and reliability testing. Original examples are not automatic operations or new mandatory API contracts; real client activation remains NOT_VERIFIED.

Seven further originals were compared: `benchmark-optimization-loop` is ALREADY_PRESENT via performance-load-testing; `search-first` and `docker-patterns` are HOLD_CONFLICT due automatic agent, package or ECC-specific runtime assumptions; `security-scan` is HOLD_UNSUPPORTED as it requires external AgentShield and optionally paid Anthropic API; `iterative-retrieval`, `agent-security-hardening` and `benchmark-methodology` remain HOLD_REVIEW pending measured added value and existing #432 scope alignment. These eight decisions are not a claim to complete semantic review of the whole 601-component catalogue.

## Browser, accessibility, Python and frontend source review (1 November 2026)

Nine additional pinned ECC 2.2.3 original skill files were read at `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b` and compared against real Toolkit skills. Exact original file Git blobs are recorded per decision in `integrations/ecc/catalog_review.json`. This is **source-level classification only**; no runtime, agent, browser, model, installation or visual owner acceptance was executed.

- **ALREADY_PRESENT:** `browser-qa` (browser-workflow-evidence + Playwright + accessibility and release evidence), `frontend-a11y` (accessibility-testing + component practices), `seo` (existing evidence-based seo-audit). Browser, AT and real website outcomes remain NOT_VERIFIED; the original browser skill's Claude-specific MCP and `/canary-watch` are not assumed installed.
- **HOLD_CONFLICT:** `python-testing` prescribes always-on TDD, global >=80% coverage and 100% critical paths, conflicting with Toolkit's project/risk-based opt-in testing contract. Pytest concepts themselves can be reused where justified.
- **HOLD_UNSUPPORTED:** `agent-eval` is a guide to an unreviewed external agent-eval CLI, external coding agents and potentially paid judges; no owner-side runtime or cost permission.
- **HOLD_REVIEW:** `react-testing` (React Testing Library/MSW, hooks), `fastapi-patterns` (FastAPI/Pydantic v2/SQLAlchemy), `design-system` (token extraction, HTML preview), `python-patterns` (language-specific reference). These may contain useful focused material; a real fixture, dependency/security validation and a collision comparison are required before native inclusion.

The maintained catalogue now records **36 of 601** semantic decisions; **565 remain without a substantive decision**. Existing six opt-in native ECC-derived skills and their registration are unchanged. Source-based analogy is not live browser/client/AT/E2E verification. No ECC runtime, installation plan, auto-spend, new controller, or third-party script was introduced.

## Native MCP dependency review and two P0 comparisons (1 November 2026)

Three original MIT skills at the pinned ECC 2.2.3 commit were reviewed against real Toolkit sources. Original `skills/mcp-dependency-review` is now bundled **unchanged** as the seventh opt-in native Toolkit skill (`native-mcp-dependency-review`) with a retained MIT notice and exact upstream Git blob `4b08af8b05d44a0301693fc025a60ca5f4e8ee6d`. It provides a static *source-guided* review of npm/npx, Python/uvx/pipx and Docker MCP selector mutability, a narrow gap beyond existing `external_skill_gate.py` checks of authorization, secrets and install-on-use. It does not implement or execute a scanner, launch any MCP server, query registries, fetch packages or change user configuration; `SAFE` means only that the direct selector is exact.

Original `click-path-audit` remains HOLD_REVIEW until a real React/Zustand sequential-state regression comparison establishes added value and verifies no unsupported `/superpowers` or automatic agent spawning. Original `agent-architecture-audit` remains HOLD_CONFLICT for global automatic use because it mandates an additional agent release gate and requests Read/Write/Edit/Bash tools. Its focused diagnostic may be used only under separately selected original-tool and permission boundaries. Neither source-level review nor installer CI proves actual client selection or useful defect detection: **NOT_VERIFIED**. Maintained catalogue now **39/601**; **562** not substantively decided. No ECC runtime or paid service.

## Selective native Toolkit additions and source-wide triage (1 November 2026)

Six further unmodified MIT originals are now bundled as separate **opt-in** Toolkit profiles: `agent-introspection-debugging` (diagnose stalled tool-using agents), `content-hash-cache-pattern` (path-independent file-cache strategy), `loop-design-check` (bounded agent-loop goals), `make-interfaces-feel-better` (specific UI polish by explicit request), `article-writing` (source-grounded long-form content drafts for SEO), and `click-path-audit` (trace sequential action/store resets). Original workflow directions remain inside each standalone source; user/host permissions govern execution. The UI polish skill is **not automatically added** to UX/UI Orchestra; no new global visual rules or controllers, no automatic publishing or agent subprocesses. Original Git blob SHA pins and MIT notices are recorded in the maintained source catalogue and provenance.

Full pinned-source screening is added to the **existing** `scripts/ecc_gap_catalog.py`. It reads all 601 tracked primary files and emits `ecc-relevance-source-triage.json` alongside the existing full inventory. The report groups potential relevance to development, testing, design and SEO, flags references to external tools or writes, and identifies remaining deep-review work. **It is automated triage, NOT individual functional/security review, benchmark, license-chain attestation, or permission for installation.** Current maintained manual source decisions **44/601**, **557 pending deeper review**. Native opt-in bundles **13**; original source/installation CI does not verify real client activation or skill effectiveness (NOT_VERIFIED).

## Native editorial voice and source-first content profiles (1 November 2026)

Two further unchanged MIT originals ship as separately selected `native-brand-voice` and `native-content-engine`; `native-editorial-suite` intentionally selects both to retain the upstream coordinated workflow. The complete original voice-profile schema and attribution are bundled. This adds repeatable voice extraction from authorized examples and different platform-native drafts based on a real source document, without publishing or network calls. The original optional X API and crosspost tools are not installed. Current maintained manual decisions: **46/601**; **555** require further in-depth review. Full source triage remains explicitly non-approving. Total optional native ECC-derived skills **15**, live client/SEO improvement NOT_VERIFIED.

## Exact Git blob verification for every reviewed source (1 November 2026)

All **46/46** maintained individual source decisions now include their primary-file `source_blob` SHA-1, checked against the immutable ECC 2.2.3 Git tree (the prior 27 historical entries had no per-file blob field). The inventory generator rejects missing/malformed/mismatched manual source blob claims and a tracked source/manifests checkout modified after the pinned commit. It resolves Git object identities without executing instructions, scripts, hooks or installers from ECC. Negative tests cover absent, malformed, mismatched hashes and dirty worktrees. `source_blob` identifies the **primary file only**; `sha256_component` remains a separate digest of all tracked component files. Exact provenance is not evidence of copyright ownership, useful behavior, model/client activation or manual assessment of the remaining **555** components.

## Cross-stack pinned source review: 14 additional skills (1 November 2026)

Fourteen original ECC 2.2.3 SKILL.md primary files were read and compared against concrete Toolkit skills. Each new catalogue entry records the exact pinned Git blob, specific compatibility/security reasoning and a falsifiable next test. **ALREADY_PRESENT (3):** `backend-patterns`, `security-review`, `deployment-patterns` via existing backend, security and DevOps/release skills. A second generic controller would duplicate functionality.

**HOLD_CONFLICT (3):** `github-ops`, `docs-governance`, `cost-aware-llm-pipeline`. The upstream material introduces unapproved gh/stale-closing operations, ECC-only governance commands or automatic paid model routing with an inadequate pre-call budget guard. **HOLD_REVIEW (8):** `accessibility`, `mcp-server-patterns`, `i18n-sync`, `react-performance`, `postgres-patterns`, `skill-host-compat`, `frontend-design-direction`, `conventional-commit-review`. Mobile assistive technology, MCP SDK validation, JSON locale preservation, React measurements/source rights, PostgreSQL RLS/configuration, host-specific lint, original visual checker/hosted research, and personal-origin commit-message rights need targeted verification before any optional adoption.

**Maintained review coverage: 60/601, 541 remain.** No additional native skill or runtime is bundled in this batch. Original-tool behavior and explicit owner permissions remain authoritative. The new branch still requires pinned-source inventory CI and exact-head repository validation; installed AI-client effectiveness, independent rightsholder chain and release remain NOT_VERIFIED. Earlier counts are historical checkpoints.

## Agent runtime, context, research and workflow review: 25 pinned originals (1 November 2026)

Reviewed 25 original ECC 2.2.3 `SKILL.md` primary files against actual Toolkit skills, scripts and the applicable host/owner boundaries. All entries record independent primary Git blob SHA from the pinned upstream commit, concrete rationale, analogue, benefit and falsifiable follow-up case. This is semantic *source* review, not agent execution, runtime rights attestation or observed efficacy.

**ALREADY_PRESENT (2):** `prompt-optimizer`, `benchmark`. Existing prompt-refinement and measured performance workflows cover the central user intent without creating an ECC controller or automatic `.ecc/benchmarks` files.

**HOLD_CONFLICT (8):** `autonomous-agent-harness`, `agent-self-evaluation`, `documentation-lookup`, `git-workflow`, `gateguard`, `rules-distill`, `project-flow-ops`, `token-budget-advisor`. These ask for Claude-specific resident automation/hooks, subjective completion scores, automatic Context7 routing, generic merge/deploy, global rule rewriting, mandatory Linear authority or a token-choice dialogue. Explicitly chosen upstream tools still follow their own workflow within host/user permissions; none becomes a default Toolkit rule.

**HOLD_UNSUPPORTED (3):** `codehealth-mcp`, `skill-comply`, `deep-research`. The originals require CodeScene, Firecrawl/Exa or `claude -p` live runtimes and potential authentication, external data flows and costs. No such runtime is packaged or silently activated.

**HOLD_REVIEW (12):** `agent-harness-construction`, `agent-runtime-gateway-smoke-test`, `continuous-learning-v2`, `context-budget`, `prompt-caching-strategy`, `eval-harness`, `regex-vs-llm-structured-text`, `canary-watch`, `config-gc`, `workspace-surface-audit`, `skill-scout`, `skill-stocktake`. These have possible incremental value for agent action-space schemas, gateway E2E, project-scoped learning (separately owned by #436), native-client context meters, prompt caching, eval/structured-text oracles, bounded canary watching, configuration and tool inventory, and safe skill discovery. Each needs isolated executable evidence, provenance/rights and effect measurement before adoption.

**Current maintained source decisions: 85/601. Remaining 516 need substantive review.** No new original source files, Skill Manager registration, global controller, hooks, paid APIs, installed-client verification, merge, deployment or release in this batch. Exact-head CI and the pinned-source catalogue workflow must pass separately. The earlier 60/601 count above is the previous checkpoint.

## Practical candidate-value proof: agent QA and context (1 November 2026)

Four `HOLD_REVIEW` originals were compared with existing functionality:
`eval-harness`, `agent-harness-construction`, `context-budget` and
`prompt-caching-strategy`. The only proved **offline reporting** gap in
this round is in `scripts/skill_eval.py`: overall paired acceptance
could hide a task's repeated-run instability. An opt-in
`--observed-repeatability` now reports first-trial, within-three, and
all-three clean-success rates from already recorded verdicts, without
another evaluation runtime, model or package. A synthetic three-task
fixture keeps pooled acceptance at 6/9 in both conditions while
all-three success differs 2/3 versus 0/3. Missing repetitions yield null,
not false success; risky recorded actions cannot count as clean success.

`eval-harness` remains `HOLD_REVIEW` for actual model execution and
independent graders. `agent-harness-construction` still lacks a measured
tool-use comparison; `context-budget` cannot convert measured source
bytes to live provider tokens; `prompt-caching-strategy` needs real
provider receipts and privacy/cost verification. **No original skill
was imported or reclassified; coverage remains 85/601, 516 outstanding.**
See [existing scorer](../SKILL_EVALS.md) for a reproducible, offline-only
test. All model efficacy remains `NOT_MEASURED`.
