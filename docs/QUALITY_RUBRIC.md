# Рубрика оценки качества

Оценивайте каждый навык отдельно; неизвестное не равно пройденной проверке.

- **Портируемость:** отсутствуют необъявленные требования к runtime, ветке, ОС, провайдеру и домену.
- **Контракт:** явные цель, условия применения, границы и ожидаемый результат.
- **Формат:** валидный YAML frontmatter и локальные ссылки.
- **Безопасность:** нет автоматического запуска непроверенного кода или необоснованного расширения полномочий.
- **Проверяемость:** исполнимые команды, тестовые сценарии, фактическое evidence.
- **Происхождение:** источники, лицензии, версия и ограничения сторонних компонентов указаны.
- **Согласованность:** нет противоречий проектным AGENTS.md и другим активным навыкам.

Offline quality gate: `python scripts/validate_quality.py` checks declared skill/role inventories, links and anchors across repository Markdown (including templates and recipes), path containment, profiles and explicit mutually exclusive workflows in `docs/QUALITY_RULES.json`. It does not infer semantic contradictions from keywords. `BLOCKER` findings break CI; `WARNING`/`INFO` denote manual observations outside the required gate. See [audit](SKILLS_QUALITY_AUDIT.md).

Статусы: `verified` (проверено статически/тестом), `manual` (требует эксперта), `not-applicable`, `unknown`, `failed`. Не называйте пакет полностью проверенным по итогам одного статического анализа.

Provenance statuses (`verified`, `documented`, `requires_owner_review`, `restricted`, `unknown`, `not_applicable`) are **separate** from quality-gate statuses. Both `python scripts/validate_provenance.py --mode inventory` and `--mode release` run as required CI steps on Linux and Windows. Release mode also enforces the exact immutable owner-approved source snapshots and rejects restricted material, missing owner approvals and reclassification attempts. Neither certifies title, permissions or legal compliance. See [PROVENANCE_AUDIT.md](PROVENANCE_AUDIT.md).
