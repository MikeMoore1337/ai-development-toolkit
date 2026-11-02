# Adaptive Feature Delivery Orchestra

[Русская версия](ru/FEATURE_DELIVERY_ORCHESTRA.md) | [End-to-end authority and traceability](END_TO_END_WORKFLOW.md)

Use **one existing feature controller**: portable `feature-delivery` by default, or `make-feature` only when the project explicitly chose it. This orchestra is a **bounded delegation/handoff pattern**, not an installed agent runtime, background worker, task scheduler, competing issue tracker or release controller.

## Routing without needless parallelism

| Task | Route | Actual workers |
| --- | --- | --- |
| Small known fix with reversible change | `quick` | One implementer; targeted test; no panel |
| Multiple connected components, understood contracts | `normal` | One implementer, optional independent research or QA |
| Unknown/high-risk data, rights, payments, authorization or destructive effects | `deep` | Validate assumptions; specialized review and explicit gates before effects |

Never select `quick` merely because the diff is small. Select only needed expertise and up to three independent workstreams **when they can genuinely work independently**. One named skill is not a spawned agent. On clients without subagents, apply the same role briefs serially and report `SEQUENTIAL`. Codex/Claude Code/cloud clients may differ in actual execution capabilities: check the current client, never invent tool calls, names or concurrency.

## Operational steps

1. **Contract:** read target `AGENTS.md`, current Issue/PR, original R/AC, project scope, dependency graph, exact baseline SHA, allowed tools/budget and approval gates. Use [end-to-end evidence contract](END_TO_END_WORKFLOW.md); never create a second source of truth.
2. **Plan:** choose `quick`/`normal`/`deep`, one controlling workflow and up to three useful roles. Name read-only outputs, acceptance tests, dependencies, path ownership and stops before delegating.
3. **Independent preparation:** read-only analysis, contract/a11y/security critique and QA may be assigned to distinct workers with actual tool invocation and returned trace. Otherwise apply the same skills sequentially without pretending independence.
4. **Single writer:** assign **one** implementer to the scoped branch/worktree. Do not allow reviewers or researchers to mutate code. Concurrent writers or edits to shared migrations/schema, API contracts or common fixtures require serial ownership and integration. Never let a worker update another branch.
5. **Convergence:** reconcile conflicting suggestions by approved requirements and observed behavior; preserve every AC, explicit decision, negative path and rejected hypothesis. Only the authorized implementer changes code, then source tests and actual target CI re-run for the changed exact HEAD.
6. **Independent verification where available:** use existing `qa-strategy` and the QA Pack. When `docs/QA_ORCHESTRATION.md` exists in the target revision, it may supply a **QA evidence perspective**, not another workflow controller. A second role name in the same context is self-review, never independent review. `NOT_RUN` is not `PASS`.
7. **Report and stop:** give one handoff listing exact changed paths/commit/AC, test command, environment, observed evidence, worker trace or sequential mode, unresolved risk, reviewer findings, approval gates, and single next action. `READY_FOR_REVIEW` is **not** merge, release or deploy. Human visual, legal, security, destructive and paid-service gates remain with the target repository.

## Verification and safety

Optional offline assertion linter: `python scripts/validate_feature_orchestra.py fixtures/feature_orchestra_valid.json`. The fixture is **synthetic**, with `NOT_RUN` checks and `PLAN_ONLY` outcome. The linter rejects fake independent workers, lost acceptance links, duplicate controllers, unsafe write scopes, dependency cycles and false-ready/false-PASS declarations. It validates **only internal consistency**: it cannot authenticate a CI URL, worker trace, owner decision or actual runtime. No new paid API, external installer, daemon, repo-local task database or mandatory report file.

For each target repository, keep its existing branch policy, QA roles, visual approval and release gates. A development role never grants permissions to resident services. Do not bypass explicit authorization, privacy boundaries, or background-job restrictions. Respect the target project's documented delivery rules.

## Native parallel worktree preflight (#440; opt-in, read-only)

The existing feature-delivery controller can **review a candidate plan of 2-12 independent tasks** without starting workers, creating branches or worktrees, modifying permissions, merging or cleaning up. This is a planning/checking extension of the original controller, **not** a scheduler, new execution service or a change to the legacy `feature_orchestra_valid.json` report schema.

