# Локальный Toolkit MCP для Codex и Claude Code

[English](../MCP_INSTALL.md) · [Установка](INSTALLATION.md) · [Обновление](UPDATING.md) · [Выбор интеграции](INTEGRATIONS.md)

## Возможности и ограничения

Toolkit содержит настоящий **MCP-сервер stdio** (`scripts/toolkit_mcp.py`) на стандартной библиотеке Python 3.12+. Платные API и запросы к моделям не используются. Восемь инструментов позволяют получить каталог, найти и прочесть навыки и роли, предложить маршрут задачи, посмотреть план установки Skill Manager и статус управляемых навыков. Роли - инструкции, **не автоматически запускаемые агенты**.

**Через MCP доступно только чтение.** Агент не может незаметно установить навык или изменить пользовательский проект. Когда требуется установка, агент предлагает предварительный план, а человек отдельно запускает Skill Manager с `--apply`. Установщик ниже меняет лишь конфигурацию MCP выбранного проекта **после явного --apply**. ИИ-клиенты автоматически не устанавливаются.

## Перед первым запуском

1. Установите Codex или Claude Code отдельно. Сначала выберите [Desktop, CLI, IDE или облако](INSTALLATION.md). MCP не является ИИ-клиентом.
2. Откройте терминал **в корне клонированного Toolkit**. Требуется Python 3.12+. `py -3.12` и `python3.12` ниже - примеры: при установленной Python 3.13/3.14 замените **все** вызовы соответствующей командой (`py -3.14` или `python3.14`).
3. Замените пример пути к проекту на **существующий каталог**. Установщик не создаёт проект.
4. Выберите клиент через `--client codex` или `--client claude`, просмотрите план **без `--apply`** и только затем разрешайте запись.

## Один проектный установщик для Desktop и CLI

- **Codex Desktop:** выберите локальный проект, используйте `--client codex` ниже, перезапустите Desktop и проверьте реальные MCP-инструменты. Отдельный Codex CLI этому установщику **не требуется**.
- **Codex CLI:** выполните те же команды с `--client codex`, запустите `codex` из целевого проекта и проверьте `/mcp`.
- **Claude Code Desktop:** выберите локальный проект во **вкладке Code**, используйте `--client claude`, начните новую сессию и подтвердите проектный MCP.
- **Claude Code CLI:** выполните те же команды с `--client claude`, запустите `claude` из целевого проекта и проверьте `/mcp`.

Установщик пишет `.codex/config.toml` или `.mcp.json` в выбранном проекте и не вызывает CLI клиентов. В IDE/WSL/SSH/контейнере интерпретатор и абсолютные пути Toolkit должны существовать на фактическом хосте выполнения. Шаблоны ниже не настраивают облачную среду или обычный чат Claude/ChatGPT.

**Проверка Project MCP:** запросите `toolkit_catalog`, затем чтение `qa-strategy` через `toolkit_read_skill` в выбранном клиенте. `toolkit_info` и `toolkit_prepare_task` относятся к отдельному [Personal MCP](ONE_COMMAND_SETUP.md), а не Project MCP. Не устанавливайте оба подключения под одним именем, не разрешив конфликт.

## Windows (PowerShell)

**Нужны два разных пути:** `$toolkit` - папка клонированного **AI Development Toolkit**, содержащая `scripts\toolkit_mcp.py`; `$project` - папка **существующего проекта, в котором Codex будет использовать Toolkit** (например, `your-fitness-coach`). Путь к самому ADT в `$project` указывайте только тогда, когда подключаете Toolkit к разработке Toolkit. Этот установщик не подключает MCP глобально ко всем проектам.

**1. Сначала проверьте Python.** Выполните в PowerShell `py --list-paths` и `py -3 --version`. Выбранная версия должна быть **3.12 или новее**. Команда `py -3.12` работает только при наличии именно Python 3.12; `py -3` выбирает доступный Python 3. Если `py` недоступен, проверьте `python --version` и замените `py -3` в примерах на `python` (если версия 3.12+). Если подходящего Python нет, установите его с [python.org](https://www.python.org/downloads/windows/), заново откройте PowerShell и повторите проверку. Ошибка `No suitable Python runtime found` означает, что **установщик даже не запустился**.

**2. Укажите обе папки и проверьте их.** Замените пути в примере на свои. Команды можно выполнять **из любой папки PowerShell**: для скрипта используется абсолютный путь.

~~~powershell
$toolkit = 'D:\Pet-projects\ai-development-toolkit'
$project = 'D:\Pet-projects\your-fitness-coach'
$script = Join-Path $toolkit 'scripts\toolkit_mcp.py'
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw 'Не найдена папка Toolkit: проверьте $toolkit' }
if (-not (Test-Path -LiteralPath $project -PathType Container)) { throw 'Не найдена папка проекта: проверьте $project' }
py -3 -c "import sys; assert sys.version_info >= (3, 12), 'Нужен Python 3.12+'; print(sys.version)"
~~~

