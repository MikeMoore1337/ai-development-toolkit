# ADT для Cursor - нативный плагин и существующий Personal MCP

**Статус:** исходники плагина и проверяемый локальный установщик. Реальную загрузку и применение в Cursor нужно подтвердить в запущенном клиенте отдельно. Публикация в Cursor Marketplace не выполняется автоматически.

## Что входит

- `.cursor-plugin/plugin.json`, `mcp.json`: формат Cursor Plugin с подключением **уже установленного** ADT Personal MCP в режиме stdio/READ_ONLY.
- `skills/`: четыре нативных Agent Skills (разработка, QA, безопасность, UX/UI).
- `rules/`: краткое правило маршрутизации при явном выборе ADT, без самостоятельных действий и конфликтующих контроллеров.
- `commands/`: команды `/adt-build`, `/adt-qa`, `/adt-security`, `/adt-ui`.
- `scripts/manage.py`: проверка, установка, обновление и безопасный откат локального пакета.
- `scripts/launch_mcp.py`: использует существующие файлы ADT Personal MCP и его отдельный Git-источник, ничего не загружает и не устанавливает.

## Перед установкой

Нужны Python 3.10+, Cursor и установленный ADT Personal MCP с постоянной копией Toolkit (см. [Personal MCP](../personal-mcp/README.ru.md)). На Windows стандартные пути:
`%LOCALAPPDATA%\ADT-Personal\mcp\adt_mcp.py` и `%LOCALAPPDATA%\ADT-Personal\toolkit-source`.

Если пути отличаются, укажите **локальные абсолютные** `ADT_PERSONAL_MCP` и `ADT_TOOLKIT_SOURCE` в окружении процесса Cursor. Linux/macOS по умолчанию используют `${XDG_DATA_HOME:-~/.local/share}/adt-personal`. Убедитесь, что `python` доступен в окружении Cursor. Плагин **не** ставит MCP бинарник, не обновляет копию исходников и не копирует навыки в чужие проекты.

## Установка (Windows PowerShell)

Из корня чистой, проверенной копии Toolkit:

```powershell
python integrations/cursor-plugin/scripts/manage.py install
python integrations/cursor-plugin/scripts/manage.py install --apply
python integrations/cursor-plugin/scripts/manage.py doctor
```

Сначала увидите `PREVIEW` без изменений. Применение создаёт локальный пакет в `~/.cursor/plugins/local/ai-development-toolkit`; чужие файлы в этой папке не перезаписываются. Cursor по [официальной инструкции](https://cursor.com/docs/plugins) обнаруживает локальные плагины после **Developer: Reload Window** или перезапуска, если политика позволяет местные плагины.

В **Cursor → Customize** убедитесь, что четыре навыка, правила, команды и MCP обнаружены. В Cursor Agent действительно вызовите `toolkit_info`, `toolkit_prepare_task` и подходящий `toolkit_get_skill`. Отдельно проверьте реальное использование методики на небольшой задаче. Успешный `doctor` проверяет локальные файлы, **не** обнаружение Cursor.

**Важно:** не добавляйте тот же MCP ещё раз в глобальный `~/.cursor/mcp.json`: получите дублирование. Если уже добавлен, сохраните другой существующий MCP и удалите только прежнюю запись ADT после проверки.

## Обновление, диагностика, откат

После обновления **проверенной** исходной копии Toolkit:

```powershell
python integrations/cursor-plugin/scripts/manage.py update
python integrations/cursor-plugin/scripts/manage.py update --apply
python integrations/cursor-plugin/scripts/manage.py status
python integrations/cursor-plugin/scripts/manage.py doctor
python integrations/cursor-plugin/scripts/manage.py rollback
python integrations/cursor-plugin/scripts/manage.py rollback --apply
```

- `update` сначала показывает план. `--apply` сохраняет предыдущий управляемый пакет отдельно в пользовательском каталоге `ADT-Cursor/backups`.
- `rollback` восстанавливает последнюю управляемую версию либо удаляет первую установку. Если пользователь менял файлы установленного плагина, операция блокируется с `DRIFT`, чтобы не уничтожить изменения.
- `status` и `doctor` ничего не меняют; `doctor` различает состояние пакета, обнаружение MCP на диске и непроверенный вызов в Cursor.
- Обновление Git-источников ADT **не** переустанавливает Personal MCP. Его обновляйте отдельно по [инструкции](../personal-mcp/README.ru.md) с резервной копией и новой проверкой `toolkit_info`.
- Для Linux/macOS используйте те же команды `python3`, но проверьте поддерживаемые пути в своей среде.

## Границы безопасности

MCP только читает разрешённые локальные инструкции и не выполняет команды/тесты, не изменяет проект, не запускает ИИ-модель и не публикует релизы. Реальные действия выполняет Cursor по разрешениям пользователя. Отдельные тарифы/лимиты моделей Cursor не входят в бесплатность ADT. Публикация в Marketplace, автоматическая установка MCP, запуск CLI Codex/Claude и платные API не нужны.

[English](README.md) · [Документация Cursor Plugins](https://cursor.com/docs/reference/plugins) · [Agent Skills](https://cursor.com/docs/skills)
