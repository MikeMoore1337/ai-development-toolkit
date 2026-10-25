# Политики клиентов - предварительная проверка без запуска

[English](../CLIENT_POLICY_ROUTES.md) | [Задача #395](https://github.com/MikeMoore1337/ai-development-toolkit/issues/395)

Toolkit различает **доступные варианты клиентов**, **пожелания пользователя**, **факт установки программы**, **возможности текущего подключения** и **реальное разрешение на действия**. Галочка в настройках не подтверждает запуск клиента, обращение к модели или отсутствие расходов.

Команда `scripts/client_policy_route.py` использует существующие `toolkit_preferences.py`, `client_capabilities.py` и проверенные реестры клиентов. Она ничего не устанавливает, не вызывает модель, MCP или CLI, не пишет файлы и не расходует средства.

## Примеры

```sh
python scripts/client_policy_route.py --client chatgpt
python scripts/client_policy_route.py --client codex-desktop --target /path/to/project
python scripts/client_policy_route.py --client codex-cli --operation cli-agent --user-config /private/preferences.json
python scripts/client_policy_route.py --client api --operation paid-api --user-config /private/preferences.json
```

Статус может быть `GUIDANCE_ONLY`, `BLOCKED_BY_POLICY` или `REVIEW_REQUIRED`. Последний **не является разрешением на запуск**: поля `execution_authorized=false`, `execution=NOT_EXECUTED`, `model_calls=0` и `paid_api_calls=0` неизменны. Пользователь сам хранит настройки за пределами Toolkit. В комплекте остаётся пример без дополнительных расходов.

| Маршрут | Возможности и границы |
| --- | --- |
| `codex-desktop` | Подсказки по Codex, но не управление Desktop |
| `codex-cli` | Отдельное разрешение на возможность CLI; фактический запуск отсутствует |
| `claude-code` | Аналогично, без вызова Claude CLI |
| `chatgpt`, `chatgpt-plugin` | Подсказки в чате; наличие плагина не доказывает активацию навыка |
| `claude-web` | Работа в чате, без выдуманного локального каталога |
| `mcp` | Протокол, конкретный сервер не считается установленным |
| `api` | Платный путь требует трёх независимых разрешений и отдельной проверки лимитов |

Заявление клиента о поддержке `AVAILABLE` помечается `USER_DECLARED_NOT_VERIFIED`, а не доказательством L4/L5/L6. Реальная интеграция обязана отдельно проверять клиента, разрешения на задачу, источник, изоляцию, секреты, отмену и ограничения расходов. Запрет на выполнение реальных агентных экспериментов из Issue #11 не снимается.

Проверка: `python -m unittest tests.test_client_policy_route -v`. Поддерживается стандартный Python 3.12+ на Windows, Linux и macOS. Установка через Skill Manager по-прежнему требует отдельного `--apply`.
