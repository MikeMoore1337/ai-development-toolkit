---
name: feature-delivery
description: "Use for implementing a new feature or significant behavior change. Pick quick, normal or deep workflow based on risk, track acceptance criteria and prove completion without unnecessary ceremonies."
---

# Feature delivery

Use the smallest workflow that can provide verifiable value. Read project `AGENTS.md`, current code, tests, and accepted product decisions first. Do not replace an existing project process.

## Route by risk (not code size alone)

| Route | Apply when | Minimum evidence |
|---|---|---|
| `quick` | Existing pattern, clear acceptance, one limited and reversible change | Observable before/after, focused check, regression risk noted |
| `normal` | New behavior or multiple connected components, interfaces understood | Acceptance criteria, choice, contract, implementation, testing and review |
| `deep` | Rights, payments, data loss/migration, irreversible action, unresolved key integration or disputed requirement | Test key assumption before build, alternatives, independent review if available, integration evidence |

Never escalate merely to satisfy a process. Never downgrade when the risk remains unresolved. A quick bug fix with material data-loss risk is `deep`.

## Delivery contract

1. **Understand:** Write C1..Cn acceptance criteria, scope, current behavior and a reproducible baseline where possible. For a bug, establish root cause instead of asserting it.
2. **Choose:** Inspect reuse and existing architecture. Record one decision D1 and why it beats meaningful alternatives. If uncertain, validate the critical assumption first.
3. **Implement:** Make a minimal diff, keep compatibility, provide error and retry behavior where applicable. Protect unrelated files and other agents' work.
4. **Verify:** Map every C* to an observed check or explicitly unverified condition. Run focused tests and relevant regressions. Distinguish mock, local, staging and production evidence. For UI, visually inspect real renders when tools permit.
5. **Handoff:** Report changed files, checks/results, remaining risks, and exact continuation. Do not declare merge or production deploy performed without evidence.

For `normal`/`deep`, use a separate implementer/reviewer **only if** the environment actually supports independent contexts. Never pretend a second agent exists. Acceptance independence after a change means re-checking touched evidence.

## Evidence-driven diagnosis and completion

Before changing a suspected defect, establish the observed failure, minimal reproduction (or explain why it is unsafe/unavailable), relevant recent changes, and the earliest failing boundary. Separate a confirmed cause from a hypothesis. For complex paths (for example UI -> API -> persistence), trace input/output at the boundaries while redacting secrets; avoid repeated speculative fixes.

Before saying a requirement is done, link each acceptance criterion to **fresh** evidence from the exact current revision: command or observation, execution environment, outcome and remaining limits. A prior run, a synthetic fixture, another agent's claim, a screenshot alone, or green CI on a different commit is not completion evidence. If the tool or target environment is unavailable, say `NOT_VERIFIED` and preserve the blocker rather than inferring success.

For work needing isolation, first detect whether the host already owns a worktree or sandbox. Use the host-native workflow when available; do not create an extra worktree behind its back. Repository-controlled leases, protected branches, permission gates, and the project's existing finish/cleanup procedure prevail. See `docs/en/SUPERPOWERS_EVIDENCE.md` for the read-only decision tree.

## Durable state

Prefer existing issue/PR/tracker. For complex or interruptible tasks, store a small index with owner, request, C*, chosen D*, artifact paths, current step, test commands and unresolved blockers. Do not create parallel source-of-truth documents. Do not reset counters after resume.

## Stop conditions

If a required permission, source, dependency, baseline or irreversible decision is missing, do not invent it. Complete independent available work and leave the dependent step clearly pending. Required acceptance criteria cannot be silently removed to claim success.

Read [the feature evidence checklist](references/FEATURE_EVIDENCE.md) when accepting a feature; use only the applicable sections.

## Optional orchestration
For genuinely independent cross-layer work, use the adaptive feature orchestra guide (`docs/FEATURE_DELIVERY_ORCHESTRA.md`) **only if the task warrants delegation**. It keeps this `feature-delivery` controller, one writer, scoped read-only specialists, and current exact-head checks. Small fixes stay single-agent; without real subagents report sequential execution, never invented reviewers. Do not add another workflow state machine or release permission.
