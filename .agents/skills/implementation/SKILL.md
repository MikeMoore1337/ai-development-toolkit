---
name: implementation
description: Implement a bounded source-code change while preserving project conventions and verifying changed behavior. Use for actual software implementation tasks.
---


# Implementation
1. Discover language/runtime, current base branch, existing architecture, build commands, lint/test setup and applicable `AGENTS.md`.
2. Inspect the affected functions and public contracts before editing. Prefer small compatible edits over new infrastructure.
3. Make the minimal complete change, update directly affected documentation, and add regression checks proportionate to risk.
4. Run focused checks first and the repository-defined final checks that apply. Record the exact commands and results.
5. Review the diff for data loss, errors, permissions, logs, generated files, and unrelated changes.
6. Do not assume `main`, `master`, Python, GitHub, hosted CI, or a deployment service. Discover them.
7. Treat commit, push, PR, merge and production deployment as separate operations governed by explicit instructions and granted authority.
**Output:** changed files, behavior, evidence, limitations, delivery state.
