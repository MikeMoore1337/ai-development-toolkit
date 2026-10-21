# Сопровождение и поддержка (Issue #66)

[English source](../MAINTENANCE_SUPPORT.md)

Профиль `maintenance-support` добавляет один навык Operations и переиспользует QA, управление задачами, диагностику и безопасный выпуск. Это **не** отдельный Helpdesk, CRM, база тикетов, фоновый агент или контроллер разработки.

## Применение

Новичок: «После обновления приложение перестало сохранять записи. Помоги разобраться и подготовить ответ». Достаточно симптома, ожидаемого и наблюдаемого поведения. Остальное уточняйте по необходимости, не требуя знания технических терминов. Специалист: «Подготовь intake, классификацию, дедупликацию, reproduction evidence, инженерную передачу с AC, QA, версии Issue/PR/build/release/deployment, Known Issues, deprecation и безопасную коммуникацию».

Категории: DEFECT, FEATURE_REQUEST, HOW_TO, CONFIGURATION, ENVIRONMENT, EXTERNAL_DEPENDENCY, SERVICE_INCIDENT, SECURITY_OR_PRIVACY, DUPLICATE, EXPECTED_BEHAVIOR, UNKNOWN. Severity - тяжесть, Priority - срочность; последствия для пользователя и эксплуатации оцениваются отдельно, без выдуманных чисел или SLA.

## Переиспользование

| Функция | Существующие навыки | Дополнение |
| --- | --- | --- |
| Описание ошибок и похожие жалобы | defect-management | Общее обращение, возможный и доказанный дубликат |
| Диагностика | failure-triage, observability-sre | Противоречия, невоспроизводимость, недоступные данные |
| Передача инженерам | project-delivery-management, requirements-traceability | Сквозная связь Report - Issue - PR - AC |
| Проверка и выпуск | quality-gate-assessment, release-safety | QA, merge, published release, канал и версия пользователя не смешиваются |
| Жизненный цикл | documentation-maintenance, product-discovery, security-engineering | Known Issues, согласованная депрекация, приватность |

NOT_REPRODUCED не доказывает, что пользователь ошибается. Одинаковые сообщения ошибок могут иметь разные причины. Без доступа к production нельзя утверждать, что данные просмотрены. Локальный PASS не означает merge или deployment; опубликованный release не подтверждает обновление всех клиентов. После rollback пересматриваются доступность и статус известной проблемы.

Known Issues фиксируют затронутые версии, подтверждённые симптомы и проверенный обходной путь с ограничениями. Changelog - история изменений; release notes - сведения об опубликованном выпуске; support message - ответ одному пользователю. Для прекращения поддержки нужны согласование, уведомление, проверенный способ миграции. Нельзя выдумывать SLA и сроки.

Сообщения по умолчанию DRAFT. Отправка, изменение внешних Issue, merge и deployment требуют отдельного разрешения. В чужих проектах копии Toolkit остаются read-only; результаты по умолчанию в чате, реальные обращения и секреты туда не сохраняются.

## Автономная проверка

`python scripts/validate_maintenance_support.py` и `python -m unittest tests.test_maintenance_support -v`.

Пять синтетических сценариев: до релиза; canary без подтверждения клиента; подтверждение клиента; откат; противоречащие невоспроизводимые обращения. Намеренно повреждённые данные отклоняет тот же независимый проверяющий код. Никаких платных сервисов, production или реальных сообщений. Живые испытания поддержки и активация навыка у ИИ-клиента - NOT_TESTED/NOT_MEASURED.

[Навык](../../extensions/operations/skills/maintenance-support/SKILL.md) - [Контракты](../../extensions/operations/skills/maintenance-support/references/CONTRACTS.md) - [Примеры](../../fixtures/maintenance-support/README.md).
