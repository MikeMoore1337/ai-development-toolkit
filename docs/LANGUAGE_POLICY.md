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
| English-only specialized/audit/history | Remaining docs such as `PROVENANCE_AUDIT.md`, `SKILLS_QUALITY_AUDIT.md` and archived release/evaluation notes |
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

**Next in sequence:** additional high-value EN-only user docs and specialized and historical documents based on practical demand. Broader specialist/audit pages are P2/P3, based on user value. No claim of full bilingual translation until both directions and actual documentation are reviewed.
