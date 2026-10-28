# Полный каталог ECC 2.2.3 для Toolkit (#435)

Источник: affaan-m/ECC commit 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b. Генератор scripts/ecc_gap_catalog.py создаёт матрицу без установки ECC и без запуска моделей. Вход: точная Git-ревизия upstream и provenance реального Toolkit. Обрабатываются ВСЕ Git-отслеживаемые компоненты skills, agents, commands, rules. Фиксируются источник, SHA256, описание, trigger, лицензия, заявленные зависимости/клиенты, аналог в Toolkit, статус, аргумент и тест.

Матрица появляется в GitHub Actions workflow ecc-gap-catalog.yml под артефактом ecc-full-gap-matrix: ecc-gap-full.csv, ecc-gap-full.json, ecc-gap-summary.json. Итоговые количества считываются из Git tree; не использовать маркетинговые цифры как факт. Неоцененные компоненты сохраняются со статусом HOLD_REVIEW, а не пропускаются.

## Выборочная оригинальная интеграция

Upstream имеет штатные команды catalog.js и install-plan.js с ключом --skills. CI проверяет оригинальный план для windows-desktop-e2e на цель codex в одноразовом HOME. Этот навык - ADOPT_AS_IS_CANDIDATE, не разрешение на установку. До фактической установки требуется убедиться, что план не затрагивает другие навыки, AGENTS.md и глобальную конфигурацию. Если совместимость не подтверждена - HOLD.

Два исходных навыка прошли предметную проверку на функциональное покрытие (партия #435 от 28.10.2026):

- **`skills/change-impact` - ALREADY_PRESENT после улучшения**: в Toolkit уже есть `extensions/qa/skills/change-impact-analysis/SKILL.md` и `scripts/qa_change_impact.py` для анализа затронутых вызовов, контрактов, данных и регрессионных проверок. Существующий навык усилен сверкой запланированного охвата с реальным diff, фиксацией расширения объёма и `NOT_VERIFIED`. Новый дублирующий контроллер не устанавливается.
- **`skills/tdd-workflow` - ALREADY_PRESENT после улучшения**: в `.agents/skills/feature-delivery/SKILL.md` добавлен добровольный тестовый цикл RED / минимальный GREEN / рефакторинг с реальными свидетельствами. Из оригинала намеренно не перенесены обязательные для всех 80% покрытия, тесты каждого уровня, автоматические промежуточные коммиты и детектор менеджера пакетов.
- **`skills/continuous-learning` v1 - HOLD_UNSUPPORTED**: устарел по самому ECC; новая реализация рассматривается отдельно в #436.

Это подтверждённое покрытие рабочих сценариев, **не** дословное копирование кода, не live-проверка модели и не аудит всех оставшихся компонентов. Источник закреплён на `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, файлы `skills/change-impact/SKILL.md` и `skills/tdd-workflow/SKILL.md`. Существующий артефакт матрицы сохраняет прежние HOLD-статусы до нового запуска генератора. Сценарии проверки и ограничения - в `catalog_review.json`.

Успех синтетического CI не подтверждает работающий Codex Desktop или Hermes. Без платных API, Codex CLI/Claude CLI, автоматической установки, hook-активации, доступа к сессиям и production. Для клиентов других пользователей возможны добровольные штатные маршруты с отдельным согласием. Откат: удалить workflow и отчётный генератор в PR.

Запуск из доверенного checkout Toolkit: python scripts/ecc_gap_catalog.py --ecc-root /isolated/ECC --toolkit-root . --source-revision 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b --output-dir /tmp/ecc-gap

Дополнительная пофайловая проверка оригинальных api-design, database-migrations, e2e-testing и существующих Skill Toolkit подтверждает покрытие их основной функции. Они помечены ALREADY_PRESENT, с реальными путями аналогов в матрице. Для windows-desktop-e2e оригинальный план --skills раскрывает четыре модуля: platform-configs, skill-unified-memory, workflow-quality и shared-script-utils. Поэтому фактическая установка одного навыка находится на HOLD_SHARED_MODULES, независимо от статуса кандидата на функциональное рассмотрение.
