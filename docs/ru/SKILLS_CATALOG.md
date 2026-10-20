# Навыки, роли и профили

Актуальный справочник по `MANIFEST.json` и исходным `SKILL.md` этого набора. Количества сверяются с манифестом автоматическими проверками. Описания кратко пересказывают метаданные; доступность зависит от клиента и выбранного профиля. [English source](../SKILLS_CATALOG.md).

## Основные навыки

Эти 23 навыка находятся в `.agents/skills/`.

| Навык | Когда использовать |
| :--- | :--- |
| [`adaptive-delivery`](../../.agents/skills/adaptive-delivery/SKILL.md) | Устаревшая схема выбора глубины работы (v3), оставленная для совместимости. Для новых функций предпочитайте feature-delivery; не запускайте оба процесса вместе. |
| [`agent-framework-fit`](../../.agents/skills/agent-framework-fit/SKILL.md) | Оцените, нужен ли вообще фреймворк оркестрации агентов, прежде чем добавлять LangGraph, CrewAI, DeerFlow или другую полноценную среду. |
| [`architecture-decisions`](../../.agents/skills/architecture-decisions/SKILL.md) | Сравните архитектурные альтернативы при значимых изменениях, не усложняя инфраструктуру без необходимости. |
| [`browser-workflow-evidence`](../../.agents/skills/browser-workflow-evidence/SKILL.md) | Выполняйте браузерные задачи с проверяемым результатом и честным описанием ограничений; для UI-автоматизации и браузерных агентов. |
| [`clear-voice`](../../.agents/skills/clear-voice/SKILL.md) | Пишите и редактируйте естественные тексты на русском и английском, сохраняя проверяемые факты и авторский стиль. |
| [`code-review`](../../.agents/skills/code-review/SKILL.md) | Проверяйте изменения кода на корректность, регрессии, совместимость, безопасность и сопровождаемость. |
| [`codebase-knowledge-map`](../../.agents/skills/codebase-knowledge-map/SKILL.md) | Исследуйте связи компонентов и зависимости больших репозиториев, если обычного поиска недостаточно. |
| [`design-system-consistency`](../../.agents/skills/design-system-consistency/SKILL.md) | Проверяйте интерфейсы на соответствие существующей дизайн-системе, не ломая визуальную целостность. |
| [`documentation-maintenance`](../../.agents/skills/documentation-maintenance/SKILL.md) | Обновляйте документацию вслед за изменениями поведения, конфигурации, публичных контрактов и инструкций. |
| [`editorial-naturalness`](../../.agents/skills/editorial-naturalness/SKILL.md) | Редактируйте пользовательский и профессиональный текст на русском или английском без искажения фактов. |
| [`external-skill-review`](../../.agents/skills/external-skill-review/SKILL.md) | Оценивайте сторонние навыки, установщики, хуки и MCP-инструменты перед подключением. |
| [`feature-delivery`](../../.agents/skills/feature-delivery/SKILL.md) | Управляйте реализацией функции с глубиной quick/normal/deep по риску и неопределённости; фиксируйте критерии и доказательства готовности. |
| [`implementation`](../../.agents/skills/implementation/SKILL.md) | Реализуйте ограниченное изменение кода, соблюдая соглашения проекта и проверяя поведение. |
| [`minimal-safe-change`](../../.agents/skills/minimal-safe-change/SKILL.md) | Выбирайте минимальное поддерживаемое решение с учётом тестов, безопасности и совместимости. |
| [`motion-quality`](../../.agents/skills/motion-quality/SKILL.md) | Оценивайте назначение, длительность, доступность и производительность анимаций. |
| [`provider-reality-check`](../../.agents/skills/provider-reality-check/SKILL.md) | Проверяйте актуальные условия и бесплатные лимиты поставщиков LLM API по официальным источникам. |
| [`qa-strategy`](../../.agents/skills/qa-strategy/SKILL.md) | Выбирайте риск-ориентированные unit, integration, contract, UI и E2E-проверки. |
| [`release-safety`](../../.agents/skills/release-safety/SKILL.md) | Подготавливайте выпуск и развёртывание по реальному процессу проекта и только в пределах полученных разрешений. |
| [`research-verification`](../../.agents/skills/research-verification/SKILL.md) | Исследуйте неизвестные технические вопросы с проверкой первоисточников, актуальности и неопределённости. |
| [`screenshot-fidelity`](../../.agents/skills/screenshot-fidelity/SKILL.md) | Сравнивайте реализованный интерфейс с эталонными скриншотами, включая адаптивность и регрессии. |
| [`security-boundaries`](../../.agents/skills/security-boundaries/SKILL.md) | Проверяйте границы доверия, учётные данные и опасные сценарии при изменениях безопасности. |
| [`skill-portability`](../../.agents/skills/skill-portability/SKILL.md) | Создавайте, переносите и оценивайте Agent Skills с проверкой структуры, ссылок, совместимости и происхождения. |
| [`task-scoping`](../../.agents/skills/task-scoping/SKILL.md) | Формулируйте границы, критерии приёмки и зависимости задачи до начала реализации. |

