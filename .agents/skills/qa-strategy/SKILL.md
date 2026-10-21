---
name: qa-strategy
description: Choose risk-based unit, integration, contract, UI and end-to-end validation. Use for changes requiring test design or verification evidence.
---


# QA strategy
1. State the behavioral claim and how it could fail while tests remain green.
2. Rank by impact, probability and detectability; prioritize critical workflows and invariants.
3. Pick the cheapest test level that reliably proves each behavior. Avoid duplicating test cases across layers without reason.
4. Cover relevant happy, error, boundary, permission, retry and persistence cases, not a mechanical checklist.
5. Check setup/teardown, isolation, timeouts, idempotency, false-green assertions and CI repeatability.
6. Distinguish mocked, local, staging and real production evidence; never claim checks not run.
**Output:** risk matrix, chosen tests, actual results, uncovered risks.

## Optional independent QA coordination
For a genuinely cross-layer or high-risk verification request, use [QA Orchestra](../../../docs/QA_ORCHESTRATION.md) to select at most three independent **read-only** QA perspectives, with sequential fallback when no real subagent tool exists. Reuse the relevant QA Pack skills, not a new controller. Always report actual run evidence and preserve the target repository's Issue, approval and release gates. For a small fix, use one agent and this skill's normal risk-based test plan.
