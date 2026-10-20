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
| Originally Russian; English missing | `ADAPTATION.md`, `INTEGRATION_MATRIX.md`, `PORTABILITY_EVAL_SCENARIOS.md`, `TASK_PROMPT_TEMPLATE.md` |
| Mixed Russian and English, requires editorial treatment | `QUALITY_RUBRIC.md`, `SOURCE_EVALUATION.md` |
| English-only high priority | `BEGINNER_WORKFLOW.md`, `UNIVERSAL_ENGINEERING.md`, `SKILL_QUALITY_V2.md` |
| English-only specialized/audit/history | Remaining docs such as `PROVENANCE_AUDIT.md`, `RELEASE_PROCESS.md`, `SKILLS_QUALITY_AUDIT.md` and archived release/evaluation notes |
| Canonical skill with Russian instructions | Make Feature and Clear Voice; **no parallel installable English `SKILL.md`** |
| This change | [Make Feature user guide (EN)](MAKE_FEATURE_INTEGRATION.md) and [guide (RU)](ru/MAKE_FEATURE_INTEGRATION.md) |

Read existing [Russian docs index](ru/README.md) for actual currently translated pages. Never infer the accuracy or freshness of a translation from the presence of a link.

## Rules for new translations

1. Every human guide identifies its counterpart language, canonical source and **truthful scope**: full translation, summary or instructions about a Russian original.
2. Keep code snippets, file paths, task IDs, CLI flags, status constants and approval requirements semantically identical. Provide Windows-specific commands only if supported.
3. Pin source revisions when a file has an EN→RU translated peer, using [SOURCE_REVISIONS.json](ru/SOURCE_REVISIONS.json) and the existing offline freshness check. A checksum verifies the **original version**, not equivalence or translation quality.
4. Translations of originally Russian guides into English must use the same review discipline; automatic hashing in the existing script is currently **one-directional**, and bidirectional checking is tracked in #87. Do not claim both directions are already automated.
5. Do not edit protected Make Feature or QA source snapshots, personal licenses or bundled third-party material merely to change language. A new version of source text needs a separate origin/rights review and actual client-compatibility assessment.
6. Maintain clear distinctions: file installation ≠ live client discovery, self-check ≠ independent review, CI PASS ≠ legal distribution permission, docs update ≠ release/deploy.

**Next in sequence:** English companion guides for Russian originals, Russian [beginner workflow](BEGINNER_WORKFLOW.md), and an editorial EN/RU separation of mixed-language pages. Broader specialist/audit pages are P2/P3, based on user value. No claim of full bilingual translation until both directions and actual documentation are reviewed.
