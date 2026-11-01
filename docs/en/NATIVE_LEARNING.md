# Native manual learning preview (#436)

Toolkit implements a **read-only, project-scoped candidate preview** on top of the existing opt-in Task Observer review handoff. It does not install or execute ECC, depend on Claude/Codex CLI, call a model, start hooks, watch a session, capture private prompts or automatically promote practices. Source comparison: ECC `skills/continuous-learning-v2/SKILL.md` at `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b` (MIT root license claim). The original project observer/Haiku daemon and instinct installation are **not** imported.

## Authorized offline preview

Prepare a **manually sanitized** JSON file with exactly `schema_version=2` and `observations`. Each row contains exactly `observation_id`, `skill_id`, `category` (one of the existing Task Observer categories), `source_url` (public canonical GitHub issue, PR, run, or commit), `signal` (`support` or `contradict`) and `observed_on` (`YYYY-MM-DD`). Do not include session text, prompts, personal files, secrets, user identifiers or raw tool output.

Use the existing read-only validation script, only after selecting an explicitly authorized public repository and a fixed calendar date:

```bash
python scripts/skill_observation_review.py --input sanitized-public-observations.json --learning-preview --project-repo example/repo --as-of 2026-10-28
```

The file must already exist. The command reads it once, validates a strict 32-KiB/20-observation bound, and writes **no files**. A normal `--input` without `--learning-preview` continues to use the existing version-1 review schema. No network and no paid API.

## Output semantics

Candidates are grouped only within the explicitly supplied `owner/repo` scope by existing `skill_id` and observation category; foreign-repository links, duplicate IDs and duplicate evidence URLs within a candidate are rejected. Contradictory and stale evidence reduce a bounded `confidence_hint`, which is a **transparent unverified heuristic**, not an empirical probability, a verified GitHub claim or approval. A candidate with fewer than two supporting links is `INSUFFICIENT_SUPPORT`; even with two or more it is `MANUAL_REVIEW_REQUIRED`.

Output always reports `evidence_verified=false`, `owner_approval=NOT_GRANTED`, `auto_promoted=false`, `observer_executed=false`, `model_calls=0` and `skill_files_written=0`. Source links are **claims only**; a separate authorized human reviewer must verify content, relevance, provenance and benefit before proposing a new reusable practice in the existing Issue/PR. No `AGENTS.md`, skills, user memory, global scope, session stores or model selection are changed.

## Failure containment and remaining gates

Fail closed on malformed or extra fields, unsupported project scope, non-public sources, dates in the future or older than 730 days, contradictory/duplicate source accounting or untrusted plan text. The review result is ephemeral; rollback is simply discarding the preview. Actual client execution, learning utility, human evidence validation and an approved reusable-practice lifecycle remain **NOT_VERIFIED** until independently demonstrated. This is not the full automatic ECC instinct pipeline; those background/hook behaviors remain excluded for this owner's environment.

## Explicit public GitHub fact verification (separate opt-in)

A separate command verifies typed assertions associated with the **unchanged** v2 observations and v1 CLI. Supply one assertion for each `source_url`, with the exact fields `source_url`, `predicate` and `expected_sha`:

```json
{
  "schema_version": 1,
  "claims": [
    {"source_url":"https://github.com/example/repo/issues/101","predicate":"issue_exists","expected_sha":null},
    {"source_url":"https://github.com/example/repo/pull/102","predicate":"pr_merged_at_sha","expected_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
  ]
}
```

This is a synthetic illustration, not evidence of real resources. Supported predicates: `issue_exists`, `pr_head_at_sha`, `pr_merged_at_sha`, `run_success_at_sha` and `commit_exists_at_sha`.

```bash
python scripts/skill_learning_verification.py \
  --input sanitized-public-observations.json \
  --claims typed-claims.json \
  --project-repo example/repo --as-of 2026-11-01
```

Optionally provide all four `--skill-root`, `--skill-id`, `--skill-file`, `--skill-expected-sha256` to check a local skill revision. Supported relative paths: `.agents/skills/<skill-id>/SKILL.md` or `extensions/<pack>/skills/<skill-id>/SKILL.md`. A missing or changed source pin prevents review-readiness. A local SHA match does **not** attest a remote commit.

Only on explicit invocation, bounded unauthenticated HTTPS GETs target public `api.github.com`. No redirects, tokens, extra permissions, arbitrary hosts or private sources. The verifier checks exact repository, resource existence, PR head/merge SHA and successful Actions run SHA. Failed network/API checks, forged SHA or failed CI yield `NOT_VERIFIED`. Issue/PR bodies never become instructions or appear in receipts.

`EXISTS_ONLY` means only that an Issue/commit exists, not that a bug is fixed. Merged PR and green CI are not production deployment proof. PRs and runs sharing HEAD SHA count as one independent fact group. Contradictory evidence blocks readiness, and `confidence_hint` remains an uncalibrated heuristic.

## Owner approval and reversible reuse

Candidates produce deterministic structured proposals: `proposal_id`, change type, project scope, narrow evidence status, source revision, necessary tests, risks and rollback. No executable diff is automatically generated, and no skill or `AGENTS.md` is modified.

An authorized owner must **separately** inspect a specific proposal, review factual relevance and exact skill source, and approve the concrete change/diff. The normal branch/PR/review/CI/merge process then makes a reviewed change available in the existing Toolkit scope. Regressions use a separately reviewed revert PR; source SHA changes require re-review. Authorization to merge Issue #436 mechanism code is not approval of a future practice.

Reports always retain `approval=NOT_GRANTED`, `applied=false` and `practice_auto_promotion=false`. Codex Desktop E2E is `NOT_VERIFIED`, real practice benefits are `NOT_MEASURED`, release is `NOT_PUBLISHED`.

## ECC v2 capability gap matrix

| ECC behavior | Existing Toolkit | Gap | Decision |
| --- | --- | --- | --- |
| Claude hooks and Haiku observer | Manual Observer v1/v2 | Automatic capture | Do not import |
| Project-scoped instincts | Offline v2 preview | Fact verification | Explicit GitHub GET only |
| Confidence and contradictions | Recency heuristic | Independent/forged evidence | Typed facts and SHA grouping |
| Evolve/promote/global | GitHub Flow and Skill Manager | Review packet | Structured proposal, no auto-promotion |
| Revoke/decay | Observation age | Changed skill source | Local SHA gate and manual revert |

CI uses synthetic GitHub responses with an injected GET fake: these tests are not live network or model improvement evidence.
