---
name: adaptive-delivery
description: Legacy v3 scope-size routing guide kept for backward compatibility. For new feature implementation prefer feature-delivery rather than activating both workflows.
---

# Adaptive delivery - legacy compatibility reference

Use `feature-delivery` instead for new implementations. Never activate both coordinators in the same task. This older workflow is retained so v3 workflows do not break.

## Small, medium, large
Use a scaled methodology inspired by the staged reasoning in Bulletproof. Avoid forcing a 12-stage process on one-line fixes.

1. Read actual repository constraints and the request; identify a testable user-visible outcome.
2. Classify scope: S (localized reversible change), M (cross-module or migration), L (architectural or production-critical). State why.
3. S: reproduce, make smallest correct change, test, inspect diff, report. No mandatory research document.
4. M: record acceptance criteria, compare reasonable approaches, map nearby consumers, implement, run focused and regression checks, review changed code.
5. L: document alternatives and impact, identify migration and rollback paths, stage evidence gates, preserve owner approval boundaries.
6. Before calling a defect confirmed, produce a reproducible example or observable failure; an assumption is not proof.
7. Stop if the project contract forbids the requested operation. Do not grant yourself merge or deployment permissions.
8. Report implemented/not implemented, actual tests, remaining risks, and whether PR/merge/production actions *actually* happened.

**Output:** classification, acceptance criteria, evidence, exact status; minimize artifacts for S tasks.
