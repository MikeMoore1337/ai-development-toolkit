# Full original ECC 2.2.3 gap catalogue (#435)

Source is pinned to affaan-m/ECC commit 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b. The read-only scripts/ecc_gap_catalog.py report generator inventories ALL tracked skills, agents, commands and rules from the original Git tree. No ECC implementation is copied. Each component has source path, content digest, description and trigger, license claim, registered component and dependency/host declarations, Toolkit analogue, reasoned status, benefit and a test case.

GitHub Actions ecc-gap-catalog.yml publishes the reproducible ecc-full-gap-matrix artifact: ecc-gap-full.csv, ecc-gap-full.json, and ecc-gap-summary.json. Headline marketing counts may differ from the pinned source: use the measured inventory. Unassessed items are explicitly HOLD_REVIEW, not silently skipped. Root MIT license assertions do not independently attest transitive dependency rights or source security.

## Original selective installation route

Upstream already ships catalog.js and install-plan.js --skills. Our CI tests the original read-only plan for windows-desktop-e2e with --target codex, in a disposable HOME. Its verdict is ADOPT_AS_IS_CANDIDATE, NOT approval to install: shared workflow-quality module paths or global AGENTS/skill collisions require separate inspection before any apply. If single-skill selectability or existing config preservation is unclear, HOLD rather than implement a new installer.

change-impact overlaps Toolkit scripts/qa_change_impact.py; tdd-workflow overlaps Toolkit QA practice. Both are HOLD_REVIEW, pending functional comparison. continuous-learning v1 is DEPRECATED upstream and is HOLD_UNSUPPORTED; separately review v2 under #436. See catalog_review.json and full CSV for rationale.

No Codex or Claude CLI, paid API, automatic client installation, resident hooks, session ingestion or production change is authorized. Official targets for other users remain optional with separate consent. Passing a source-only CI is not verified Windows Codex Desktop or Hermes runtime activation. Rollback: remove the optional CI and report generator in a reviewed PR.

To reproduce using trusted local checkouts: python scripts/ecc_gap_catalog.py --ecc-root /isolated/ECC --toolkit-root . --source-revision 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b --output-dir /tmp/ecc-gap
