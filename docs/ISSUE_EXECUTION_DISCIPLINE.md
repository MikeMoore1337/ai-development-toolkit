# Optional Issue slicing and session retrospective

[Русская версия](ru/ISSUE_EXECUTION_DISCIPLINE.md) | [Issue Orchestrator](ISSUE_ORCHESTRATOR.md)

Selected, independently rewritten engineering methods from [mattpocock/skills](https://github.com/mattpocock/skills/tree/5863806dd4e15c63174bee4e7515a4256792ecfa), especially `to-tickets` and `retro` (MIT, © 2026 Matt Pocock). No upstream skill, setup hook, agent, CLI or controller is installed or copied. The existing Toolkit `feature-delivery` remains the sole chosen delivery controller.

## When to apply

Use **only** when the user asks to break a substantial objective into Issues or to diagnose an inefficient completed session. Do not multiply a single clear task into ceremony. Inspect the current parent Issue, prior decisions, repository `AGENTS.md`, existing tracker entries, actual code and accepted non-goals first. Do not re-ask settled questions or invent scope. Create/modify tracker items only within explicit permission.

## Draft vertical, verifiable Issues

Each Issue should have a complete, independently demonstrable outcome (a **vertical slice**, possibly touching persistence, API, UI and tests), not a generic “write the database layer” piece. Specify:

- **Outcome** and boundaries: a concrete user-facing behavior or independently testable capability, exact in/out of scope, and non-goals.
- **Acceptance**: observable pass/fail criteria tied to tests, evidence and the target branch; preserve the parent Issue contract.
- **Prerequisites**: minimal, actual blocking Issues using `Blocked by: #N` on its own line (or native GitHub relationships). Avoid self-dependency, cycles, unknown predecessors and redundant edges. Do not create extra work just to populate a graph.
- **Risk and rollback**: affected interfaces/data, reversibility and explicit owner approval, where applicable.
- **Size**: work fitting a single bounded implementation context. If it does not fit, narrow scope without losing an observable outcome.

Prefer a single Issue for a small fix. Use a separate **expand -> migrate batches -> contract** chain for genuinely broad mechanical refactoring when no vertical slice can keep CI green; treat that as an exception, not an excuse for a wider redesign.

### Fictional example

**Bad:** `#20 Build all API code`, `#21 Build all UI code`, `#22 Implement all tests` - none delivers usable behavior alone.

**Better:** `#20 User can create a note and read it back (API, persistence, basic UI, tests)`. `#21 User can edit their own note and cannot edit another owner's note (authorization, UI, negative tests)`, with `Blocked by: #20` only if it really depends on persistence created in #20.

A user-approved series may contain parallel-ready independent tickets, but the **current Toolkit Issue Orchestrator remains WIP=1** and executes one eligible Issue at a time. The existing `scripts/issue_orchestrator.py` `dependencies`, `is_cyclic` and read-only `plan` already recognize and reject dependency problems. This guidance **does not** authorize agent spawning, branch operations, automatic state changes, background work or bypassing approval/release gates. One chat should address one implementation Issue unless the owner changes the scope.

## Optional post-session retrospective

Use a compact, evidence-first record **only on request** or for a directly observed agent performance defect. Never add hooks, passive logging, surveillance of other sessions or unnecessary model calls.

| Field | Requirement |
|---|---|
| Source | Exact session/client/version and task, **if actually known** |
| Observation | Evidence-backed retries, duplicate file reads, redundant plans, unneeded handoffs, actual error codes; do not count legitimate CI polling as waste |
| Measurement | Real observed timestamps/call counts/token counters, or `NOT_MEASURED` - never an estimate disguised as a metric |
| Cause | Separate `CONFIRMED` from `HYPOTHESIS`, with falsifiable explanation |
| Minimum correction | One bounded change to skill, prompt, routing or test, not a new controller |
| Regression/rollback | What must remain green, how to verify impact, what to revert if worse |

Example: “Two identical reads of `path/X.py` were observed in the same run (tool log, redacted). Why: `HYPOTHESIS` - repeated navigation. Proposed change: reuse the existing source map. Token savings: `NOT_MEASURED`. Verify on same task and source SHA; do not infer value from one synthetic case.”

Keep sensitive source code, raw prompts, complete transcripts, credentials, personal paths and project data **out of Toolkit**. Write only into the owner-authorized target repository, private location or chat. For paired effectiveness evidence, reuse `python scripts/skill_eval.py` and its existing source/evidence gate; no performance improvement is established here (`NOT_MEASURED`).

## Regression and rollback

`tests/test_issue_execution_discipline.py` checks that existing dependency parsing/cycle detection still works, that the optional source guidance is discoverable, and that neither document claims automatic execution. These are **source-only checks**: actual quality and time/token savings require independently observed client runs. To roll back, revert this PR; no external assets or user configuration were changed.
