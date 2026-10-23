# Real-agent paired Skill Evals pilot (Issue #11)

[Русское руководство оператора](ru/REAL_AGENT_PILOT.md)

**Owner ZERO-SPEND hold (2026-10-18): actual agent execution is source-locked.** The owner does not authorize *any* incremental charges for model/provider API use, VM hosting or test infrastructure. `scripts/agent_eval_runner.py` now rejects `--execute` and direct Python `execute()` before touching the output directory, even with `--acknowledge-costs` and `--acknowledge-isolation`. No CLI/env flag, fake budget, or approved gate overrides this. Preflight, hidden-oracle unit tests and synthetic offline checks remain available. The real-run commands below are *historical examples*, intentionally blocked until a separate reviewed code change and explicit owner approval of a verified no-charge method.

**Status: execution harness implemented; actual agent trials and independent verdicts NOT YET performed.**
Do not cite synthetic fixture tests or successful CI as evidence that skills improve models.

## Scope and case registry

The pilot creates three independent, disposable local Git repositories from
`scripts/agent_eval_fixtures.py`: Python Retry-After parser, JavaScript port
validator and Go timeout parser. Each case has an intentionally faulty initial
implementation and a hidden deterministic regression oracle. Real task
acceptance is evaluated against these oracles **after the agent exits**.
Every independent workspace receives the same pinned local Git commit for its
case; the script also records a SHA256 snapshot of visible fixture files.
All inputs are newly written synthetic examples, not customer/company data.

Selected candidate: `minimal-safe-change`. In the candidate condition its
unchanged `SKILL.md` is made available under `.agents/skills` (Codex) or
`.claude/skills` (Claude). In baseline it is absent. Neither condition is
prompted to use a specific skill; both receive the same neutral task instruction.
Presence **does not demonstrate activation**. Review raw traces for actual
reading/invocation and record `skill_activation_observed` explicitly.

## Preflight (no network, no writes, no agent calls)

```powershell
cd D:\Pet-projects\ai-development-toolkit
py -3 scripts/agent_eval_runner.py --provider codex
py -3 scripts/agent_eval_runner.py --provider claude
```

Real runs require an installed/authenticated CLI, suitable model access, a
disposable externally isolated VM/container, and a known spending limit.
A connected remote device is not an agent runtime or evidence.
Do not run the pilot on production folders, with live credentials inside
the scratch workspaces, or without understanding CLI/provider billing.

## Optional real runs (only in your isolated test VM)

```powershell
# Replace MODEL_ID with an exact available model, and pick a fresh output folder.
py -3 scripts/agent_eval_runner.py --provider codex --model MODEL_ID `
  --trials 2 --max-seconds 300 --output D:\eval-evidence\codex-pilot-001 `
  --execute --acknowledge-costs --acknowledge-isolation

py -3 scripts/agent_eval_runner.py --provider claude --model MODEL_ID `
  --trials 2 --max-seconds 300 --output D:\eval-evidence\claude-pilot-001 `
  --execute --acknowledge-costs --acknowledge-isolation
```

The Codex adapter uses `codex exec --sandbox workspace-write --ephemeral --json`.
The Claude adapter uses `claude -p --permission-mode dontAsk --tools Read,Edit,Write`
and therefore does not grant command execution, but **is not a full OS sandbox**.
The program requires explicit confirmation of EXTERNAL isolation for both.
No dangerous skip-permission flags or shell string concatenation are used.
Agent runtimes may still access credentials/configuration outside scratch
unless the operating system or container enforces isolation. Timeouts stop
the direct CLI process; they do not constitute a process-tree sandbox.
Do not run this with access to sensitive local data. Agent CLI versions vary;
validate supported flags in your installed version before spending money.

The tool alternates run order between trials, captures stdout/stderr, source
diff, per-run start UTC, observed duration, CLI return code, SHA256 evidence digests, hidden oracle
result, a local Git SHA and source snapshot digest. It does not infer token
usage, safety counters, actual skill activation, acceptance or quality.
Output is private local evidence: **do not commit it to this public repo**.
Inspect logs before sharing; agent output can contain user/environment data.

## Independent human review (mandatory before scoring)

`observations.json` is **not** a scored report. The reviewer must inspect
every pair and complete a distinct JSON file, for example:

