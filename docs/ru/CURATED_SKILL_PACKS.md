# Подбор тематических наборов навыков

[Русская документация](README.md) | [Каталог навыков](SKILLS_CATALOG.md) | [Исходное руководство (EN)](../CURATED_SKILL_PACKS.md)

Наборы используют существующие профили `MANIFEST.json` и каталоги навыков. **Новый менеджер, среда исполнения, обязательные зависимости или автоматическая установка не добавляются.**

## Выберите задачу

| Задача | Основной профиль | Навыков | Дополнения по выбору - автоматически не устанавливаются |
| --- | --- | ---: | --- |
| Серверная разработка, REST API | `backend` | 7 | `data-access`, `database-migrations`, `background-processing`, `authentication-authorization` |
| Интерфейсы и компоненты | `frontend` | 7 | `state-management`, `forms-validation`, `frontend-performance` |
| Сквозная разработка UI и API | `fullstack` | 6 | `cross-layer-debugging`, `contract-testing`, `e2e-testing` |
| Автотесты API на Python | `qa-python` | 7 | Отдельный профиль `qa-ci` при проблемах в CI |
| UI-тесты Playwright | `qa-ui` | 5 | При необходимости `qa-ci` |
| Контрактные и интеграционные тесты | `qa-contract` | 4 | Дополнения по задаче |
| Анализ ошибок CI | `qa-ci` | 4 | Нет |
| Проверка перед выпуском | `qa-release` | 4 | Нет |
| Архитектура ИИ-агентов | `agent-architecture` | 4 | `security-boundaries`, `external-skill-review` |
| Проверка идеи, MVP и PRD | `product-discovery` | 3 | Формальный анализ QA-требований только при необходимости |
| Техническое исследование | `research` | 2 | `codebase-knowledge-map` для больших репозиториев |
| Изучение условий LLM API | `provider-research` | 2 | Платный API не требуется |

## Product Discovery - от идеи к MVP

Необязательный профиль `product-discovery` объединяет один новый продуктовый навык
с существующими `task-scoping` и `research-verification`.
Выход - PRD с проверяемыми гипотезами, а не готовое приложение или доказанный спрос.
[Руководство на русском](PRODUCT_DISCOVERY.md). Платный API и новый установщик не нужны.

## Backend - серверная разработка

Профиль `backend` объединяет существующие инструкции по реализации и проверке кода с `service-architecture` и `api-design`. Навыки `data-access`, `database-migrations`, `background-processing` и `authentication-authorization` добавляйте **только если задача затрагивает эти области**.

Ни один навык не требует обязательного выбора Python, Go, Java, .NET, конкретного фреймворка или базы данных. Если задача ограничивается тестированием, используйте отдельный профиль QA.

## Frontend - клиентская разработка

Профиль `frontend` включает работу с UI, реализацию и проверку, а также `component-architecture` и `frontend-api-integration`. По необходимости добавляйте `state-management`, `forms-validation` или `frontend-performance`.

Ни React, ни Vue, Angular, Svelte, TypeScript или конкретный CSS-фреймворк не обязательны. Для точечной визуальной задачи лучше `ui-fix` или `ui-motion`; при наличии эталонов используйте скриншоты и проверку анимаций.

## Fullstack - взаимодействие слоёв

В `fullstack` входят `end-to-end-feature-design`, `fullstack-integration` и общие навыки планирования, реализации и проверки. `cross-layer-debugging` пригодится для диагностики проблем между слоями, а профильные навыки Frontend, Backend или QA добавляются по потребности.

`fullstack` согласовывает контракты интерфейса и сервера, **но не заменяет** управление поставкой функции. Если нужен отдельный процесс разработки функции, выбирайте **один** из `feature-delivery` или `make-feature`, не оба сразу.

Принципы независимости от стека, границы активации и примеры приёмки: [UNIVERSAL_ENGINEERING.md (EN)](../UNIVERSAL_ENGINEERING.md).

## QA - тестирование и управление качеством

Используйте существующие профили `qa-core`, `qa-python`, `qa-fullstack`, `qa-ui`, `qa-ci`, `qa-contract`, `qa-release`, `qa-security`, `qa-management` и `qa-collaboration`.

