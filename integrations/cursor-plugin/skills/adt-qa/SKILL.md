---
name: adt-qa
description: Use for FastAPI/pytest API-test strategy, Playwright/mobile/UI tests, flaky CI, failures, regression planning and QA quality gates; also when ADT is not named. Do not trigger for trivial questions.
---
# Focused QA and regression
1. Work in the ONE specified project; read test config, fixtures and directly related CI. If no project selected and several candidates exist, ask once before reading unrelated projects.
2. For substantive QA tasks call toolkit_prepare_task with concrete task and max_skills: 1 via ADT MCP. Avoid toolkit_info and enumerating catalog without diagnostics.
3. Use the returned complete test skill; fetch another selected skill or its references only when affecting concrete oracles, risks or test architecture. When truncated, fetch the missing portion before claiming fully loaded.
4. On meaningful transition (investigation -> tests -> regression assessment) or newly observed failure, use toolkit_prepare_stage, max_skills: 1 and still-current consulted_skills SHA256 map. Do not repeat unchanged skills/stages.
5. Prefer deterministic observable oracles, scoped tests and PASS/FAIL/NOT_RUN/BLOCKED evidence; reading a skill is not running pytest or a release gate.
