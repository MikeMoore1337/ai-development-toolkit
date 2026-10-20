# Матрица подключения по проектам

[English translation](en/INTEGRATION_MATRIX.md) | [Языковая политика](ru/LANGUAGE_POLICY.md)

| Контекст | Навыки | Что не включать автоматически |
|---|---|---|
| Любой новый проект, Codex | task-scoping, implementation, qa-strategy, minimal-safe-change | Все hooks, серверы и сторонние зависимости |
| Mobile/web UI | design-system-consistency, screenshot-fidelity, motion-quality по задаче | Новые дизайн-системы, другие наборы иконок, изменение релизных правил |
| Domain backend | feature-delivery, qa-strategy, research-verification | Непроверенные предметно-специфичные формулы, правила и выводы из внешних навыков (например, медицинские, финансовые или инженерные утверждения без источников) |
| Agent runtime | agent-framework-fit, codebase-knowledge-map, provider-reality-check, external-skill-review | NousResearch/hermes-agent целиком, непроверенные хранилища cookies, autopilot/deploy hooks |
| knowledge base | codebase-knowledge-map при масштабном импорте, editorial-naturalness, qa-strategy | Ненужные браузерные движки, LLM-провайдеры и дизайн-генераторы |
| Research Scout | provider-reality-check, research-verification | Бесплатность/качество API без проверки условий и реальных запросов |

Критерии перед активацией любого внешнего проекта:
1. Реальное отсутствие требуемой функции в текущем стеке;
2. Прочитанный лицензированный источник, версия/commit;
3. Анализ полномочий/секретов/внешних вызовов;
4. Сравнение затрат и проверка на отдельной ветке/пилоте;
5. Никакого автоматического переноса инструкций по release/approval.

Изображения/иконки: выбирайте **одну** текущую библиотеку для каждого продукта, а не Lucide + Tabler + Phosphor + Iconoir сразу.

Эффект от навыков требует испытаний на одинаковых задачах: regressions, full task success, scope creep, operator approvals, время, токены, ручные правки. Пока такого эксперимента нет, улучшение является инженерной гипотезой.

## Фактические layouts (структурная совместимость)

Машиночитаемый реестр и границы доказанной совместимости L1-L6: [CLIENT_COMPATIBILITY.md](CLIENT_COMPATIBILITY.md).

| Клиент | Каталог проекта | Управление через Toolkit | Ограничение |
| --- | --- | --- | --- |
| Codex | `.agents/skills/` | Skill Manager `--layout codex` | Нет реального теста обнаружения/использования |
| Claude Code | `.claude/skills/` | Skill Manager `--layout claude` | Не редактировать существующий `CLAUDE.md` |
| Custom | Явный `--skills-dir` | Только `install.py` | Нет гарантии Agent Skills и ownership |
| Hermes | Документированные `.agents/skills/`, `.hermes/skills/` | Прямой Hermes-адаптер не добавлен | Не запускался, механизм доверия требует отдельной проверки |

Два управляемых клиента в одном проекте могут использовать независимые
schema-v1 lockfile. `migrate` переносит только идентичные текущему Toolkit
управляемые файлы; локальный drift и конфликты запрещены. Подробности:
[CLIENT_MIGRATION.md](CLIENT_MIGRATION.md). Структурная совместимость и
успешное копирование не доказывают обнаружение и использование моделью.
