# Полный каталог ECC 2.2.3 для Toolkit (#435)

Источник: affaan-m/ECC commit 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b. Генератор scripts/ecc_gap_catalog.py создаёт матрицу без установки ECC и без запуска моделей. Вход: точная Git-ревизия upstream и provenance реального Toolkit. Обрабатываются ВСЕ Git-отслеживаемые компоненты skills, agents, commands, rules. Фиксируются источник, SHA256, описание, trigger, лицензия, заявленные зависимости/клиенты, аналог в Toolkit, статус, аргумент и тест.

Матрица появляется в GitHub Actions workflow ecc-gap-catalog.yml под артефактом ecc-full-gap-matrix: ecc-gap-full.csv, ecc-gap-full.json, ecc-gap-summary.json. Итоговые количества считываются из Git tree; не использовать маркетинговые цифры как факт. Неоцененные компоненты сохраняются со статусом HOLD_REVIEW, а не пропускаются.

## Выборочная оригинальная интеграция

Upstream имеет штатные команды catalog.js и install-plan.js с ключом --skills. CI проверяет оригинальный план для windows-desktop-e2e на цель codex в одноразовом HOME. Этот навык - ADOPT_AS_IS_CANDIDATE, не разрешение на установку. До фактической установки требуется убедиться, что план не затрагивает другие навыки, AGENTS.md и глобальную конфигурацию. Если совместимость не подтверждена - HOLD.

change-impact пересекается с Toolkit scripts/qa_change_impact.py; tdd-workflow пересекается с QA-навыками. Для них HOLD_REVIEW, пока не доказан выигрыш. continuous-learning v1 сам ECC считает deprecated, поэтому HOLD_UNSUPPORTED. Полный список и решения в catalog_review.json и CSV.

Успех синтетического CI не подтверждает работающий Codex Desktop или Hermes. Без платных API, Codex CLI/Claude CLI, автоматической установки, hook-активации, доступа к сессиям и production. Для клиентов других пользователей возможны добровольные штатные маршруты с отдельным согласием. Откат: удалить workflow и отчётный генератор в PR.

Запуск из доверенного checkout Toolkit: python scripts/ecc_gap_catalog.py --ecc-root /isolated/ECC --toolkit-root . --source-revision 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b --output-dir /tmp/ecc-gap

Дополнительная пофайловая проверка оригинальных api-design, database-migrations, e2e-testing и существующих Skill Toolkit подтверждает покрытие их основной функции. Они помечены ALREADY_PRESENT, с реальными путями аналогов в матрице. Для windows-desktop-e2e оригинальный план --skills раскрывает четыре модуля: platform-configs, skill-unified-memory, workflow-quality и shared-script-utils. Поэтому фактическая установка одного навыка находится на HOLD_SHARED_MODULES, независимо от статуса кандидата на функциональное рассмотрение.
