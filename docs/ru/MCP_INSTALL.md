# Локальный Toolkit MCP для Codex и Claude Code

[English](../MCP_INSTALL.md) · [Установка](INSTALLATION.md) · [Обновление](UPDATING.md)

## Возможности и ограничения

Toolkit содержит настоящий **MCP-сервер stdio** (`scripts/toolkit_mcp.py`) на стандартной библиотеке Python 3.12+. Платные API и запросы к моделям не используются. Шесть инструментов позволяют получить каталог, найти и прочесть навык, предложить маршрут задачи, посмотреть план установки Skill Manager и статус управляемых навыков.

**Через MCP доступно только чтение.** Агент не может незаметно установить навык или изменить пользовательский проект. Когда требуется установка, агент предлагает предварительный план, а человек отдельно запускает Skill Manager с `--apply`. Установщик ниже меняет лишь конфигурацию MCP выбранного проекта **после явного --apply**. ИИ-клиенты автоматически не устанавливаются.

## Windows (PowerShell)

Команды из корня Toolkit; выбранный рабочий проект должен уже существовать.

~~~powershell
$project = 'C:\Work\existing-project'
py -3.12 scripts/toolkit_mcp.py install --client codex --project $project
# Сначала проверьте предложенное изменение конфигурации:
py -3.12 scripts/toolkit_mcp.py install --client codex --project $project --apply
py -3.12 scripts/toolkit_mcp.py doctor --client codex --project $project
~~~

## Linux (bash)

~~~bash
project="$HOME/projects/existing-project"
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project"
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project" --apply
python3.12 scripts/toolkit_mcp.py doctor --client codex --project "$project"
~~~

## macOS (Apple Silicon и Intel)

~~~bash
python3.12 --version
project="$HOME/Projects/existing-project"
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project"
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project" --apply
python3.12 scripts/toolkit_mcp.py doctor --client codex --project "$project"
~~~

Для **Claude Code** используйте `--client claude` вместо `--client codex`. Codex получает проектный `.codex/config.toml`, Claude Code - `.mcp.json`. Существующие чужие настройки сохраняются; конфликты и символические ссылки блокируются. Глобальные настройки не изменяются. После применения переподключите MCP, при необходимости подтвердите доверие к проекту и проверьте список инструментов. Для Codex может помочь `codex mcp list`, но наличие записи **не доказывает активацию**.

## Удаление и обновление

Удаление соответствующей записи также начинается с предпросмотра:

~~~bash
python3.12 scripts/toolkit_mcp.py uninstall --client codex --project /absolute/existing-project
python3.12 scripts/toolkit_mcp.py uninstall --client codex --project /absolute/existing-project --apply
~~~

В Windows используйте `py -3.12` и настоящий путь Windows. Удаление MCP не удаляет установленные навыки.

Конфигурация содержит **абсолютные пути** к уже полученной копии Toolkit. После перемещения копии удалите прежнюю запись и установите новую. MCP **не обновляется сам в фоне**. Обновление доверенной копии Toolkit выполняется после просмотра изменений Git ([UPDATING.md](UPDATING.md)); затем MCP переподключается. Управляемые навыки обновляются через отдельный предпросмотр Skill Manager.

Реализован MCP stdio JSON-RPC (протокол 2025-11-25 с обычной инициализацией). HTTP-сервера для браузерного ChatGPT, OAuth, фонового демона и автоматического скачивания навыков **нет**. Плагин ChatGPT работает отдельно. CI проверяет протокол и настройки, а работу настоящего Codex/Claude Code с моделью необходимо испытывать отдельно.
