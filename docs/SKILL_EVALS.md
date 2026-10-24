# Skill Evals: paired trial records (experimental)

[Русская версия](ru/SKILL_EVALS.md)

This is a **scorer**, not an agent runner or a benchmark certification. It never
accesses remote accounts, executes target projects, infers missing telemetry, or
decides whether an evidence artifact proves a claimed outcome.

## Collect data

Choose a pinned repository SHA, task definitions and acceptance criteria.
On the same model version and tool permissions, run every task both without
the skill (`baseline`) and with the candidate skill (`candidate`). Change
run order across repetitions where possible to avoid systematic bias.
Independent reviewers should inspect the actual artifacts and enter the
observed outcomes.

Data shape (`schema_version=1`):

```json
{
  "schema_version": 1,
  "dataset": "pilot-2026-10",
  "model": "provider/model-version",
  "repository_sha": "full-pinned-commit",
  "runs": [
    {
      "task_id": "api-error-case",
      "trial": 1,
      "variant": "baseline",
      "accepted": false,
      "regressions": 0,
      "unsafe_actions": 0,
      "tokens": null,
      "duration_seconds": null,
      "evidence": ["evidence/api-error-case-baseline-1.txt"]
    },
    {
      "task_id": "api-error-case",
      "trial": 1,
      "variant": "candidate",
      "accepted": true,
      "regressions": 0,
      "unsafe_actions": 0,
      "tokens": null,
      "duration_seconds": null,
      "evidence": ["evidence/api-error-case-candidate-1.txt"]
    }
  ]
}
```

Evidence paths must be relative to the JSON file, exist, and be nonempty.
All `task_id/trial` combinations must have one baseline and one candidate.
Acceptance must be a boolean; safety and regression counters must be known
non-negative integers. Tokens and duration may be null, but must never be
fabricated. Dataset/model/repository pins are shared by the paired records.

## Score

```bash
python scripts/skill_eval.py /path/to/recorded-runs.json
python -m unittest tests.test_skill_eval -v
```

The output is machine-readable JSON with acceptance rates, the paired difference
in percentage points, regression/unsafe-action totals, optional mean cost and
duration, and `classification: exploratory`. The tool does **not** calculate
statistical confidence or verify the content of evidence files. Treat even
large deltas as hypotheses until multiple independent comparable trials are
reviewed. Do not advertise the synthetic unit-test scores as real benchmarks.

## Controlled real-agent pilot harness (Issue #11)

A strictly opt-in Codex/Claude CLI trial runner, three synthetic
Python/JavaScript/Go demonstrators with hidden oracle tests, and a separate
human-review gate are now described in [REAL_AGENT_PILOT.md](REAL_AGENT_PILOT.md).

**Issue #11 is CLOSED / NOT_PLANNED under the owner's ZERO-SPEND rule.** The existing runner blocks real agent execution, including with cost/isolation acknowledgement flags. The source harness and offline tests do **not** establish that model runs happened. Running real clients would require independently verified zero-cost conditions and separate authorization; do not infer skill activation from installation or authentication. See [the real-agent pilot policy](REAL_AGENT_PILOT.md).

Issue #141 completed a **narrower zero-cost exploratory orchestration pilot**, not L4-L6 coverage or independently measured effectiveness.

## Free lexical routing regressions

[Offline skill routing regression checks](SKILL_ROUTING_EVALS.md) began from a **historical 65-skill fixture**; the present [manifest](../MANIFEST.json) declares **82 skills**. A fixture's historical count must not be presented as the size of the current catalog. These are deterministic **source-only, lexical** checks of curated positive and negative prompts, not independent semantic accuracy, live client discovery, activation or demonstrated task benefit. Actual Codex/Claude CLI comparisons remain prohibited by the ZERO-SPEND gate in [Issue #11](https://github.com/MikeMoore1337/ai-development-toolkit/issues/11); [Issue #141](https://github.com/MikeMoore1337/ai-development-toolkit/issues/141) was completed only within its limited exploratory pilot scope.

## Practical profile usefulness protocol (Issue #298)

[Profile usefulness: five comparable synthetic tasks](PROFILE_BENEFIT_EVAL.md) covers `general`, `backend`, `fullstack`, `qa-python`, and `ui-orchestra`. The zero-cost command `python scripts/profile_benefit_preflight.py` verifies manifest membership, explicit acceptance oracles and actual **source-file byte counts** for every profile; all real baseline/candidate task results and time remain `NOT_MEASURED`. Its optional `--score` mode consumes **previously recorded** 20-run, counterbalanced paired evidence through this existing scorer. It does not run clients, authenticate a self-attested independent reviewer or override Issue #11 ZERO-SPEND. These fixtures must not be advertised as L6 evidence without independent, truly free real-task execution.
