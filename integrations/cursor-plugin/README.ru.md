# ADT для Cursor - нативный плагин и существующий Personal MCP

**Статус:** исходники плагина и проверяемый локальный установщик. Реальную загрузку и применение в Cursor нужно подтвердить в запущенном клиенте отдельно. Публикация в Cursor Marketplace не выполняется автоматически.

## Как Cursor использует полные навыки без лишней нагрузки

Плагин содержит четыре **коротких навыка-маршрутизатора**, а не копию всего каталога. Cursor узнаёт о них по полю description, сам решает, когда активировать навык, а короткое правило adt-routing.mdc предлагает использовать ADT для содержательных задач разработки, тестирования, безопасности или UI даже без явного слова ADT. Это инструкция агенту, **не гарантия** его поведения.

**Экономный порядок работы:**
1. Установить один целевой проект и его правила. Не сканировать все доступные репозитории. При неоднозначности спросить один раз, какой проект анализировать.
2. На этапе подготовки, если ADT действительно нужен, обратиться к Personal MCP с toolkit_prepare_task и max_skills=1. Этот вызов может уже вернуть полный SKILL.md; повторно читать его не требуется. Каталог и toolkit_info не нужны при каждом запросе.
3. Только при новой потребности дочитать другой навык через toolkit_get_skill и конкретную справку через toolkit_get_reference. Если ответ обрезан, получить недостающие части до заявления о полном чтении.
4. При существенном переходе (например, анализ -> реализация -> регрессия) вызвать toolkit_prepare_stage с max_skills=1 и реально подтверждёнными хешами ранее прочитанных **полных** навыков в consulted_skills. Не повторять тот же этап и не считать исчезнувший контекст сохранённым.
5. В отчёте различать выбор и чтение навыка, фактические вызовы Cursor, выполнение тестов и результат. MCP остаётся READ_ONLY.

**Когда не вызывать ADT:** простой вопрос, мелкая самостоятельная правка, прямой запрет пользователя, выбор оригинального стороннего инструмента в качестве контроллера. Не включать дополнительных моделей, платных API, автоматические сканирования и фоновые проверки.

**Как проверить в Cursor:** откройте проект и в обычном чате Agent, без упоминания ADT, попросите: «Проанализируй тестовые фикстуры FastAPI и предложи точечный план регрессии, без изменений». В истории инструментов должны быть реально видны вызовы ADT. На следующем этапе («Теперь напиши выбранные тесты») проверьте вызов toolkit_prepare_stage. Отсутствие вызова означает, что автоматическая маршрутизация имеет статус **NOT_VERIFIED**, а не PASS. Ни исходный код правила, ни тесты пакета не подтверждают уменьшение расхода лимитов Cursor: это требует отдельного сравнения живых сессий.

## Что входит

- `.cursor-plugin/plugin.json`, `mcp.json`: формат Cursor Plugin с подключением **уже установленного** ADT Personal MCP в режиме stdio/READ_ONLY.
- `skills/`: четыре нативных Agent Skills (разработка, QA, безопасность, UX/UI).
- `rules/`: краткое правило автоматического подбора ADT для содержательных задач без обязательного упоминания ADT; без самостоятельного исполнения и конкурирующих контроллеров.
- `commands/`: команды `/adt-build`, `/adt-qa`, `/adt-security`, `/adt-ui`.
- `scripts/manage.py`: проверка, установка, обновление и безопасный откат локального пакета.
- `scripts/launch_mcp.py`: использует существующие файлы ADT Personal MCP и его отдельный Git-источник, ничего не загружает и не устанавливает.

## Если manage.py не найден

Это **устаревшая локальная копия Toolkit**, а не ошибка версии Python. Сначала проверьте git status --short --branch и наличие integrations/cursor-plugin/scripts/manage.py. **Не запускайте git reset --hard или git pull поверх несохранённых правок.** Безопаснее сохранить старую рабочую папку и создать новую рядом с ней.

Находясь в корне старого Toolkit, выполните в PowerShell:

    Set-Location ..
    git clone --depth 1 --branch main https://github.com/MikeMoore1337/ai-development-toolkit.git ai-development-toolkit-cursor
    Set-Location .\ai-development-toolkit-cursor
    Test-Path .\integrations\cursor-plugin\scripts\manage.py

Последняя команда должна вернуть True. Если папка ai-development-toolkit-cursor уже существует, не клонируйте поверх неё: проверьте её git status. Обновлять разрешённую чистую выделенную копию можно через git pull --ff-only.

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

В **Cursor → Customize** убедитесь, что четыре навыка, правила, команды и MCP обнаружены. Для отдельной диагностики в Cursor Agent вызовите `toolkit_info` и `toolkit_prepare_task`, затем при необходимости `toolkit_get_skill`. При обычной задаче автоматический вызов `toolkit_info` не требуется. Отдельно проверьте реальное использование методики на небольшой задаче. Успешный `doctor` проверяет локальные файлы, **не** обнаружение Cursor.

**Важно:** не регистрируйте один MCP дважды. Если ADT уже есть в глобальном `~/.cursor/mcp.json`, используйте режим `--reuse-global-mcp` ниже; текущую запись ADT удалять не нужно.

### Если ADT MCP уже подключён в Cursor

Если в ~/.cursor/mcp.json уже зарегистрирован сервер ai-development-toolkit, **не создавайте второй экземпляр MCP**. Подключите нативные компоненты плагина через существующий сервер:

    python integrations/cursor-plugin/scripts/manage.py install --reuse-global-mcp
    python integrations/cursor-plugin/scripts/manage.py install --reuse-global-mcp --apply
    python integrations/cursor-plugin/scripts/manage.py doctor

Флаг --reuse-global-mcp требует совместимую существующую локальную регистрацию. Установленный плагин не содержит второго mcp.json; глобальная запись не изменяется. Без флага установщик проверяет конфликт и останавливается. Если MCP в Cursor ещё нет, используйте обычные команды выше.

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
