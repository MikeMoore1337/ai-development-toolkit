# Full original ECC 2.2.3 gap catalogue (#435)

Source is pinned to affaan-m/ECC commit 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b. The read-only scripts/ecc_gap_catalog.py report generator inventories ALL tracked skills, agents, commands and rules from the original Git tree. No ECC implementation is copied. Each component has source path, content digest, description and trigger, license claim, registered component and dependency/host declarations, Toolkit analogue, reasoned status, benefit and a test case.

GitHub Actions ecc-gap-catalog.yml publishes the reproducible ecc-full-gap-matrix artifact: ecc-gap-full.csv, ecc-gap-full.json, and ecc-gap-summary.json. Headline marketing counts may differ from the pinned source: use the measured inventory. Unassessed items are explicitly HOLD_REVIEW, not silently skipped. Root MIT license assertions do not independently attest transitive dependency rights or source security.

## Original selective installation route

Upstream already ships catalog.js and install-plan.js --skills. Our CI tests the original read-only plan for windows-desktop-e2e with --target codex, in a disposable HOME. Its verdict is ADOPT_AS_IS_CANDIDATE, NOT approval to install: shared workflow-quality module paths or global AGENTS/skill collisions require separate inspection before any apply. If single-skill selectability or existing config preservation is unclear, HOLD rather than implement a new installer.

Two original skills have now completed functional comparison against existing native Toolkit mechanisms (reviewed batch #435, 28 October 2026):

- **`skills/change-impact` - ALREADY_PRESENT after native uplift**: `extensions/qa/skills/change-impact-analysis/SKILL.md` plus `scripts/qa_change_impact.py` already cover code, caller, contract, data and regression risk surfaces. The existing native skill now includes explicit *planned impact vs actual diff* reconciliation, scope drift and `NOT_VERIFIED` handling. No second impact controller or force-created document tree.
- **`skills/tdd-workflow` - ALREADY_PRESENT after native uplift**: `.agents/skills/feature-delivery/SKILL.md` now supports an opt-in RED / minimal GREEN / refactor evidence cycle within the existing feature controller. We deliberately reject upstream's universal 80% coverage mandate, all-layer testing, automatic checkpoint commits and package-manager detector as global requirements.
- **`skills/continuous-learning` v1 - HOLD_UNSUPPORTED**: ECC marks it deprecated. Its v2 successor remains separately under #436.

These two classifications are *functional workflow coverage*, not byte-identical ports, observed model improvements, or a claim that all ECC components have been reviewed. Original source: `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, paths `skills/change-impact/SKILL.md` and `skills/tdd-workflow/SKILL.md`. The unchanged baseline gap-matrix artifact will continue to show its earlier HOLD statuses until its workflow is rerun using this reviewed catalog. See `catalog_review.json` for tested scenarios and evidence limits.

No Codex or Claude CLI, paid API, automatic client installation, resident hooks, session ingestion or production change is authorized. Official targets for other users remain optional with separate consent. Passing a source-only CI is not verified Windows Codex Desktop or Hermes runtime activation. Rollback: remove the optional CI and report generator in a reviewed PR.

To reproduce using trusted local checkouts: python scripts/ecc_gap_catalog.py --ecc-root /isolated/ECC --toolkit-root . --source-revision 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b --output-dir /tmp/ecc-gap

Manual comparison of original ECC api-design, database-migrations and e2e-testing with the actual Toolkit skills confirms their core functions are ALREADY_PRESENT, with exact analogue paths in the matrix. The upstream --skills windows-desktop-e2e plan expands to FOUR modules (platform-configs, skill-unified-memory, workflow-quality, shared-script-utils); applying this as a single skill therefore remains HOLD_SHARED_MODULES regardless of its initial functional candidacy.
