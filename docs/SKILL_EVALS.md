# Skill Evals: paired trial records (experimental)

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

## Next research milestone

Implement opt-in adapters to collect real run artifacts from compatible
clients, preserve budgets and tool permissions, and define task-specific
acceptance oracles. Avoid ranking a skill from a tiny self-selected dataset.
Make release claims only after independent review and reproducible runs.
