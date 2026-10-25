# Установка Toolkit MCP одной командой и подключение плагина из локального каталога

[English](../ONE_COMMAND_SETUP.md) | [Personal MCP](../../integrations/personal-mcp/README.ru.md) | [Плагин ChatGPT](../../integrations/chatgpt-plugin/README.ru.md)

## Перед установкой

Нужны Git, Python 3.10+ и установленный Codex. Команда ниже подключает **Personal MCP к Codex** в профиле пользователя, не устанавливает нативные навыки и не добавляет плагин в ChatGPT. Не нужны sudo, платные API, повышение прав или изменение рабочего проекта. На рабочем компьютере необходимо разрешение организации.

Команда один раз получает Toolkit из официального GitHub, проверяет адрес Git-источника и отсутствие локальных изменений, после чего вызывает **существующий** установщик. Уже полученную копию она не обновляет: [обновление отдельно](UPDATING.md). Ветка `main` изменяется и **не является** закреплённым релизом с проверенной контрольной суммой. Для строгого контроля используйте [архив конкретного SHA](INTEGRATION_SOURCE_RELEASES.md).

## Windows / PowerShell - вставить одной командой

~~~powershell
& { $ErrorActionPreference='Stop'; $u='https://github.com/MikeMoore1337/ai-development-toolkit.git'; $d=Join-Path $env:LOCALAPPDATA 'ADT-Personal\toolkit-source'; if (Test-Path -LiteralPath $d) { if ((Get-Item -LiteralPath $d -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refusing linked Toolkit source' } } else { New-Item -ItemType Directory -Force -Path (Split-Path -Parent $d) | Out-Null; & git clone --depth 1 -- $u $d; if ($LASTEXITCODE -ne 0) { throw 'Git clone failed' } }; $origin=& git -C $d remote get-url origin; if ($LASTEXITCODE -ne 0 -or $origin -ne $u) { throw 'Unexpected Toolkit origin' }; $dirty=& git -C $d status --porcelain; if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Toolkit source is modified' }; & powershell.exe -NoProfile -File (Join-Path $d 'integrations\personal-mcp\adt-personal\Install-ADT-Personal.ps1') -ToolkitPath $d -Codex; if ($LASTEXITCODE -ne 0) { throw 'MCP installer failed' } }
~~~

Используется штатный установщик Windows; ограничения запуска PowerShell не обходятся. Существующие сторонние подключения MCP сохраняются. Если запись `ai-development-toolkit` уже существует, установщик не подменяет её без проверки.

## Linux и macOS / терминал - вставить одной командой

~~~sh
sh -c 'set -eu; u=https://github.com/MikeMoore1337/ai-development-toolkit.git; d="${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/toolkit-source"; [ ! -L "$d" ] || { echo "Refusing linked Toolkit source" >&2; exit 2; }; if [ ! -e "$d" ]; then mkdir -p "$(dirname "$d")"; git clone --depth 1 -- "$u" "$d"; fi; actual=$(git -C "$d" remote get-url origin); [ "$actual" = "$u" ] || { echo "Unexpected Toolkit origin" >&2; exit 2; }; [ -z "$(git -C "$d" status --porcelain)" ] || { echo "Toolkit source is modified" >&2; exit 2; }; sh "$d/integrations/personal-mcp/adt-personal/Install-ADT-Personal.sh" --source "$d"'
~~~

Shell-установщик Linux/macOS сейчас подключает только **Codex**. Для Claude Code используйте [проектный установщик MCP](MCP_INSTALL.md) с `--client claude`. Реальная установка одной командой на macOS ещё не проверена на физическом устройстве.

## Проверка

Перезапустите Codex, выполните `codex mcp get ai-development-toolkit`, затем в самом Codex проверьте реальные вызовы `toolkit_info` и `toolkit_prepare_task`. Успешная запись файла, самопроверка установщика и CI не доказывают, что модель использовала MCP. Для дополнительной диагностики Windows: `py -3 "$env:LOCALAPPDATA\ADT-Personal\toolkit-source\integrations\personal-mcp\adt-personal\diagnose_mcp.py"`.

Команду можно повторить для **чистой неизменённой** выделенной Git-копии. Она не обновляет исходники и не копирует навыки в рабочие проекты. Если каталог изменён или принадлежит другому источнику, установка останавливается. Планировщик обновления исходников и обновление исполняемого MCP - [отдельные процедуры](UPDATING.md).

## Плагин ChatGPT/Codex - установка из интерфейса

В репозитории добавлен `.agents/plugins/marketplace.json`. В **поддерживаемом ChatGPT Desktop Work/Codex** откройте доверенную локальную копию репозитория, перезапустите приложение, откройте Plugins, выберите источник **AI Development Toolkit (local)** и установите **AI Development Toolkit**. Запись каталога ссылается на готовый плагин с навыками; она не запускает MCP и не требует платного API.

Это **локальный каталог репозитория**, а не публичный каталог ChatGPT. Он не означает установку на веб-версии, iOS или Android. Установленный личный плагин версии `0.1.8` и публичные исходники плагина `0.1.2` - **разные экземпляры**; не перезаписывайте один другим. Без доступа к локальным каталогам остаётся [импорт ZIP через интерфейс](../../integrations/chatgpt-plugin/README.ru.md), если клиент и права это позволяют.

## Публичный каталог - отдельное согласование

Для появления в общем каталоге необходимы [отправка плагина и проверка OpenAI](https://developers.openai.com/plugins/deploy/submission): права и подтверждение издателя, проверенный архив, положительные и отрицательные сценарии, видеодемонстрация, автоматические проверки, модерация и отдельная публикация. **PRIVATE-плагин и локальный каталог не равны опубликованному плагину**. Выполненную публикацию пока не заявляем.

Статусы: `REPO_MARKETPLACE_READY_FOR_CLIENT_TEST` / `PUBLIC_DIRECTORY_NOT_SUBMITTED`. Реальную установку из каталога ChatGPT Desktop и публичное одобрение надо подтверждать отдельно.