**3. Просмотрите план (без изменений файлов).** В **том же окне PowerShell** выполните:

~~~powershell
py -3 $script install --client codex --project $project
~~~

Проверьте путь проекта, имя MCP и список планируемых изменений. Это только предварительный просмотр, установка ещё не выполняется.

**4. Примените изменения, только если план корректен.**

~~~powershell
py -3 $script install --client codex --project $project --apply
~~~

Команда создаёт или обновляет проектный `.codex/config.toml`, не удаляя посторонние настройки.

**5. Проверьте конфигурацию.**

~~~powershell
py -3 $script doctor --client codex --project $project
~~~

Затем перезапустите **Codex Desktop** с выбранным проектом и попросите вызвать `toolkit_catalog`, а затем `toolkit_read_skill` для `qa-strategy`. Команда `doctor` проверяет конфигурацию, но не обнаружение инструментов самим клиентом. **Codex CLI не требуется.** Если между шагами открыли новое окно PowerShell, заново выполните шаг 2, чтобы восстановить переменные.

Если Toolkit должен быть доступен **сразу во всех проектах Codex**, вместо этого используйте [Personal MCP](ONE_COMMAND_SETUP.md): это другое подключение, с другими командами и именами инструментов.

## Linux (bash)

~~~bash
project="$HOME/projects/existing-project"
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project"
~~~

**Остановитесь и проверьте план.** Убедитесь, что выбраны правильный проект, имя MCP и только ожидаемые изменения конфигурации. Затем выполните следующую команду отдельно:

~~~bash
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project" --apply
python3.12 scripts/toolkit_mcp.py doctor --client codex --project "$project"
~~~

## macOS (Apple Silicon и Intel)

~~~bash
python3.12 --version
project="$HOME/Projects/existing-project"
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project"
~~~

**Остановитесь и проверьте план.** Убедитесь, что выбраны правильный проект, имя MCP и только ожидаемые изменения конфигурации. Затем выполните следующую команду отдельно:

~~~bash
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project" --apply
python3.12 scripts/toolkit_mcp.py doctor --client codex --project "$project"
~~~

Для **Claude Code** используйте `--client claude` вместо `--client codex`. Codex получает проектный `.codex/config.toml`, Claude Code - `.mcp.json`. Существующие чужие настройки сохраняются; конфликты и символические ссылки блокируются. Глобальные настройки не изменяются. После применения переподключите MCP, при необходимости подтвердите доверие к проекту и проверьте список инструментов. Для Codex может помочь `codex mcp list`, но наличие записи **не доказывает активацию**.

**Проверка результата:** `doctor` сообщает состояние конфигурации. Затем переподключите Codex/Claude Code и проверьте **в самом клиенте**, появился ли Toolkit MCP и его инструменты. Если их нет, проверьте исполняемый Python, путь к Toolkit, доверие к проекту и настройки клиента. Запись файла сама по себе не доказывает обнаружение или использование инструментов моделью.

## Удаление и обновление

Удаление соответствующей записи также начинается с предпросмотра:

~~~bash
python3.12 scripts/toolkit_mcp.py uninstall --client codex --project /absolute/existing-project
~~~

**Остановитесь и проверьте план.** Убедитесь, что выбраны правильный проект, имя MCP и только ожидаемые изменения конфигурации. Затем выполните следующую команду отдельно:

~~~bash
python3.12 scripts/toolkit_mcp.py uninstall --client codex --project /absolute/existing-project --apply
~~~

В Windows используйте `py -3.12` и настоящий путь Windows. Удаление MCP не удаляет установленные навыки.

Конфигурация содержит **абсолютные пути** к уже полученной копии Toolkit. После перемещения копии удалите прежнюю запись и установите новую. MCP **не обновляется сам в фоне**. Обновление доверенной копии Toolkit выполняется после просмотра изменений Git ([UPDATING.md](UPDATING.md)); затем MCP переподключается. Управляемые навыки обновляются через отдельный предпросмотр Skill Manager.

Реализован MCP stdio JSON-RPC (протокол 2025-11-25 с обычной инициализацией). HTTP-сервера для браузерного ChatGPT, OAuth, фонового демона и автоматического скачивания навыков **нет**. Плагин ChatGPT работает отдельно. CI проверяет протокол и настройки, а работу настоящего Codex/Claude Code с моделью необходимо испытывать отдельно.
