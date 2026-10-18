# Матрица подключения по проектам

| Контекст | Навыки | Что не включать автоматически |
|---|---|---|
| Любой новый проект, Codex | task-scoping, implementation, qa-strategy, minimal-safe-change | Все hooks, серверы и сторонние зависимости |
| Mobile/web UI | design-system-consistency, screenshot-fidelity, motion-quality по задаче | Новые дизайн-системы, другие наборы иконок, изменение релизных правил |
| Domain backend | adaptive-delivery, qa-strategy, research-verification | Непроверенные формулы и медико-спортивные выводы из сторонних дизайн-навыков |
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
