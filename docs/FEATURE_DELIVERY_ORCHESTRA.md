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
