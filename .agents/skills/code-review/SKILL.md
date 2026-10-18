---
name: code-review
description: Review a proposed code diff for correctness, regressions, compatibility, security and maintainability. Use for independent change review.
---


# Code review
1. Understand the intended behavior and compare it with the actual diff and surrounding code.
2. Focus on actionable defects: broken contract, data loss, permission bypass, race, unhandled failure, flaky test or regression.
3. For each finding cite file, location, trigger, impact and a specific remediation or verification step.
4. Mark unsupported suspicions as questions, not proven bugs.
5. Check tests for false positives; do not equate passing checks with correct behavior.
6. Do not edit production code in read-only review unless explicitly assigned implementation rights.
**Output:** findings by severity, evidence, checks performed, remaining uncertainty.