## Расширение Frontend

Необязательные навыки, не привязанные к конкретной технологии, из `extensions/frontend/skills/`.

| Навык | Когда использовать |
| :--- | :--- |
| [`component-architecture`](../../extensions/frontend/skills/component-architecture/SKILL.md) | Определяйте границы UI-компонентов без навязывания фреймворка. |
| [`state-management`](../../extensions/frontend/skills/state-management/SKILL.md) | Определяйте источники состояния и учитывайте конкурентные изменения. |
| [`frontend-api-integration`](../../extensions/frontend/skills/frontend-api-integration/SKILL.md) | Согласовывайте реальные контракты API и состояния интерфейса. |
| [`forms-validation`](../../extensions/frontend/skills/forms-validation/SKILL.md) | Проектируйте состояния форм и понятные сообщения о проверке ввода. |
| [`frontend-performance`](../../extensions/frontend/skills/frontend-performance/SKILL.md) | Измеряйте и устраняйте подтверждённые проблемы производительности UI. |

## Расширение Backend

Необязательные навыки, не привязанные к конкретной технологии, из `extensions/backend/skills/`.

| Навык | Когда использовать |
| :--- | :--- |
| [`service-architecture`](../../extensions/backend/skills/service-architecture/SKILL.md) | Определяйте границы сервисов и их зависимости. |
| [`api-design`](../../extensions/backend/skills/api-design/SKILL.md) | Проектируйте совместимые контракты API на стороне поставщика. |
| [`data-access`](../../extensions/backend/skills/data-access/SKILL.md) | Проверяйте целостность данных и корректность запросов к хранилищу. |
| [`database-migrations`](../../extensions/backend/skills/database-migrations/SKILL.md) | Планируйте изменения схемы, совместимость и восстановление. |
| [`background-processing`](../../extensions/backend/skills/background-processing/SKILL.md) | Определяйте семантику фоновых задач, доставки и повторных попыток. |
| [`authentication-authorization`](../../extensions/backend/skills/authentication-authorization/SKILL.md) | Проверяйте, что операции с ресурсами разрешены доверенной моделью доступа. |

## Расширение Fullstack

Необязательные навыки, не привязанные к конкретной технологии, из `extensions/fullstack/skills/`.

| Навык | Когда использовать |
| :--- | :--- |
| [`fullstack-integration`](../../extensions/fullstack/skills/fullstack-integration/SKILL.md) | Согласовывайте контракты и поставку изменений между UI и сервером. |
| [`cross-layer-debugging`](../../extensions/fullstack/skills/cross-layer-debugging/SKILL.md) | Диагностируйте неисправности на границе интерфейса и серверных компонентов. |
| [`end-to-end-feature-design`](../../extensions/fullstack/skills/end-to-end-feature-design/SKILL.md) | Проектируйте сквозную функцию с проверяемыми критериями приёмки. |

## Расширение Product Discovery

