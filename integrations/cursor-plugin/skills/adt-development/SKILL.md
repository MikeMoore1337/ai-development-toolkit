---
name: adt-development
description: Use for substantive software implementation, FastAPI/backend/frontend/API work, bug fixes, architecture and refactoring; applies even if the user never mentions ADT. Skip tiny fixes and general questions.
---
# Focused implementation
1. Identify requested behavior, ONE authorized workspace, project rules, relevant files and regression risks. Avoid scanning unrelated repositories or entire trees without need.
2. If ADT guidance is warranted, use read-only Personal MCP initial stage: toolkit_prepare_task with task text and max_skills: 1. The returned SKILL.md may already be complete; request another only when justified. Do not routinely call catalog/info.
3. Implement the smallest complete change using Cursor's own editing tools. When shifting to verification or a new risk, call toolkit_prepare_stage with original task, stage, max_skills: 1 and confirmed full consulted_skills digests; do not reload unchanged instructions.
4. Run focused tests first, expand regression by change impact. Report real commands/results separately from source guidance.
5. Never merge, deploy, install dependencies, spawn models or exceed spending/permission gates automatically. Explicit native external controllers take precedence.
