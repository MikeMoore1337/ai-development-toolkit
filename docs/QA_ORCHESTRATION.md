# QA Orchestra - independent verification without a second controller

[Русская версия](ru/QA_ORCHESTRATION.md)

This is an **optional task-scoped QA process**, not a runtime, agent scheduler, second issue lifecycle or CI/merge gate. Reuse `qa-strategy`, `qa-verifier` and the existing QA Pack specialists. The target repository's AGENTS.md, Issue, permission boundaries and release/visual approval rules always win.

## When to engage

- **Single agent:** typo, one small isolated fix, a known deterministic regression. Do not spawn a review panel.
- **Two QA perspectives:** one changed boundary with independent user-facing impact, e.g. API/auth + UI behavior.
- **Up to three perspectives:** risky cross-layer changes, inconsistent signals, broad E2E migrations or release-critical evidence. Three is a maximum, not a quota.
- For product implementation, use only one controlling process (`feature-delivery` or explicitly available `make-feature`). This guide coordinates *QA evidence only* and never owns the PR or task lifecycle.

## Offline adaptive decision (Issue #279)

The optional `scripts/orchestration_decision.py INPUT.json` is a **read-only, deterministic advice tool**, not a worker orchestrator. Declare exactly: `schema_version=1`, `scope=SMALL|MEDIUM|LARGE`, `independent_readonly_streams=0..3`, `writes_required` (boolean), `parallel_capability=VERIFIED|NOT_VERIFIED|UNAVAILABLE`, `owner_parallel_approval`, `zero_incremental_cost_verified`, and `isolation_verified` (booleans).

- A small task stays `SINGLE_AGENT`. Medium/large work stays `SEQUENTIAL_REVIEW` with a single controller unless **all** parallel gates hold: at least two separate read-only streams, verified available client capability, explicit owner approval, verified no incremental cost, verified isolation, and **no writes required**.
- Even then `OPTIONAL_PARALLEL_READONLY_REVIEW` is only a suggestion: it launches zero workers. The actual client must independently check permissions and provide invocation traces. A mixed read/write task never authorizes parallel writers.
- The output includes blockers and reason codes. Execution is always `NOT_RUN`; activation `NOT_VERIFIED`; time, tokens and benefit `NOT_MEASURED`. Claimed input evidence is not independently authenticated. Reuse the existing `validate_qa_orchestration.py` for later declared QA execution reports; do not alter the historical A/B pilot ledger.
- The three previously reported A/B examples were directionally mixed (one approximately 49% faster, two approximately 6% and 4% slower), with differing tasks and no defensible universal improvement claim. These are **not** thresholds used by the selector.

Minimal synthetic input:

```json
{"schema_version":1,"scope":"SMALL","independent_readonly_streams":0,
 "writes_required":false,"parallel_capability":"NOT_VERIFIED",
 "owner_parallel_approval":false,"zero_incremental_cost_verified":false,
 "isolation_verified":false}
```

## Procedure

1. **Preflight:** capture exact owner request, Issue acceptance criteria, target repo/revision, changed files, declared risk, available clients/tools and data boundaries. Identify the smallest independent test oracles.
2. **Select specialist streams only as needed:** contracts/API/auth (`api-testing`, `contract-testing`); browser/interaction/accessibility (`playwright-testing`, `e2e-testing`); Python/DB (`pytest-test-design`, `database-validation`); CI/stability (`failure-triage`, `flaky-analysis`); security (`security-testing`, `security-review`). Do **not** load all skills or invent experts for each skill.
3. **Assign distinct read-only work:** each stream receives the same exact SHA, acceptance criteria, explicit files/surfaces, risks, test environment, expected oracles and prohibition on unauthorised mutations. Independent workers return findings; one designated implementer may later fix accepted issues on a single owned branch.
4. **Real parallelism only:** if the client exposes actual subagent creation, use at most three genuinely independent read-only workers. Record tool identifiers/actual execution. Generic agents supplied with a role brief remain **generic**, not branded specialists. Otherwise apply the same perspectives sequentially, label `SEQUENTIAL` and do not claim independent agents ran. Never start paid providers or bypass client quotas.
5. **Reconcile:** deduplicate overlapping findings, reproduce material failures, prioritize blockers, and distinguish observed proof from code-only hypotheses. Map each required acceptance criterion to a test oracle and exact evidence. `NOT_RUN`/`UNKNOWN` are never green.
6. **Return one report:** baseline SHA, work modes and traces, requirements/risk matrix, test status/environment, evidence identifiers, conflicting findings and resolution, missing coverage, `READY_FOR_REVIEW` / `BLOCKED` / `INSUFFICIENT_EVIDENCE`, next action. `READY_FOR_REVIEW` means evidence can be reviewed, **not** merge or release approval.
7. **Handoff:** agreed issues can be implemented in a separately authorized development step; rerun affected tests and the actual repository CI for its current PR HEAD. No offline report grants deployment.

## Evidence and worker contract

Per stream: `id`, scope, loaded skill/reference status, `SEQUENTIAL` or `ACTUAL_SUBAGENT`/`GENERIC_SUBAGENT`, actual trace only if an invocation happened, findings/limitations, tests with observables, environment, SHA, and exact evidence references.

Use `PASS`, `FAIL`, `NOT_RUN`, `BLOCKED`, `UNKNOWN`. Test/CI/browser PASS requires real observed output for the exact revision; file reading and synthetic examples are not execution evidence. Surface any mismatched provider/target revision as unverified. UI screenshots must be actual and sanitized. A self-review is not independent, even when assigned a different role name.

The optional `scripts/validate_qa_orchestration.py fixtures/qa_orchestra_valid.json` checks **internal consistency of declarations**, not that URLs, logs, agents or tests existed. The sample is synthetic with `NOT_RUN`. Do not require JSON for ordinary chat QA. The validator rejects false-green labels and fabricated parallel counts; it cannot authenticate worker provenance.

## Applying QA to different project types

- **Web or mobile application:** verify user flows, accessibility, frontend/API/database contracts and the existing release and visual-approval gates.
- **Agent-based service:** check incident evidence, uncertainty and model-call constraints without granting resident processes new permissions.
- **Application with private data or external actions:** test privacy boundaries, consent, retry/idempotency and reconciliation using synthetic data only.

No extra dependencies, paid API, unsolicited report files or unattended execution are required.
