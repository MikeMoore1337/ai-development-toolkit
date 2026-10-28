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

