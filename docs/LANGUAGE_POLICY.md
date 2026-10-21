# Documentation languages and translation coverage

[Русская версия](ru/LANGUAGE_POLICY.md) | [English README](../README.md) | [Русский README](../README.ru.md) | [Tracking issue #87](https://github.com/MikeMoore1337/ai-development-toolkit/issues/87)

## Decision

**Two languages for human-facing guidance, one canonical implementation for skills.** Readers should be able to understand how to select, install, use and verify Toolkit features in Russian or English. Do **not** duplicate the installation-time `SKILL.md`, frontmatter, commands, `AGENTS.md`, source scripts, tests or machine-readable profiles solely for translation. Two copies would diverge and could conflict in clients' skill discovery or violate approved source-snapshot constraints.

The canonical skills are **not all English**. The original Make Feature 0.3.0 `SKILL.md`, much of its supporting text, and the Clear Voice skill are predominantly Russian; most other skill definitions are English. Their human-use entry points can be bilingual while their source remains unchanged. This does not establish bilingual activation in any client.

## Audit snapshot - 20 October 2026

The source tree has 34 Markdown pages immediately under `docs/` (excluding `docs/ru/`). Before this change it has 10 Russian documentation pages, with 6 filename-matched EN/RU source/translation pairs in the existing pinned-source registry. This is **not full coverage**. Read these numbers as a dated inventory, not continuously updated metrics.

| Direction / case | Pages and status |
| --- | --- |
| EN → RU available | `INSTALLATION`, `SKILLS_CATALOG`, `CURATED_SKILL_PACKS`, `CLIENT_MIGRATION`, `CLIENT_COMPATIBILITY`, `PUBLICATION_POLICY` |
| Originally Russian; English translations now available in `docs/en/` | [Adaptation](en/ADAPTATION.md), [Integration matrix](en/INTEGRATION_MATRIX.md), [Portability scenarios](en/PORTABILITY_EVAL_SCENARIOS.md), [Task template](en/TASK_PROMPT_TEMPLATE.md) |
| Formerly mixed-language guide | [Source evaluation (RU)](SOURCE_EVALUATION.md) now has an [English counterpart](en/SOURCE_EVALUATION.md); [Quality rubric (EN)](QUALITY_RUBRIC.md) / [RU](ru/QUALITY_RUBRIC.md) |
| More EN → RU guides | [Universal engineering](ru/UNIVERSAL_ENGINEERING.md), [Skill Quality v2](ru/SKILL_QUALITY_V2.md) and [Beginner workflow](ru/BEGINNER_WORKFLOW.md) have Russian counterparts |
| Additional translated technical guides | [Agent Skills spec RU](ru/AGENT_SKILLS_SPEC.md), [Release process RU](ru/RELEASE_PROCESS.md), and [Skill metrics RU](ru/SKILL_QUALITY_METRICS.md); each retains its canonical English source |
| Added repository-operation guides (EN → RU) | [Publishing RU](ru/PUBLISHING.md) / [EN](PUBLISHING.md); [Branch protection RU](ru/BRANCH_PROTECTION.md) / [EN](BRANCH_PROTECTION.md). Existing release and owner gates remain unchanged |
| Source-locked real-agent pilot operator guide (EN → RU) | [Russian operating guide](ru/REAL_AGENT_PILOT.md) / [English canonical source](REAL_AGENT_PILOT.md). Describes the zero-spend hold; does not unlock real agent execution |
| Additional practical guides (EN → RU) | [Skill Evals](ru/SKILL_EVALS.md), [GitHub setup](ru/GITHUB_SETUP.md), [Windows publishing troubleshooting](ru/WINDOWS_PUBLISHING.md). The last two are explicitly first-publication-only for new repositories; source-locked real trials remain blocked |
| Additional audit, evaluation and historical docs (EN → RU) | All eight formerly unpaired source pages now have Russian counterparts: provenance and skills audits, QA portability, Skill Quality v2 anti-patterns, roadmap, v4 evaluation plan, and the historical v5.0.0/v5.2.0 release audits |
| Canonical skill with Russian instructions | Make Feature and Clear Voice; **no parallel installable English `SKILL.md`** |
| Bilingual human guides for Russian-primary skills | [Make Feature EN](MAKE_FEATURE_INTEGRATION.md) / [RU](ru/MAKE_FEATURE_INTEGRATION.md); [Clear Voice EN](CLEAR_VOICE_INTEGRATION.md) / [RU](ru/CLEAR_VOICE_INTEGRATION.md). Original skills remain unchanged. |

Read existing [Russian docs index](ru/README.md) for actual currently translated pages. Never infer the accuracy or freshness of a translation from the presence of a link.

## Rules for new translations

1. Every human guide identifies its counterpart language, canonical source and **truthful scope**: full translation, summary or instructions about a Russian original.
2. Keep code snippets, file paths, task IDs, CLI flags, status constants and approval requirements semantically identical. Provide Windows-specific commands only if supported.
3. Pin source revisions when a file has an EN→RU translated peer, using [SOURCE_REVISIONS.json](ru/SOURCE_REVISIONS.json) and the existing offline freshness check. A checksum verifies the **original version**, not equivalence or translation quality.
4. Translations of originally Russian guides into English must use the same review discipline; the source-revision checker now accepts pinned translations under both `docs/ru/` and `docs/en/`. It warns about changes in either original; it does **not** verify meaning or writing quality.
5. Do not edit protected Make Feature or QA source snapshots, personal licenses or bundled third-party material merely to change language. A new version of source text needs a separate origin/rights review and actual client-compatibility assessment.
6. Maintain clear distinctions: file installation ≠ live client discovery, self-check ≠ independent review, CI PASS ≠ legal distribution permission, docs update ≠ release/deploy.

## Current translation gap inventory (non-blocking)

From the repository root, run:

```bash
python scripts/check_translation_freshness.py --coverage
```

This prints deterministic counts of root `docs/*.md` pages, pages with a filename-matched `docs/ru/` **or** `docs/en/` counterpart, and each unpaired source. A Russian-first guide with an English companion counts as paired. Historical and specialist pages remain visible as gaps rather than disappearing from the audit. **An absent translation does not fail CI.** To separately enforce source-revision freshness on already registered pairs, use `--strict`; neither mode establishes semantic equivalence, human usability or AI-client activation.

**File-pair snapshot (2026-10-21, Issue #87):** all 59 then-existing root `docs/*.md` pages have filename-matched counterparts in `docs/ru/` or `docs/en/`. This demonstrates file coverage only, **not** semantic equivalence, novice usability or skill activation. New documents must appear in future `--coverage` reports. Installed canonical skills are not duplicated for localization.
