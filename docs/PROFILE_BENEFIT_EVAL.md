# Profile usefulness: controlled baseline versus Toolkit guidance (Issue #298)

[Русская версия](ru/PROFILE_BENEFIT_EVAL.md) | [Existing evaluator](SKILL_EVALS.md) | [Real-agent zero-spend prohibition](REAL_AGENT_PILOT.md)

## Current result - 24 October 2026

**OFFLINE_PROTOCOL_READY**, **L6 benefit NOT_MEASURED**. This is a methodology and real source-file measurement, **not a successful real agent trial**. No model, paid API, Codex CLI, Claude CLI or user project was executed. Case requirements are AI-authored and **not independently human approved**.

A fixed set of five synthetic, generic tasks appears in [profile_benefit_20261024.json](../fixtures/profile_benefit_20261024.json). Source reference: `40479bee677887d9cc4821a0f2a2398b9c57a6e3`. The profile names and target oracles are frozen **before** collecting any candidate agent output. This avoids retroactive profile selection.

| Profile | Generic task | Acceptance oracle |
| --- | --- | --- |
| `general` | Default-value compatibility review | Explicit criteria for compatibility, negative tests, rollback; independent human review of actual output |
| `backend` | Python Retry-After parser defect | Reuse hidden `python-api` deterministic oracle from `agent_eval_fixtures.py` |
| `fullstack` | JS port-input/parser boundary | Reuse hidden `javascript-ui` deterministic oracle from `agent_eval_fixtures.py` |
| `qa-python` | Regression case design for a Python parser | Inspect coverage and runnable assertions; human review; do not reveal hidden grading oracle to candidate |
| `ui-orchestra` | Fictional responsive reading tracker | Independently inspect three **rendered**, different sketches, mobile/desktop and explicit visual acceptance; never assume UI is approved |

## Run the free, read-only preflight

```bash
python scripts/profile_benefit_preflight.py
python -m unittest tests.test_profile_benefit_preflight -v
```

The first command reports the actual available **source-file bytes** (total declared skill files, and SKILL.md subset) for the five profiles. The no-profile baseline has **zero Toolkit skill source bytes by definition**. This is not model context consumption, loaded instructions, performance overhead, token expense or savings. All *real* output quality, acceptance deltas, duration, token and incremental-cost fields remain `NOT_MEASURED`, and client execution remains `NOT_RUN`.

## Protocol for a future *separately permitted, verified no-charge* experiment

1. Use the **same model/build, client version, user prompt, project snapshot and tool permissions** for baseline (no Toolkit skill) and candidate (the named profile only). Keep task-specific requirements and hidden oracles outside both visible prompts. No trained or speculative agent is allowed to grade its own output.
2. Record **two paired trials per task** (5 profiles × 2 trials × 2 variants = 20 run records). Alternate execution order: trial 1 baseline → candidate; trial 2 candidate → baseline. Record errors and actual timestamps if supported, never derive duration from estimates.
3. Give an independent reviewer the resulting artifact, case acceptance criteria, regression evidence and safety trace. Judge whether the user-visible work **actually passed**. For `ui-orchestra`, check real image/HTML sketches rather than textual claims. Include `client_skill_use` per run: `OBSERVED_WITH_TRACE`, `NOT_OBSERVED` or `NOT_VERIFIED`. Presence of files alone cannot justify `OBSERVED_WITH_TRACE`.
4. Keep all trial logs and user-specific data private; never commit them into this public repository. If account billing, permissions or isolation cannot be independently confirmed as free, **DO NOT RUN** under Issue #11. No environment flag or CLI bypass is provided here.
5. For **already produced** zero-cost observations only, supply a privately stored JSON with `schema_version=1`, `dataset`, `model`, exact `repository_sha`, all 20 `runs` using the pre-existing [skill_eval.py](../scripts/skill_eval.py) evidence schema, plus `trial_protocol`: `client_version`, `tool_permissions`, `reviewer`, `independent_review_attested=true`, `incremental_cost_verified_zero=true`, `case_order` mapping each ID to `[["baseline","candidate"],["candidate","baseline"]]`. Run `python scripts/profile_benefit_preflight.py --score /absolute/path/to/private-recordings.json`.
6. Even after an operator claims independent review and zero-cost status, the evaluator can only confirm **schema, pairing, supplied evidence-file existence, and arithmetic**. It cannot authenticate the reviewer, inspect hidden oracles, validate any cost statement, verify actual skill use or eliminate bias. The result is `EXPLORATORY_RECORDED_PAIRS_NOT_CERTIFIED`, never automatically `PASS` or verified benefit.

Do not combine previous source-only/lexical 416-case routing tests, ChatGPT installed plugin guidance, owner's Codex MCP call observations or illustrative unit-test acceptance rates into this empirical score. These measure **different levels**. Observed skill instruction loading (L5) does not imply L6 task improvement.

**Disposition for #298:** implement and test the reproducible, honest no-spend protocol. Real paired agent outcomes and independent impact validation are **explicitly excluded until an authorized, genuinely free execution mechanism exists**. Later source/checksum changes on `main` do not retroactively alter the pinned case baseline.
