# Task prompt template for ChatGPT / Codex

[Русский оригинал](../TASK_PROMPT_TEMPLATE.md) | [Language policy](../LANGUAGE_POLICY.md)

**Context:** [repository and issue]. **Goal:** [observable change].

1. Inspect current code, the request, repository rules and dependencies. Do not assume that an old description reflects the current state.
2. Define acceptance criteria and scope. Use only the roles and skills that are needed.
3. Implement the smallest complete change while preserving contracts and project conventions.
4. Test the changed behavior using the project's existing tools. Add negative and regression cases proportionate to risk.
5. Self-review; report exact commands, actual results and unverified areas.
6. Commit, open a PR, merge or deploy **only when requested and permitted by actual project rules and user authority**. Never represent a plan as completed delivery.
7. End with: changes, evidence, PR/commit link if available, merge/deploy status if applicable, and remaining limitations.
