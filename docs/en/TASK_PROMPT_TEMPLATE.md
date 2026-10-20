# Task prompt template for ChatGPT / Codex

[Русский оригинал](../TASK_PROMPT_TEMPLATE.md) | [Language policy](../LANGUAGE_POLICY.md)

**Context:** [repository and issue]. **Goal:** [observable change].

1. First inspect the current code, issue, repository rules and dependencies. Do not trust an outdated description of current state.
2. State acceptance criteria and scope; use only the necessary roles and skills.
3. Implement the smallest complete change while preserving existing contracts and project conventions.
4. Test the changed behavior with the project's existing tools; include negative and regression cases as appropriate to risk.
5. Perform a self-review and list the actual commands, observed results and unverified areas.
6. Commit, open a PR, merge or deploy **only** when the request and actual repository rules and permissions allow it. Do not present plans as completed delivery.
7. Final report: changes, evidence, PR/commit link (if available), merge/deployment status (if applicable), and limitations.
