# Локальный MCP для Codex (Windows, Linux и macOS)

## Personal MCP 0.1.13 — повторная оценка Model Advisor #401

Для ранее включённого opt-in появился `toolkit_model_review_checkpoint`:
переоценивает значимость независимой проверки после **нового риска,
обнаруженного при изучении файлов или diff**. Аргументы: исходная задача,
до 8 конкретных наблюдений, `stage` и `proactive_model_advice=true`.
Не выполняет файлоопераций, поиска моделей, консультаций или сетевых вызовов.
`REVIEW_CANDIDATE` — эвристический сигнал, а не разрешение на делегирование.
Если перечень нативных моделей неизвестен, Codex должен честно обозначить
неизвестную доступность, но не скрывать важную рекомендацию. Остальные
пользователи остаются opt-out. Обновление MCP отдельно через `-McpOnly`.
См. [руководство #401](../../docs/ru/PROACTIVE_MODEL_ADVISOR.md).

## Personal MCP 0.1.12 — дополнительный opt-in Model Advisor #401

В существующий `toolkit_prepare_task` добавлен необязательный параметр
`proactive_model_advice` (по умолчанию `false`). Только при явном opt-in
возвращается ограниченный источник-риск `model_advisor`. Он не знает каталог
моделей клиента, не меняет основную модель и не запускает субагентов.
Подтверждение пользовательского выбора остаётся в Codex Desktop.
Исполняемый MCP обновляется отдельно от Git-копии через
`Install-ADT-Personal.ps1 -McpOnly` без Codex CLI. После обновления клиента
требуется перезапуск и новая проверка загрузки инструкций. Подробности:
[Proactive Model Advisor](../../docs/ru/PROACTIVE_MODEL_ADVISOR.md).

## Personal MCP 0.1.11 — оркестрация Codex #357 (только чтение)

Исходная версия 0.1.11 добавляет инструменты `toolkit_codex_prepare_delegation` и
`toolkit_codex_review_delegation` к прежним десяти инструментам. Они вызывают
**только локальный контракт** `scripts/codex_host_orchestration.py` из
выделенной копии Toolkit, сверяя его SHA256 с `SHA256SUMS.txt`.
Никаких нативных Codex tools, моделей, платных API, shell-команд или записей
в пользовательские проекты MCP не запускает. Подтверждение стоимости
`zero_incremental_cost_verified=false` блокирует подготовку.

**Обновление только установленного MCP на Windows без Codex CLI и без
повторной регистрации:** в проверенном, обновлённом репозитории Toolkit
запустите `integrations/personal-mcp/adt-personal/Install-ADT-Personal.ps1
-McpOnly` (сначала `-WhatIf`). Установщик использует штатные проверки,
резервное копирование и отказ при нетипичном пути. Убедитесь, что отдельная
выделенная копия источника Toolkit, из которой MCP читает контракт, содержит
новую версию `scripts/codex_host_orchestration.py` и корректный SHA256.
**Обновление исходников не обновляет MCP-программу; MCP 0.1.11 не считается
установленным до нового `toolkit_info` в Codex Desktop.**

Следом проверьте `tools/list` в новой сессии Codex: оба инструмента должны
иметь `readOnlyHint=true`. Без независимых сведений о денежной стоимости и
атомарного host-only lease не выполняйте реальный `spawn_agent`.


Это один из двух **равноправных способов подключения** к AI Development Toolkit наряду с [плагином ChatGPT](../chatgpt-plugin/README.ru.md). MCP предназначен для локального Codex, когда агент имеет разрешённый доступ к рабочему проекту. Локальный MCP не является удалённым подключением ChatGPT.

## Что делает MCP

`toolkit_prepare_task` получает от Codex текст задачи и имена доступных навыков/ролей, подбирает нужные инструкции из Toolkit и возвращает их **в контекст Codex**. Сам MCP не сканирует проект, не создаёт субагентов, не устанавливает навыки в `.agents/skills/` и не переписывает корпоративные файлы. Чтобы установить нативные навыки, отдельно используйте Skill Manager и предварительный просмотр.

## Требования

Codex CLI, Python 3.10+, Git, доступ к публичному GitHub или предварительно разрешённая локальная копия Toolkit, разрешение корпоративной политики. Для Windows доступен проверенный PowerShell-установщик; для Linux и macOS подготовлен отдельный shell-установщик (изолированная проверка в Linux выполнена, проверка в реальном Codex/macOS - отдельно).

Скопируйте `integrations/personal-mcp/adt-personal` **вне рабочего проекта**, затем выполните соответствующие команды.

### Windows (PowerShell)

```powershell
$package = 'C:\path\to\ai-development-toolkit\integrations\personal-mcp\adt-personal'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$package\Install-ADT-Personal.ps1" -Codex
py -3 "$package\diagnose_mcp.py"
```

### Linux (терминал)

```bash
package="$HOME/ai-development-toolkit/integrations/personal-mcp/adt-personal"
sh "$package/Install-ADT-Personal.sh"
python3 "$package/diagnose_mcp.py" \
  --launcher "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/mcp/adt_mcp.py" \
  --source "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/toolkit-source"
```

### macOS (Terminal)

```bash
package="$HOME/ai-development-toolkit/integrations/personal-mcp/adt-personal"
sh "$package/Install-ADT-Personal.sh"
python3 "$package/diagnose_mcp.py" \
  --launcher "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/mcp/adt_mcp.py" \
  --source "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/toolkit-source"
```

Путь `$HOME/ai-development-toolkit` - пример: замените на место **распакованного пакета** или клонированного Toolkit. На Windows `py -3` должен находить установленный Python 3. На macOS установка Codex CLI/Git/Python может зависеть от способа управления программами, используемого организацией.

После установки полностью перезапустите Codex и проверьте `codex mcp get ai-development-toolkit`, затем **реальный вызов** `toolkit_info` и `toolkit_prepare_task` в самом Codex. Только локальная диагностика MCP не доказывает автоматическую активацию.

## Проверка версии и откат выделенной Git-копии

Команда `--preflight` у установленного Personal MCP показывает текущую версию/SHA Toolkit, последнюю известную ревизию и возможность отката, **без сети и изменений**. Для Windows:

```powershell
py -3 "$env:LOCALAPPDATA\ADT-Personal\updater\update_toolkit.py" --preflight
```

Для Linux/macOS используйте установленный `~/.local/share/adt-personal/updater/update_toolkit.py` или `$XDG_DATA_HOME` со своим реальным путём. Сначала `--rollback` показывает только план; `--rollback --apply` явно возвращает выделенную чистую Git-копию к закреплённой прежней ревизии. Рабочий проект и файлы MCP/ChatGPT не меняются. При локальных изменениях, неверном origin или несовпадении сохранённого состояния операция запрещается. Для длительного отката отключите планировщик, иначе он позже снова подтянет `main`. Подробности — в [руководстве по обновлению](../../docs/ru/UPDATING.md).

## Автообновление навыков из GitHub

### Windows

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$package\Enable-ADT-AutoUpdate.ps1"
py -3 "$env:LOCALAPPDATA\ADT-Personal\updater\update_toolkit.py" --status
```

### Linux (systemd пользователя)

```bash
sh "$package/Enable-ADT-AutoUpdate.sh"
python3 "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/updater/update_toolkit.py" \
  --source "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/toolkit-source" \
  --state-dir "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/updater/state" --status
systemctl --user list-timers adt-personal-toolkit-update.timer
```

Linux-вариант использует пользовательский `systemd`; без него установите доступное разрешённое планирование вручную. Таймер запускается, когда доступен пользовательский диспетчер; офлайн-система не может загрузить GitHub.

### macOS (launchd пользователя)

```bash
sh "$package/Enable-ADT-AutoUpdate.sh"
python3 "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/updater/update_toolkit.py" \
  --source "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/toolkit-source" \
  --state-dir "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/updater/state" --status
launchctl print "gui/$(id -u)/com.ai-development-toolkit.personal-updater"
```

Планировщики проверяют `main` ежедневно в 10:35 по местному времени устройства. **Обновляются только навыки, роли и профили** в отдельной локальной копии. Код MCP и пакет ChatGPT обновляются отдельно. При изменении Toolkit перезапускайте Codex. При сбое или корпоративном запрете сетевого доступа проверка покажет `FAIL` - это не доказательство обновления.

## Безопасность рабочего проекта

- Не устанавливайте пакет внутри корпоративного проекта; он размещается в профиле пользователя (`LOCALAPPDATA` на Windows, `~/.local/share/adt-personal` по умолчанию в Linux/macOS).
- Существующие записи MCP в Codex не перезаписываются; проверяйте их перед использованием.
- Изменение локальных исходников проекта и физическая установка навыков **не выполняются автоматически**.
- Внешние навыки являются инструкциями, не разрешениями на действия. Правила организации и проекта имеют приоритет.

[English](README.md) | [Обзор](../../docs/ru/INTEGRATIONS.md)

## Меньше текста при первом запросе (#276)

По умолчанию `toolkit_prepare_task` возвращает тексты **трёх** наиболее приоритетных `SKILL.md` вместо пяти. Полный список `selected_skills` остаётся прежним, отложенные навыки перечисляются в `remaining_skills_to_consult`. При необходимости укажите `max_skills` до восьми или запросите конкретный `toolkit_get_skill`; вспомогательные файлы доступны адресно через `toolkit_get_reference`. Поле `context_load_metrics` измеряет байты фактически переданного текста навыков и ролей, **не** токены модели. Для использования этой логики нужно отдельно обновить установленный MCP; синхронизация только Git-копии её не заменяет.

## Подбор навыков для промптов и SEO

При актуальном источнике Toolkit инструмент `toolkit_prepare_task` может автоматически выбрать профиль `prompt-refinement` для явного запроса «составь хороший промпт для Codex из заметок» и `seo-audit` для «проверь SEO сайта». Запрос «сделай сайт» **нужно выполнять**, а не превращать в промпт для повторной отправки; при создании нового дизайна сохраняется этап визуального согласования.

MCP только читает и передаёт инструкции. Реальное выполнение SEO-аудита или работы над проектом зависит от инструментов и разрешений Codex. Изолированные проверки маршрутизатора не доказывают, что новая версия MCP уже установлена у пользователя и активирована в Codex.

## MCP 0.1.10: установка пары модулей с восстановлением (#190)

В версии исходного MCP `0.1.10` требуется **два файла**:
`mcp/adt_mcp.py` и `mcp/adt_discovery.py` в одном каталоге.
Старый установщик копировал только первый; после обновления импорт
`adt_discovery` мог завершиться ошибкой. Установщики Windows и Linux/macOS
теперь сначала проверяют оба файла во временной папке, делают резервные
копии прежней установки, переносят пару в постоянный пользовательский
каталог и повторно проверяют запуск. При ошибке прежние файлы
восстанавливаются; регистрация MCP не заменяется намеренно.

Ежедневный updater библиотеки навыков **не обновляет** исполняемый MCP.
Используйте отдельно проверенный закреплённый пакет, а не произвольный
`main`. После установки нужны `--check` из постоянного каталога и
фактический вызов инструмента в новом сеансе клиента. Есть синтетический
Linux-тест и статическая проверка PowerShell; реальный Windows/macOS хост,
обновление личного Codex и работа модели **NOT_VERIFIED**. Сторонние
`SKILL.md` не выполняются и не устанавливаются.

## Обновление уже подключённого MCP без Codex CLI (#190)

Если `toolkit_info` показывает `mcp_server_version=0.1.6` при версии
библиотеки Toolkit `5.5.3`, планировщик обновил **только инструкции**.
Новый MCP `0.1.10` нужно поставить отдельно. Для уже установленного в
`%LOCALAPPDATA%\ADT-Personal\mcp\adt_mcp.py` сервера
используйте режим `-McpOnly` установщика из **нового проверенного ZIP**.
Он не вызывает Codex CLI/Claude CLI, не пишет в `config.toml`,
`AGENTS.md` или проект, не регистрирует MCP и не делает `git clone`.
Требуется уже существующий источник `toolkit-source`; сохраните
прежнюю настройку регистрации. Штатные резервные копии и откат при
ошибке относятся только к двум файлам MCP.

1. Скачайте версионированный ZIP из **последнего проверенного GitHub Actions
   artifact** для коммита, содержащего режим `-McpOnly`, в
   [списке запусков Validate toolkit](https://github.com/MikeMoore1337/ai-development-toolkit/actions/workflows/validate.yml)
   (`AI-Development-Toolkit-Personal-MCP-0.1.10.zip`). Не загружайте
   скрипт из произвольной ветки.
2. Проверьте SHA-256 архива по записи CI для **соответствующего SHA**;
   распакуйте за пределами рабочих проектов. Если код установщика
   отличается от документации, проверьте его перед применением.
3. В PowerShell (путь к распакованной папке задайте явно):

   ```powershell
   $package = 'C:\Downloads\ADT-Personal-0.1.10\adt-personal'
   powershell.exe -NoProfile -File "$package\Install-ADT-Personal.ps1" -McpOnly -WhatIf
   powershell.exe -NoProfile -File "$package\Install-ADT-Personal.ps1" -McpOnly
   py -3 "$env:LOCALAPPDATA\ADT-Personal\mcp\adt_mcp.py" --source "$env:LOCALAPPDATA\ADT-Personal\toolkit-source" --check
   ```

   Эти команды **не используют Codex CLI**. На компьютере с политиками
   ограничения PowerShell соблюдайте правила организации; не обходите
   ограничения исполнения сценариев.
4. Полностью закройте и откройте Codex Desktop. В новом диалоге
   реально вызовите `toolkit_info` и `toolkit_prepare_task`; ожидается
   `mcp_server_version=0.1.10`. Результат проверки без вызова в
   установленном клиенте - `NOT_VERIFIED`.

**Важно:** режим `-McpOnly` не переподключает регистрацию на другой
путь. Если ранее MCP зарегистрирован не в стандартном пользовательском
каталоге, **не выполняйте обновление вслепую**: сначала
проинспектируйте разрешённым read-only способом `~/.codex/config.toml`
и сравните используемый путь с указанным выше. Отсутствие
`toolkit_prepare_task` после обновления обычно означает, что Codex
всё ещё запускает старый путь или не был перезапущен.

## Закреплённые релизы исходников (#190)

Инструкция: [публикация архивов по проверенному SHA и безопасный откат](../../docs/ru/INTEGRATION_SOURCE_RELEASES.md). CI-артефакты хранятся 14 дней, GitHub Release assets не устанавливаются автоматически.