Необязательный навык для проверки продуктовых решений до разработки.

| Навык | Когда использовать |
| :--- | :--- |
| [`product-discovery`](../../extensions/product/skills/product-discovery/SKILL.md) | Выделить проблему и гипотезы, границы MVP, проверяемый PRD и метрики до разработки. |

[Руководство Product Discovery для новичков и экспертов](PRODUCT_DISCOVERY.md).

## Расширение Project & Delivery Management

Необязательное управление планом, зависимостями, рисками и доказательствами готовности. Не заменяет `feature-delivery`, `make-feature` или существующие GitHub Issues.

| Навык | Когда использовать |
| :--- | :--- |
| [`project-delivery-management`](../../extensions/management/skills/project-delivery-management/SKILL.md) | Превратить PRD в проверяемый план задач, зависимостей, рисков и статусов. |

[Руководство](PROJECT_DELIVERY_MANAGEMENT.md).

## Расширение Business & System Analysis

Необязательный анализ потребностей, бизнес-правил, сценариев, границ предметной области и NFR с передачей в UX/UI, разработку и QA. Не дублирует Product Discovery, Delivery Management и QA.

| Навык | Когда использовать |
| :--- | :--- |
| [`business-system-analysis`](../../extensions/analysis/skills/business-system-analysis/SKILL.md) | Превратить исходные R-ID и AC-ID в проверяемую системную спецификацию с конфликтами, неизвестными контрактами и трассировкой. |

[Руководство для новичков и специалистов](BUSINESS_SYSTEM_ANALYSIS.md).

## Расширение UX/UI Design

Необязательный процесс от требований к экранам и передаче в разработку с использованием существующих навыков.

| Навык | Когда использовать |
| :--- | :--- |
| [`ux-design-process`](../../extensions/design/skills/ux-design-process/SKILL.md) | Связать пользовательские сценарии, навигацию, прототип и проверяемый контракт разработчика. |

[Руководство по UX/UI](UX_UI_DESIGN.md).

## AI Engineering & QA

Опциональный навык [ai-engineering-qa](../../extensions/ai/skills/ai-engineering-qa/SKILL.md) проверяет версии наборов LLM, регрессию промптов, поиск и обоснованность RAG-ответов, права инструментов на синтетических офлайн-примерах. [Руководство](AI_ENGINEERING_QA.md). Без второго исполнителя моделей и платных API.

## Security Engineering

Опциональный [security-engineering](../../extensions/security/skills/security-engineering/SKILL.md) связывает угрозы, границы доверия, риски и проверяемые защитные меры. [Руководство](SECURITY_DEVSECOPS.md). Один новый навык без сканера.

## Performance & Load Testing

Опциональный [performance-load-testing](../../extensions/performance/skills/performance-load-testing/SKILL.md) описывает ограниченные модели нагрузки, метрики задержек, пропускную способность, ошибки, бюджеты и честное сравнение baseline/candidate. [Руководство](PERFORMANCE_LOAD_TESTING.md). Без внешней нагрузки.

## Reliability Testing

Опциональный [reliability-testing](../../extensions/reliability/skills/reliability-testing/SKILL.md) проверяет инварианты при отказах, ограниченные повторы, гонки, порядок событий и восстановление. Девять офлайн-пар эталон/дефект используют условную SQLite-модель. [Руководство](RELIABILITY_TESTING.md). Не доказывает свойства реального брокера.

## QA Engineering Pack

Расширение QA необязательно и не устанавливается автоматически вместе с Core.

