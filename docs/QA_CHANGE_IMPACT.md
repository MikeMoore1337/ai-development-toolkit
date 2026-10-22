# Change-aware QA regression selection (read-only)

[Русская версия](ru/QA_CHANGE_IMPACT.md)

This optional helper implements the **planning worksheet** from [Change Impact Analysis](../extensions/qa/skills/change-impact-analysis/SKILL.md), supported by [Requirements Traceability](../extensions/qa/skills/requirements-traceability/SKILL.md) and [Quality Gate Assessment](../extensions/qa/skills/quality-gate-assessment/SKILL.md). It is **not** a separate test runner, a code graph, a CI quality gate, or a substitute for the project release policy.

## Offline examples

Supply explicitly changed paths:

```bash
python scripts/qa_change_impact.py --paths frontend/views/Workout.tsx backend/api/schema.py db/migrations/101.sql
```

Or compare two **locally available exact 40-character git commit hashes** of a repository you are authorized to inspect:

```bash
python scripts/qa_change_impact.py --root /path/to/repo --repository org/repo --git-base BASE_40_SHA --git-head HEAD_40_SHA
```

On Windows, use a Windows path for `--root`. These commands do **not** fetch repositories, call models, install dependencies, execute pytest/Playwright, or modify product projects. `--output report.json` can write a new report file but never overwrite existing evidence. Never pass private file contents or customer PII as arguments.

## What the result actually means

The script matches file-path tokens to surface rules for AUTH, PRIVACY, API, DB, UI, ASYNC, CI. For example, an auth change suggests negative access, tenant isolation, and PII checks; migrations require both integrity and rollback or an explicit blocker; an API + UI diff suggests a bounded cross-layer journey. Unknown paths trigger a mandatory human impact review, **not** a green result.

Each recommendation includes `changed_paths`, `risk`, `purpose`, `status = NOT_RUN`, `evidence = PATH_HEURISTIC_ONLY` and empty execution receipts. Even with a pinned git diff, the helper cannot establish all transitive callers, changes hidden in differently named files, API contract details, available tests, acceptance criteria, or production results. For these, an engineer must inspect actual code, consumer traces, issue AC and target project's `AGENTS.md`. Additional tests may be necessary; never interpret this as permission to skip existing required CI or owner gates.

The `fixtures/qa_change_impact_cases.json` cases are **synthetic** YFC/Hermes/Second Brain-like PR examples. Passing their oracles proves deterministic lower-bound check suggestions, *not* that those applications were accessed or their tests executed.

## Persisted-state and dependent-consumer risk hints

With `--inspect-diff`, added or removed markers such as `mutation_id`, `expected_version`, `request_fingerprint`, `is_completed` and version assignments produce the **PERSISTED_STATE** signal. It adds `state-integrity` (version, persistence and no-op-write invariants), `async-replay` (idempotency, retries and conflicts), and `consumer-review` (manual search for direct callers). API hints also add `consumer-review`. A token match is **not** proof of known consumers, database migrations, test results or a call graph.

For example, a workout-set service change can affect an unchanged HTTP PATCH route, planned progression and frontend offline queue. Review such consumers **manually** and connect real tests and acceptance criteria through the separately approved test map. False positives are possible; application-level version assignments do not automatically require a migration or rollback. All recommended checks remain `NOT_RUN` until independently executed.

## Manual handoff

Map `changed path → affected consumer/contract → failure mode → named test → oracle → status → receipt`. Use the project's QA orchestration and traceability flow if several boundaries are involved. Actual test execution and resulting PASS/FAIL must be recorded separately, against an exact commit and environment; do not overwrite NOT_RUN with an assumption.


## Optional mapping to project-owned test and requirement IDs

For projects that already maintain a test/requirements inventory, provide an **explicit, separately reviewed** JSON mapping:

```bash
python scripts/qa_change_impact.py --paths frontend/views/workout.tsx backend/api/schema.py --test-map fixtures/qa_change_impact_test_map.json
```

The optional map uses schema version 1 and `entries` with an `id`, a **directory prefix** (`frontend/views/`), `check_ids` (from the existing QA check catalog), `test_ids` (symbolic references), and `requirement_ids` (project-owned IDs). A bounded exact directory-prefix match is required; no regular expressions, shell commands, executable hooks, remote fetches or automatically generated test IDs are accepted.

The additional `declared_test_candidates` contain the mapping ID, test ID, requirement IDs, matched changed paths, and explicit `NOT_RUN` / `OWNER_DECLARED_NOT_VERIFIED`. The `unmapped_check_ids` list identifies recommended checks with **no declared mapping**. Neither mapping entry existence nor syntactic validation proves a test exists, is relevant, or has passed. All critical checks from the original risk plan remain mandatory; the map can never suppress them.

The supplied `fixtures/qa_change_impact_test_map.json` is **synthetic only**: its test IDs and acceptance IDs are not claims about YFC, Hermes or Second Brain. A real project's owner must approve a local mapping and inspect actual test files, changed behavior and AC before assigning work. Never treat declared tests as execution evidence or bypass protected project release rules.


## Optional bounded inspection of changed source lines

For a *local repository with both full commit SHAs*, opt in to the bounded text-diff heuristic:

```bash
python scripts/qa_change_impact.py --root /path/to/repo --git-base BASE_40_SHA --git-head HEAD_40_SHA --inspect-diff
```

The script uses Git's built-in diff with external diffs, textconv, color and rename detection disabled, up to **256 KiB** of UTF-8 patch data. It recognizes narrow tokens in added/removed lines (API endpoints, authorization, SQL migration, UI state, background jobs, privacy and deploy controls). Only per-file counts and *surface categories* are returned - **never changed source text, matched values or credentials**. Unknown or binary files require manual investigation. Oversized or malformed patches fail closed.

The optional `diff_content` section reports `LOCAL_PATCH_TOKEN_HINTS_ONLY`. These content hints may **add** recommended checks, but cannot suppress checks inferred from paths or satisfy required CI. The resulting checks still show `NOT_RUN`, and `gate` remains `INSUFFICIENT_EVIDENCE`. Explicit test maps remain `OWNER_DECLARED_NOT_VERIFIED`. Even a recognized SQL token is not evidence that an actual database migration is required, its consumers are known or the patch is safe.

Do not use `--inspect-diff` with `--paths`: a filename list has no verified patch content. This feature is a local, read-only analysis helper - not a complete diff parser, call graph, runtime execution, security audit or deployment gate. Run it only on source you are authorized to access.
