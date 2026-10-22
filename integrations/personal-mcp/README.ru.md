# Дополнительный вариант: локальный MCP для Codex (Windows, Linux, macOS)

**Основной вариант для чат-бота:** [ChatGPT-плагин](../chatgpt-plugin/README.ru.md). Этот MCP предназначен для **локального Codex**, где агент уже имеет разрешённый доступ к рабочему проекту. Локальный MCP не является удалённым подключением ChatGPT.

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