| Навык | Когда использовать |
| :--- | :--- |
| [`api-testing`](../../extensions/qa/skills/api-testing/SKILL.md) | Проектируйте API-тесты по контрактам, изменениям состояния и семантике ошибок. |
| [`change-impact-analysis`](../../extensions/qa/skills/change-impact-analysis/SKILL.md) | Связывайте изменения с затронутыми контрактами, вызывающими компонентами и регрессионными тестами. |
| [`collaborative-development`](../../extensions/qa/skills/collaborative-development/SKILL.md) | Согласовывайте параллельную работу людей и ИИ над тестами, ветками и общими ресурсами. |
| [`contract-testing`](../../extensions/qa/skills/contract-testing/SKILL.md) | Защищайте совместимость API, событий и схем сообщений при изменениях. |
| [`coverage-analysis`](../../extensions/qa/skills/coverage-analysis/SKILL.md) | Оценивайте покрытие требований и рисков, а не только процент строк. |
| [`database-validation`](../../extensions/qa/skills/database-validation/SKILL.md) | Проверяйте семантику хранения, миграции и целостность данных независимо от СУБД. |
| [`defect-management`](../../extensions/qa/skills/defect-management/SKILL.md) | Оформляйте воспроизведённые дефекты с доказательствами и понятным описанием. |
| [`e2e-testing`](../../extensions/qa/skills/e2e-testing/SKILL.md) | Выбирайте ценные сквозные сценарии пользователя и собирайте доказательства. |
| [`failure-triage`](../../extensions/qa/skills/failure-triage/SKILL.md) | Определяйте источник падения тестов и CI по фактам, отделяя дефект продукта от инфраструктуры. |
| [`flaky-analysis`](../../extensions/qa/skills/flaky-analysis/SKILL.md) | Выясняйте причину нестабильных тестов и устраняйте недетерминизм. |
| [`graphify-adapter`](../../extensions/qa/skills/graphify-adapter/SKILL.md) | По необходимости используйте согласованный граф кода для анализа вызовов, зависимостей и влияния изменений. |
| [`integration-testing`](../../extensions/qa/skills/integration-testing/SKILL.md) | Проверяйте работу на реальных границах компонентов: очередях, БД и внешних API. |
| [`playwright-testing`](../../extensions/qa/skills/playwright-testing/SKILL.md) | Создавайте устойчивые UI-проверки Playwright, корректные ожидания и трассировки, если проект использует Playwright. |
| [`pytest-test-design`](../../extensions/qa/skills/pytest-test-design/SKILL.md) | Проектируйте детерминированные Python-тесты с pytest fixtures и параметризацией, если установлен pytest. |
| [`qa-clear-voice`](../../extensions/qa/skills/qa-clear-voice/SKILL.md) | Улучшайте ясность и точность русскоязычных отчётов QA, инцидентов и тестовой документации. |
| [`qa-code-review`](../../extensions/qa/skills/qa-code-review/SKILL.md) | Проверяйте качество кода автотестов, фикстур и тестовой инфраструктуры. |
| [`qa-safe-change`](../../extensions/qa/skills/qa-safe-change/SKILL.md) | Планируйте небольшие безопасные изменения общей инфраструктуры тестирования с проверяемым результатом. |
| [`quality-gate-assessment`](../../extensions/qa/skills/quality-gate-assessment/SKILL.md) | Оценивайте готовность слияния или релиза по критериям и реальным доказательствам. |
| [`requirement-analysis`](../../extensions/qa/skills/requirement-analysis/SKILL.md) | Преобразуйте запросы в проверяемые результаты, находите пробелы и неоднозначности. |
| [`requirements-traceability`](../../extensions/qa/skills/requirements-traceability/SKILL.md) | Связывайте требования, тесты, запуски и доказательства для аудита и передачи между командами. |
| [`security-review`](../../extensions/qa/skills/security-review/SKILL.md) | Проверяйте безопасность тестовых репозиториев, CI и вспомогательных инструментов. |
| [`security-testing`](../../extensions/qa/skills/security-testing/SKILL.md) | Разрабатывайте негативные проверки прав доступа, границ доверия, сессий и пользовательских данных. |
| [`test-analysis-design`](../../extensions/qa/skills/test-analysis-design/SKILL.md) | Применяйте классы эквивалентности, граничные значения, переходы состояний и явные оракулы тестирования. |
| [`test-data-management`](../../extensions/qa/skills/test-data-management/SKILL.md) | Организуйте изолированные воспроизводимые данные и очистку, включая параллельные тесты. |
| [`test-management`](../../extensions/qa/skills/test-management/SKILL.md) | Связывайте автотесты с системами управления тестированием без привязки к поставщику. |
| [`test-review`](../../extensions/qa/skills/test-review/SKILL.md) | Независимо проверяйте, способны ли тесты обнаружить регрессии и не дают ли ложный успех. |
| [`test-strategy`](../../extensions/qa/skills/test-strategy/SKILL.md) | Выбирайте стратегию unit, contract, API, integration, E2E и исследовательских тестов по рискам. |

