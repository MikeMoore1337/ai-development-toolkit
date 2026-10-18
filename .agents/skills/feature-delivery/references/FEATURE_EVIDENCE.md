# Evidence checklist (as needed)

- Requirement C* and link to source decision, changed code or configuration, test/observation, outcome.
- Baseline: before-state or reproduction, especially for bug fixes.
- Contract: inputs, outputs, errors, retries, permissions and persistence when relevant.
- Verification: exact command, exit status, date/commit when available; distinguish unit/mocks/real integration, UI inspection, deployment.
- Review: who/what actually reviewed; independence unverified if no separate review was possible.
- Regressions: touched upstream/downstream behavior and applicable check.
- Deployment: current branch, PR/CI, explicit permitted environment and observed production SHA only when independently verified.
- Stop: open items, why they block, and a concrete next action. A green local test does not establish production success.

Use one concise report where possible. Avoid document sprawl.
