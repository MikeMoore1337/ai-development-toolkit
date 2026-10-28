# Full original ECC 2.2.3 gap catalogue (#435)

Source is pinned to affaan-m/ECC commit 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b. The read-only scripts/ecc_gap_catalog.py report generator inventories ALL tracked skills, agents, commands and rules from the original Git tree. The read-only catalogue generator does not copy ECC source; four separately approved native skills are bundled in Toolkit as described below. Each component has source path, content digest, description and trigger, license claim, registered component and dependency/host declarations, Toolkit analogue, reasoned status, benefit and a test case.

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