Create a JSON plan **outside the repository checkout** with exactly these fields: `schema_version: 1`, `revision` (40-character lowercase Git HEAD SHA), `controller: "feature-delivery"`, `active_controllers: ["feature-delivery"]`, `runtime_state: "CLIENT_RUNTIME_NOT_VERIFIED"`, and `tasks` (2-12). Each task requires a unique `id`, matching `base_sha`, portable `branch`, portable `worktree` (relative to the **parent** of an optional explicitly supplied Git root), `writer`, nonempty `write_paths`, `shared_contracts`, `depends_on` and nonempty `acceptance`. Directory scopes use a trailing slash; wildcards are deliberately unsupported. A contract shared across tasks must be ordered with dependencies; this does **not** replace human API/schema compatibility review.

```bash
python scripts/validate_feature_orchestra.py --parallel-plan /external/plan.json
# Optional, only for an explicitly authorized local Git root:
python scripts/validate_feature_orchestra.py --parallel-plan /external/plan.json --git-root /path/to/repository
```

The first command checks declarations, path boundaries, Windows case/Unicode aliases, duplicate workspaces/branches/writers, shared files, cross-task interface risks and dependency cycles. The optional second command performs only `git rev-parse`, `git status --porcelain`, `git show-ref --heads` and `git worktree list --porcelain` against the explicit root, using `GIT_OPTIONAL_LOCKS=0`; it rejects stale HEAD, dirty/untracked files, existing checkout/branch/path collisions and symlink/junction paths. Git diagnostics are a **point-in-time preview**, not an authorization to mutate a worktree. Recheck state and exclusive writer ownership immediately before any client-native action. A plan with different source files can still contain an undisclosed semantic API/migration conflict; declare `shared_contracts` and keep integration sequencing under the existing controller.

If checks pass, output is `STATIC_PLAN_VALIDATED` and `CLIENT_RUNTIME_NOT_VERIFIED`; actual agent execution, concurrency, host leases, human permissions, conflict-free merge and model identity remain **NOT_VERIFIED/NOT_RUN**. One writer per isolated worktree is a proposed assignment, not an acquired lease. Research/review workers remain read-only. Use a **sequential** workflow for shared contracts, overlapping write scopes, migrations or uncertain ownership, and follow the actual client's native isolation and permission gates.

**Safe finish / rollback:** preserve results and current Git state, request human review of dirty worktrees, rerun source tests/CI on exact HEAD, and follow existing PR/merge policy. Do not force-remove worktrees, delete foreign branches, reset/clean user data or invent an automated teardown. A source rollback is a normal reviewed revert PR. No background sessions or model calls occur here.

**Pinned ECC comparison:** `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, `scripts/orchestrate-worktrees.js` and `scripts/lib/tmux-worktree-orchestrator.js`:
- CLI planning -> Toolkit offline static-plan check (**adapted**, no external ECC runtime).
- Branch/worktree isolation -> optional read-only Git state and collision detection (**not** automatic worktree creation).
- tmux panes, session adapters, `spawnSync`, dmux -> **not ported**; only the authorized client's native agent capabilities may execute.
- Forced worktree/branch deletion, recursive cleanup -> **rejected**; unapproved destruction is never a safe finish.
- Real simultaneous agent performance, session recovery and Win GUI integration -> **HOST_EXECUTION_NOT_VERIFIED / NATIVE_SUBAGENTS_NOT_VERIFIED / NOT_MEASURED** until separate physical client evidence.

**Existing Toolkit MCP integration:** The same optional checker is exposed as the read-only tool `toolkit_preflight_parallel_plan`. Pass `{"plan": {...}}`, optionally `{"plan": {...}, "project": "/absolute/existing/git/root"}` for Git metadata. The response distinguishes `STATIC_PLAN_VALIDATED` from `REJECTED`, lists error codes and explicitly reports `authorization: NOT_GRANTED`, `model_execution: NOT_RUN`. The MCP service does not execute Git mutations, spawn a client, create a worktree or approve merges. Using this interface requires that the host has loaded a Toolkit MCP version containing the tool; merely updating GitHub `main` does not update an installed ChatGPT plugin.

**Additional safety:** Proposed Git branches reject Git-invalid hidden or `.lock` path components and hierarchical ref namespace collisions, including collisions with existing refs. Optional Git-root reads ignore inherited `GIT_*` process overrides and refuse symbolic-link/junction `.git` metadata, so an external trace variable cannot create a log during the preflight.
