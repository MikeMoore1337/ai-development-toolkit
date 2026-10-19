# Issue #44 - Toolkit Skill Quality v2: семантический аудит

## Масштаб и метод

Базовый коммит: `084ed2ad053cff6caf8ffaebb6283789906a425e` (main, 2026-10-19). Аудит включает **65 навыков, 16 reference roles, 27 профилей** согласно текущему `MANIFEST.json`. Для каждого навыка вручную заданы два положительных и два отрицательных ожидаемых сценария, продуктовый результат, зависимости, пересечения и ограничение полномочий. Полный каталог: [inventory.json](inventory.json), реестр конкретных находок: [findings.json](findings.json). Объекты привязаны к путям и исходному SHA; это не оценка качества «в баллах».

**Итог:** документально подтверждено 16 наблюдений (0 BLOCKER, 0 HIGH, 9 MEDIUM, 7 LOW). По навыкам: 55 KEEP, 8 REFINE, 1 DEPRECATE (уже отмечен legacy), 1 REVIEW. Отсутствие подтверждённых BLOCKER/HIGH не означает, что реальные агенты безопасны или эффективны.

## Десять первоочередных наблюдений

| ID | Фактическая проблема | Куда передать |
| --- | --- | --- |
| SQ44-001 | QA Fullstack предлагается без Playwright; `scripts/recommend_profile.py` | #50 |
| SQ44-002 | QA Python предлагается без проверки pytest; `scripts/recommend_profile.py` | #50 |
| SQ44-003 | Fullstack-профиль не содержит контроллер, который требует его навык; `extensions/fullstack/skills/end-to-end-feature-design/SKILL.md` | #46 |
| SQ44-004 | Задача docs предлагает лишь редакторский навык; `scripts/recommend_profile.py` | #50 |
| SQ44-005 | Отсутствует прямой путь для типовых задач новичка; `scripts/recommend_profile.py` | #49 |
| SQ44-006 | Слово release может означать запуск вместо QA-проверки; `scripts/recommend_profile.py` | #49 |
| SQ44-007 | Первый путь требует Git и Python CLI; `README.md` | #51 |
| SQ44-009 | API Testing не задаёт форму evidence и критерий завершения; `extensions/qa/skills/api-testing/SKILL.md` | #45 |
| SQ44-011 | Make Feature рассчитывает на отдельного приёмщика; `extensions/make-feature/skills/make-feature/SKILL.md` | #45 |
| SQ44-008 | Профиль qa-all включает 27 разных по назначению навыков; `MANIFEST.json` | #50 |

**Другие подтверждённые и низкоприоритетные замечания:** SQ44-010 (LOW, #45), SQ44-012 (LOW, #47), SQ44-013 (LOW, #49), SQ44-014 (LOW, #47), SQ44-015 (LOW, #45), SQ44-016 (LOW, #49). Исходные цитаты и ограничения находятся в машиночитаемом реестре.

## Разделение полномочий и пересечений

- **HARD_EXCLUSIVE_CONTROLLER:** три уже существующих запрета WF001-WF003 для feature-delivery / make-feature / adaptive-delivery. Новых бездоказательных конфликтов не добавлено.
- **INTENTIONAL_COMPOSITION:** implementation + minimal-safe-change; архитектура API + contract-testing; security-boundaries / security-review / security-testing; end-to-end-feature-design + fullstack-integration. Смежные задачи не равны дублированию.
- **SOFT_OVERLAP:** qa-strategy / test-strategy; clear-voice / editorial-naturalness / qa-clear-voice. Выбор по контексту, не новый статический запрет.
- **TRUE_DUPLICATION:** новых доказанных пар не выявлено. **adaptive-delivery** уже deprecated, но его сохранение для v3 явно предусмотрено; без миграционной проверки удалять нельзя.
- Reference roles описывают обязанности, а не автоматически доступных subagents. Одна и та же сессия не становится независимой приёмкой от переименования reviewer. Для qa-verifier, reviewer, test-reviewer и quality-gatekeeper независимость реального контекста остаётся **NOT_MEASURED**.

## Примеры навыков KEEP

Архитектура: `architecture-decisions`, `service-architecture`, `database-migrations`. Безопасность: `security-boundaries`, `security-testing`. Разработка: `implementation`, `minimal-safe-change`. QA: `test-analysis-design`, `failure-triage`, `flaky-analysis`, `test-review`. Все они содержат осмысленные процедуры, явную проверку ограничений либо сопоставление действий с evidence; статус KEEP означает лишь отсутствие обоснования для срочной доработки текста по текущему аудиту.

## Опыт новичка

Для задач «Создать приложение», «Исправить ошибку», «Добавить функцию», «Проверить качество проекта», «Разработать API», «Создать интерфейс» сделана отдельная матрица в inventory.json. Сейчас выбор профиля требует переводить цель в технический `--task`, при этом наличие Python/JS-маркеров не доказывает наличие pytest или Playwright. Отдельный готовый разговорный путь и понятное объяснение результата принадлежат #49/#51; безопасная подготовка установки и диагностика - #50; настоящая проверка удобства с новичками - #52. Не следует заставлять каждый технический SKILL.md пересказывать весь onboarding.

## Provenance и разрешения

`extensions/qa/skills/**` и `extensions/make-feature/skills/make-feature/**` считаются защищёнными зафиксированными исходными файлами (owner-reported ID1337, без независимой юридической верификации). Этот PR **не меняет** такие файлы. Для будущих правок по SQ44-009, SQ44-010, SQ44-011 нужен новый owner review с точным перечнем файлов и ревизий. Отсутствие согласования - блокер для **правки источника**, не для принятия документального аудита. Не публиковать приватные разрешения в Git.

## План исправлений

1. **#45:** уточнить QA api-testing/test-strategy только после owner approval; пересмотреть trigger Clear Voice и fallback Make Feature, не имитировать проверяющего.
2. **#46:** привести Fullstack-инструкции и профиль к одному понятному workflow controller, добавить один сквозной пример.
3. **#47:** исправить таблицы README и непереносимую формулировку INTEGRATION_MATRIX, не менять опубликованные версии.
4. **#49-#51:** понятный выбор по цели, явные предпосылки pytest/Playwright и ясное отличие quality review от deployment.
5. **#52 / #11:** будущие реальные usability и AI-client trials независимо от статической проверки; новые результаты не предполагать.

## Доказательность и ограничения

Ручная семантическая оценка затрагивает `SKILL.md`, связанные документы, роли и manifest-профили. Примеры в inventory.json - ожидаемый выбор, а не проверенная активация модели. Имеющиеся инструменты `validate_pack.py`, `validate_quality.py`, `skill_quality_metrics.py`, `verify_client_compatibility.py`, `validate_provenance.py` и официальный pinned `skills-ref` продолжают быть источниками *отдельных* статических свидетельств; второй анализатор на ключевых словах не создан. Запуск реальных Codex/Claude/Hermes, эффективность, экономия токенов, независимый аудит лицензий: **NOT_MEASURED**.

В рамках #44 запуск новых платных API, запись в другие репозитории, merge/deploy, изменение branch protection, редактирование защищённых исходников и публикация релиза не выполняются.
