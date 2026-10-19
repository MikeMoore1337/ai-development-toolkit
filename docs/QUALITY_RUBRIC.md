# Рубрика оценки качества

Оценивайте каждый навык отдельно; неизвестное не равно пройденной проверке.

- **Портируемость:** отсутствуют необъявленные требования к runtime, ветке, ОС, провайдеру и домену.
- **Контракт:** явные цель, условия применения, границы и ожидаемый результат.
- **Формат:** валидный YAML frontmatter и локальные ссылки.
- **Безопасность:** нет автоматического запуска непроверенного кода или необоснованного расширения полномочий.
- **Проверяемость:** исполнимые команды, тестовые сценарии, фактическое evidence.
- **Происхождение:** источники, лицензии, версия и ограничения сторонних компонентов указаны.
- **Согласованность:** нет противоречий проектным AGENTS.md и другим активным навыкам.

Per-skill numeric static diagnostics (file-byte footprint, Markdown and frontmatter checks, portability-contract metadata, deterministic repeat, pinned baseline diffs) are available through `python scripts/skill_quality_metrics.py --summary --check-repeat`. No unified skill score or measured AI task success is inferred. See [measurement methodology](SKILL_QUALITY_METRICS.md). Empirical model effectiveness remains `NOT_MEASURED` until separate Issue #11 trials.

Offline quality gate: `python scripts/validate_quality.py` checks declared skill/role inventories, links and anchors across repository Markdown (including templates and recipes), path containment, profiles and explicit mutually exclusive workflows in `docs/QUALITY_RULES.json`. It does not infer semantic contradictions from keywords. `BLOCKER` findings break CI; `WARNING`/`INFO` denote manual observations outside the required gate. See [audit](SKILLS_QUALITY_AUDIT.md).

Статусы: `verified` (проверено статически/тестом), `manual` (требует эксперта), `not-applicable`, `unknown`, `failed`. Не называйте пакет полностью проверенным по итогам одного статического анализа.

Provenance statuses (`verified`, `documented`, `requires_owner_review`, `restricted`, `unknown`, `not_applicable`) are **separate** from quality-gate statuses. Both `python scripts/validate_provenance.py --mode inventory` and `--mode release` run as required CI steps on Linux and Windows. A separate Ubuntu 3.12 step validates a clean, exported Git source archive using archive-mode SHA256 verification plus the same release gate. Release mode also enforces the exact immutable owner-approved source snapshots and rejects restricted material, missing owner approvals and reclassification attempts. Neither certifies title, permissions or legal compliance. See [PROVENANCE_AUDIT.md](PROVENANCE_AUDIT.md).

For new and substantially revised skills, see [Toolkit Skill Quality v2](SKILL_QUALITY_V2.md). Semantic trigger and output acceptance criteria use a manual review checklist, not compulsory headings. Existing skills remain valid without new optional sections; source-only metrics never prove runtime activation.