## Расширение для разработки функций

| Навык | Когда использовать |
| :--- | :--- |
| [`make-feature`](../../extensions/make-feature/skills/make-feature/SKILL.md) | Разрабатывайте функцию из краткого запроса: определяйте решения, реализуйте и проверяйте результат с учётом риска. |

**Важно:** для одной задачи выбирайте только один процесс управления разработкой. Не запускайте `make-feature` и `feature-delivery` одновременно.

## Роли агентов

Роли - справочные инструкции, а не самостоятельно работающие программы. Текущие установщики копируют только навыки.

| Набор | Роль | Ссылка |
| :--- | :--- | :--- |
| Core | `implementer` | [Роль](../../.agents/roles/implementer.md) |
| Core | `orchestrator` | [Роль](../../.agents/roles/orchestrator.md) |
| Core | `qa-verifier` | [Роль](../../.agents/roles/qa-verifier.md) |
| Core | `researcher` | [Роль](../../.agents/roles/researcher.md) |
| Core | `reviewer` | [Роль](../../.agents/roles/reviewer.md) |
| QA | `ci-investigator` | [Роль](../../extensions/qa/roles/ci-investigator.md) |
| QA | `coverage-analyst` | [Роль](../../extensions/qa/roles/coverage-analyst.md) |
| QA | `flaky-analyst` | [Роль](../../extensions/qa/roles/flaky-analyst.md) |
| QA | `qa-architect` | [Роль](../../extensions/qa/roles/qa-architect.md) |
| QA | `quality-gatekeeper` | [Роль](../../extensions/qa/roles/quality-gatekeeper.md) |
| QA | `requirement-analyst` | [Роль](../../extensions/qa/roles/requirement-analyst.md) |
| QA | `security-reviewer` | [Роль](../../extensions/qa/roles/security-reviewer.md) |
| QA | `test-designer` | [Роль](../../extensions/qa/roles/test-designer.md) |
| QA | `test-implementer` | [Роль](../../extensions/qa/roles/test-implementer.md) |
| QA | `test-management-analyst` | [Роль](../../extensions/qa/roles/test-management-analyst.md) |
| QA | `test-reviewer` | [Роль](../../extensions/qa/roles/test-reviewer.md) |


[Управление планом разработки](PROJECT_DELIVERY_MANAGEMENT.md): опциональный Management-навык, не контроллер и не отдельный трекер задач.

## Профили

См. [тематические наборы навыков](CURATED_SKILL_PACKS.md) для выбора по задаче, дополнительных навыков и безопасного переключения.

Профиль - именованная подборка существующих навыков. Изучите её до установки.

