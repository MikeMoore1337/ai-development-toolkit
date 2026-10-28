# Архив: внешний ECC-плагин Codex — отменён (#424)

**Текущее решение владельца от 28 октября 2026:** Toolkit — самостоятельный продукт, а не надстройка или плагин для ECC. Внешняя установка и регистрация `affaan-m/ECC`, `ecc-universal`, `ecc-memory-mcp`, ECC Codex Marketplace, ECC hooks или sidecar **не требуются и не являются поддерживаемым способом внедрения функций в Toolkit**. [Issue #424](https://github.com/MikeMoore1337/ai-development-toolkit/issues/424) закрыта как `NOT_PLANNED`; [#431](https://github.com/MikeMoore1337/ai-development-toolkit/issues/431) — родительская программа, [#446](https://github.com/MikeMoore1337/ai-development-toolkit/issues/446) — архитектурный переход.

## Для чего остался этот документ

Исторические проверки ECC 2.2.3 были проведены на source SHA `25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, оригинальный `.codex-plugin/plugin.json` рекламировал skills, MCP и hooks, включая выполняемый SessionStart hook и Chrome DevTools MCP. Изучение оригинала помогает понять функциональность и угрозы, **не даёт разрешения устанавливать его пользователю**. Original repository: https://github.com/affaan-m/ECC. Root license MIT; вложенные зависимости и атрибуцию проверять поэлементно.

## Новая архитектура

- Все подтверждённо полезные, отсутствующие возможности ECC переносить (с лицензией и атрибуцией) или реализовывать **в существующих модулях Toolkit**: Skill Manager, MCP, QA/security, project memory, learning, eval evidence, native hooks, профили, worktrees.
- Не дублировать уже существующие функции, не создавать второй router, policy authority, skill manager или agent runtime; не включать новые функции без проверок разрешений и принятого host support.
- Оригинальные [AgentShield #432](https://github.com/MikeMoore1337/ai-development-toolkit/issues/432), [Memory #433](https://github.com/MikeMoore1337/ai-development-toolkit/issues/433), [Observability #434](https://github.com/MikeMoore1337/ai-development-toolkit/issues/434), [601-компонентный каталог #435](https://github.com/MikeMoore1337/ai-development-toolkit/issues/435) служат baseline, но CI оригинального ECC **не подтверждает наличие встроенных функций Toolkit**.
- В рабочем окружении владельца нельзя использовать Codex CLI, Claude CLI, платные API и дополнительные расходы; штатный Codex Desktop Plus — по существующим разрешениям. Для других пользователей дополнительные backend-режимы могут быть отдельно разрешены, но не должны требовать ECC.
- Ранее слитые инструменты исходного сравнения переводятся в **maintenance-only ручной режим**; обычный runtime и PR CI Toolkit не скачивают ECC.

**Критерий внедрения:** пользователь получает функцию с одним установленным Toolkit, локальные положительные и отрицательные тесты проходят, реальные права/изоляция доказаны; runtime-клиентский статус отдельно отмечен VERIFIED или NOT_VERIFIED. Обновления ECC сами ничего не устанавливают и не переписывают.