Для одной задачи выбирайте **один узкий профиль**. В обычном проекте избегайте `qa-all`. Исходники QA подчиняются существующим ограничениям происхождения и согласованного владельцем снимка. Не считайте Playwright или pytest обязательными для любого проекта.

## Agent Engineering - проектирование агентов

`agent-architecture` содержит `architecture-decisions`, `agent-framework-fit`, `codebase-knowledge-map` и `qa-strategy`. `security-boundaries` добавляйте для анализа границ доверия, `external-skill-review` - перед переносом сторонних навыков.

Для изучения условий LLM API отдельно выбирайте `provider-research`. Не устанавливаются ни Hermes runtime, ни фреймворк агентов. Наличие профиля не означает, что безопасность или работа реального агента проверены.

## Research & Analysis - исследование

`research` объединяет `task-scoping` и `research-verification`. Используйте для технических сравнений и решений, основанных на проверяемых данных. `codebase-knowledge-map` полезен при исследовании больших репозиториев. Для условий провайдеров выбирайте `provider-research`.

Сами по себе эти профили не требуют платного LLM API или поискового API. Не заявляйте актуальность источников без проверки.

## Предварительный просмотр и установка

~~~bash
python scripts/recommend_profile.py --target /path/to/project --task backend
python scripts/recommend_profile.py --target /path/to/project --task frontend
python scripts/recommend_profile.py --target /path/to/project --task fullstack
python scripts/recommend_profile.py --target /path/to/project --task research
python scripts/recommend_profile.py --target /path/to/project --task provider
python scripts/skill_manager.py catalog --profile backend
python scripts/skill_manager.py install --target /path/to/project --profile backend
python scripts/skill_manager.py install --target /path/to/project --profile backend --apply
python scripts/skill_manager.py install --target /path/to/project --profile frontend --layout claude
python scripts/skill_manager.py status --target /path/to/project
python scripts/skill_manager.py update --target /path/to/project
python scripts/skill_manager.py uninstall --target /path/to/project --skills code-review
python scripts/skill_manager.py rollback --target /path/to/project
python scripts/skill_manager.py recover --target /path/to/project
python scripts/profile_metrics.py --profile backend
python scripts/profile_metrics.py
~~~

Изменения выполняются только с `--apply`; предварительный просмотр не записывает файлы. Менеджер отдельно учитывает собственные навыки для Codex (`.agents/skills`) и Claude Code (`.claude/skills`) с раздельными файлами владения.

Повторная установка профиля с уже установленными навыками намеренно отклоняется, а не незаметно объединяется. Для изменения состава предварительно просмотрите удаление (`uninstall --skills ...`) больше не нужных управляемых навыков, затем установку действительно новых (`install --skills ...`). `update` обновляет **только содержимое** уже управляемых навыков, но не изменяет состав профиля.

Не удаляйте и не перезаписывайте чужие или локально изменённые навыки ради обхода конфликтов. Сначала сделайте резервную копию и разберитесь в причинах. См. [установку](INSTALLATION.md) и [миграцию клиентов (EN)](../CLIENT_MIGRATION.md).

Существующие `AGENTS.md` и `CLAUDE.md` не изменяются. Пользовательский каталог навыков поддерживается разовым установщиком, но не механизмом владения Skill Manager.

## Несовместимые сценарии, совместимость и метрики

**Не запускайте одновременно** `feature-delivery` и `make-feature`, а также устаревший `adaptive-delivery` совместно с одним из них. См. [QUALITY_RULES.json](../QUALITY_RULES.json).

Редакторские навыки выбирайте только для редактирования текста. Ограничения конкретного проекта и требуемые разрешения имеют приоритет над универсальными профилями.

`scripts/profile_metrics.py` оценивает байты установленных файлов, корневых `SKILL.md`, справочников, пересечения профилей и количество навыков на основании локальных исходников. Это **не количество токенов**, загружаемых моделью. Toolkit не требует обязательных зависимостей среды исполнения, но отдельный навык может ссылаться на инструменты, необходимые для конкретной задачи.

**Происхождение и права:** используются только существующие навыки без изменения лицензированных снимков. Разрешение ID1337 относится к конкретным ранее зафиксированным версиям файлов. Оно не доказывает независимую юридическую проверку и не заменяет согласование новой публикации. Реальные испытания обнаружения навыков в Codex, Claude или Hermes не заявляются.