| Профиль | Навыки |
| :--- | :--- |
| `security-engineering` | `security-engineering`, `security-boundaries`, `security-review`, `security-testing` |
| `performance-load-testing` | `performance-load-testing`, `test-strategy`, `failure-triage` |
| `reliability-testing` | `reliability-testing`, `background-processing`, `integration-testing`, `failure-triage` |
| `ai-engineering-qa` | `ai-engineering-qa`, `research-verification`, `security-boundaries`, `test-analysis-design`, `contract-testing` |
| `agent-architecture` | `architecture-decisions`, `agent-framework-fit`, `codebase-knowledge-map`, `qa-strategy` |
| `business-system-analysis` | `business-system-analysis`, `task-scoping`, `requirement-analysis`, `requirements-traceability` |
| `ux-design` | `ux-design-process`, `design-system-consistency`, `component-architecture`, `task-scoping` |
| `backend` | `task-scoping`, `architecture-decisions`, `service-architecture`, `api-design`, `implementation`, `qa-strategy`, `code-review` |
| `frontend` | `task-scoping`, `design-system-consistency`, `component-architecture`, `frontend-api-integration`, `implementation`, `qa-strategy`, `code-review` |
| `fullstack` | `task-scoping`, `end-to-end-feature-design`, `fullstack-integration`, `implementation`, `qa-strategy`, `code-review` |
| `product-discovery` | `product-discovery`, `task-scoping`, `research-verification` |
| `project-delivery-management` | `project-delivery-management`, `task-scoping`, `requirements-traceability`, `quality-gate-assessment` |
| `research` | `task-scoping`, `research-verification` |
| `browser-task` | `browser-workflow-evidence`, `qa-strategy` |
| `codex-feature` | `task-scoping`, `feature-delivery`, `minimal-safe-change`, `implementation`, `qa-strategy`, `code-review` |
| `docs-technical` | `documentation-maintenance`, `research-verification` |
| `editorial` | `clear-voice` |
| `editorial-qa` | `qa-clear-voice` |
| `feature-delivery` | `feature-delivery`, `minimal-safe-change`, `implementation`, `qa-strategy`, `release-safety` |
| `general` | `task-scoping`, `implementation`, `qa-strategy`, `code-review`, `minimal-safe-change` |
| `make-feature` | `make-feature` |
| `provider-research` | `research-verification`, `provider-reality-check` |
| `qa-all` | `api-testing`, `change-impact-analysis`, `collaborative-development`, `contract-testing`, `coverage-analysis`, `database-validation`, `defect-management`, `e2e-testing`, `failure-triage`, `flaky-analysis`, `graphify-adapter`, `integration-testing`, `playwright-testing`, `pytest-test-design`, `qa-clear-voice`, `qa-code-review`, `qa-safe-change`, `quality-gate-assessment`, `requirement-analysis`, `requirements-traceability`, `security-review`, `security-testing`, `test-analysis-design`, `test-data-management`, `test-management`, `test-review`, `test-strategy` |
| `qa-ci` | `failure-triage`, `flaky-analysis`, `test-data-management`, `test-review` |
| `qa-collaboration` | `collaborative-development`, `qa-safe-change`, `qa-code-review`, `test-review` |
| `qa-contract` | `contract-testing`, `integration-testing`, `api-testing`, `change-impact-analysis` |
| `qa-core` | `requirement-analysis`, `test-analysis-design`, `test-review`, `change-impact-analysis`, `quality-gate-assessment` |
| `qa-fullstack` | `requirement-analysis`, `test-analysis-design`, `test-review`, `change-impact-analysis`, `api-testing`, `contract-testing`, `integration-testing`, `e2e-testing`, `playwright-testing` |
| `qa-management` | `requirements-traceability`, `test-management`, `defect-management`, `quality-gate-assessment` |
| `qa-python` | `test-analysis-design`, `test-review`, `api-testing`, `pytest-test-design`, `database-validation`, `test-data-management`, `failure-triage` |
| `qa-release` | `change-impact-analysis`, `coverage-analysis`, `requirements-traceability`, `quality-gate-assessment` |
| `qa-security` | `security-testing`, `test-data-management`, `test-review`, `quality-gate-assessment` |
| `qa-ui` | `test-analysis-design`, `e2e-testing`, `playwright-testing`, `test-review`, `quality-gate-assessment` |
| `skill-import` | `skill-portability`, `external-skill-review`, `research-verification` |
| `ui-fix` | `task-scoping`, `design-system-consistency`, `screenshot-fidelity`, `qa-strategy` |
| `ui-motion` | `design-system-consistency`, `motion-quality`, `qa-strategy` |

См. [инструкции по установке](INSTALLATION.md) для предварительного просмотра, расположения навыков и ограничений совместимости.
