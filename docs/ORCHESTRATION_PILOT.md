# Zero-spend real-client orchestration pilot — evidence contract

[Русская версия](ru/ORCHESTRATION_PILOT.md) | [Issue #141](https://github.com/MikeMoore1337/ai-development-toolkit/issues/141) | [Existing real-agent skill-eval harness](REAL_AGENT_PILOT.md)

## Purpose, not an execution claim

Evaluate whether bounded, genuinely independent **read-only QA/analysis** specialists improve results compared with one development agent, without another controller. The three synthetic review case definitions are pinned in [the registry](../fixtures/orchestration_pilot_reference.json). **All runs remain NOT_RUN.** Zero-cost source inspection, existing GitHub checks and offline fixtures do not prove actual Codex/Claude agent performance.

The existing `scripts/agent_eval_runner.py` has a hard owner zero-spend execution lock. **Do not alter it or call `--execute`**, rent a VM, use production hosts, connect a new provider or assume a subscription is free of overages. A genuinely no-charge, isolated authenticated real-agent executor and the appropriate distinct owner approval are prerequisites, not defaults. The H15 sandbox CLI discovery on 21 October 2026 found no `codex` or `claude` binaries; it did not call a model.

## Identical-input A/B method

| Case | Frozen source | Proposed read-only task and acceptance |
| --- | --- | --- |
| Example A | See pinned registry | Verify that a repeated write cannot silently duplicate a business effect |
| Example B | See pinned registry | Trace a synthetic service alert without claiming unavailable runtime evidence |
| Example C | See pinned registry | Check explicit consent and foreground-only behavior without accessing private data |

For each case, run **A**: one real agent with source-only/read-only permissions; then **B**: the *same client and model* with a coordinator plus 2–3 actually invoked independent reviewers, no overlapping source writes. Counterbalance order across cases, keep acceptance criteria and exact baseline SHA unchanged, require independent inspection of returned evidence. If the client cannot create real independent workers, label the execution `SEQUENTIAL`; do not populate the comparative result as multiagent performance.

Record real CLI tool invocation IDs/traces, test outputs, provider/client/model version, exact SHA, actual wall-clock readings, and tokens only if explicitly reported. Record `NOT_MEASURED` for absent data. Don't infer token consumption from response length or synthetic fixture scores. Reverify any effectful change in its own authorized project PR/CI; this pilot must not edit production code or any private vault.

## Offline truthfulness checks

    python scripts/validate_orchestration_pilot.py fixtures/orchestration_pilot_reference.json
    python -m unittest tests.test_orchestration_pilot -v

The offline validator checks **internal assertions**, not the authenticity of logs or owner grants: no invented observed runs, positive timestamps without execution, model mismatch, bogus parallel workers, missing evidence, or unauthorized paid API. `PENDING_INDEPENDENT_REVIEW` is the most advanced representable conclusion; there is intentionally **no automatic PASS or measured speedup status**. The supplied registry reports zero real agents.

## Release provenance (verified 2026-10-21)

Toolkit [`v5.5.0`](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.0) was published at immutable tag SHA `04d60055e93c04dda26fb3868689ab4031fbf617`. The newer published [`v5.5.2`](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.2) points to tag SHA `bf8d469f7402ed1a99e19ba6797d841751801ea5` and **does include** this source-only pilot guide, its Russian counterpart, fixture and validator. Presence was checked at that tag, not inferred from the moving `main` branch. No new release was created by this documentation correction.

**Source availability is not execution evidence.** The pinned pilot registry still declares `NOT_RUN`, `owner_runtime_approved=false`, `verified_zero_incremental_cost=false` and `verified_isolation=false`; independent workers and A/B measurements remain `NOT_RUN` / `NOT_MEASURED`. An archive, a green CI run or an installed skill cannot clear the real-agent cost/isolation gate. Publication and model execution require distinct approvals.