```json
{
  "reviewer": "Independent reviewer identifier",
  "independent_review_attested": true,
  "decisions": [
    {
      "case_id": "python-api",
      "trial": 1,
      "variant": "baseline",
      "accepted": false,
      "regressions": 0,
      "unsafe_actions": 0,
      "skill_activation_observed": false,
      "notes": "Explain observed behavior, trace findings and oracle result."
    }
  ]
}
```

This is a fragment: the file must contain one reviewed decision for EVERY
observed run. Review safety violations and regressions manually instead of
filling zero by default. With both providers, keep model and client version
recorded separately. Reviewer identities/attestations are self-reported;
the scoring software cannot independently establish objectivity.

```powershell
py -3 scripts/agent_eval_review.py `
  --observations D:\eval-evidence\codex-pilot-001\observations.json `
  --reviews D:\eval-evidence\codex-reviews.json `
  --output D:\eval-evidence\codex-reviewed-001
```

The review gate refuses incomplete pairs, nonexistent evidence, a passing
human verdict for failing/timed-out hidden oracles, invalid safety counters,
and claimed baseline skill activation. It then generates per-case scorer
input and exploratory summaries compatible with `scripts/skill_eval.py`.
Keep separate scores per repository and model. **Do not aggregate unrelated
models as though they were one controlled population.**

## Acceptance plan for #11

- [x] Three reproducible small Git repositories and sealed oracle tests.
- [x] Explicit Codex/Claude adapters, matched task prompts and counterbalanced order.
- [x] Agent output, source diff, duration, environment/version and test evidence.
- [x] Independent-review gate with fail-closed acceptance and safety measurements.
- [ ] Confirm available authenticated CLIs on an isolated runner.
- [ ] Collect 2+ real attempts per condition per case and provider.
- [ ] Review real traces, agent activation evidence, safety and regressions.
- [ ] Compare against baseline; report real limitations and variability.

These are **pilot** results, not statistical proof, even after trials run.
Source references: [Codex CLI reference](https://learn.chatgpt.com/docs/cli/reference),
[Claude CLI flags](https://docs.anthropic.com/en/docs/claude-code/cli-usage).

## Zero-cost end-to-end hidden-oracle smoke (no model calls)

Run the explicitly **synthetic, reference-only** benchmark gate:

```bash
python scripts/agent_eval_offline_smoke.py --strict-runtimes
python -m unittest tests.test_agent_eval_offline_smoke -v
```

This materializes two clean repositories per case: the intentionally buggy
baseline and a fixed, **human-authored deterministic reference implementation**.
Both get the same pinned initial Git SHA. The hidden acceptance oracle is
injected only after the reference or baseline workspace has been prepared.
The required result for each of Python, JavaScript and Go is:

- Baseline oracle **FAIL** — the known defect is detectable;
- Human reference oracle **PASS** — the expected correction is recognised;
- Same pinned initial Git SHA for both variants;
- No Codex, Claude or any other AI client is invoked, and no provider keys,
  network calls or billing APIs are used. Go module fetch is forced OFF.

The tool uses throwaway temporary directories, does not touch production hosts
or real project folders, and emits only case IDs, fixture hashes and
non-sensitive test outcomes. Its JSON always says
`classification=SYNTHETIC_OFFLINE_HARNESS_SMOKE_NOT_MODEL_EVAL`,
`real_agent_trials=0`, `real_agent_outcomes=NOT_MEASURED`, and
`independent_review=NOT_PERFORMED`. Do not score its results as though a
model used a skill; human reference edits are **not** agent attempts.

Missing local Node or Go results in a rejected/explicitly incomplete check,
not a false PASS. GitHub-hosted Ubuntu/Python 3.12 CI requires all three.
The owner zero-spend runtime lock remains unchanged; `--execute` is still
blocked and a separate explicit owner decision is required for any future
real-agent experiment.


## Optional external compatibility checks

When integration contracts are pinned to another repository, verify that checkout against a fixed revision with a source-only checker. This validates only declared interfaces and explicit owner-denial gates; it neither runs the external service nor proves agent behavior. Treat repository-specific CI jobs as implementation details rather than installation instructions for Toolkit users.

The offline hidden-oracle runner now starts Python/Node/Go oracles with a
minimal environment rather than forwarding credentials, NODE_OPTIONS,
GOFLAGS, Python hooks, or other arbitrary caller variables. This is defense
in depth, **not a network sandbox**. Real-agent execution remains source-
locked and real skill-effectiveness outcomes remain NOT_MEASURED.
