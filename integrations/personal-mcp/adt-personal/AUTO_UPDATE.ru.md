# Автоматическое обновление AI Development Toolkit Personal MCP

> **Linux и macOS:** универсальные инструкции находятся в [`integrations/personal-mcp/README.ru.md`](../README.ru.md). Этот внутренний документ сохраняет подробности первоначальной реализации для Windows.


## Назначение

Настраивает ежедневную автоматическую синхронизацию **только локального каталога навыков, ролей и профилей Toolkit**, который читается персональным MCP. **Код MCP не обновляется автоматически**, поскольку он требует отдельной проверки совместимости. Рабочие проекты, настройки Codex, `AGENTS.md` и исходный GitHub-репозиторий не меняются.

- Триггеры: ежедневно в **10:35 по местному времени Windows** и при входе текущего пользователя в систему.
- Если на устройстве нет сети, проверка завершится ошибкой, существующая рабочая ревизия сохранится. Следующая проверка произойдёт при следующем запуске расписания.
- Если в текущие календарные сутки синхронизация прошла успешно, повторный запуск **пропускается**.
- Выполняется с правами текущего пользователя, только когда он вошёл в Windows. Административные права, пароли и платные API не нужны. Политики корпоративного устройства могут запретить регистрацию задач.
- На этапе установки выполняется одна немедленная проверка GitHub, если не указан `-SkipFirstCheck`.

## Установка

Скачать и распаковать архив в `Downloads`, затем в PowerShell:

```powershell
$target = "$HOME\Downloads\ADT-Personal-0.1.7"
$zip = "$HOME\Downloads\AI-Development-Toolkit-Personal-MCP-0.1.7.zip"
Expand-Archive -LiteralPath $zip -DestinationPath $target -Force
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$target\adt-personal\Enable-ADT-AutoUpdate.ps1"
```

Текущий сервер MCP v0.1.7 и его подключение сохраняются. Дальнейшее обновление навыков происходит без скачивания ZIP. Для новых экземпляров MCP/перезапущенного Codex новая ревизия доступна автоматически; уже запущенный процесс MCP может продолжать использовать старый каталог до перезапуска клиента.

## Проверка

```powershell
Get-ScheduledTask -TaskName ADT-Personal-Toolkit-Update | Select-Object TaskName, State
Get-ScheduledTaskInfo -TaskName ADT-Personal-Toolkit-Update | Select-Object LastRunTime, LastTaskResult, NextRunTime
py -3 "$env:LOCALAPPDATA\ADT-Personal\updater\update_toolkit.py" --status
```

Значения `UP_TO_DATE`, `UPDATED` и `SKIPPED_ALREADY_CHECKED_TODAY` показывают успешную синхронизацию/пропуск. `FAIL` показывает причину в `last_error`. Если штатная ежедневная проверка не удалась, можно запустить вручную, **без обхода проверок сохранности**:

```powershell
py -3 "$env:LOCALAPPDATA\ADT-Personal\updater\update_toolkit.py" --force
```

## Безопасность и откат

- `git fetch` используется только для `main` из официального `https://github.com/MikeMoore1337/ai-development-toolkit.git`.
- Допускается только fast-forward. Переписанная история, локальные изменения или добавленные файлы **блокируют обновление**.
- Новая ревизия до применения проверяется без выполнения кода из репозитория: `MANIFEST.json`, все объявленные навыки (`SKILL.md`), роли, профили, безопасность путей и отсутствие символических ссылок.
- Непосредственно перед переключением повторно проверяется чистота локального каталога. Предыдущая рабочая ревизия фиксируется как `refs/adt-personal/previous-good` и в пользовательском `state.json`.
- Если последующая проверка обнаружит сбой и безопасный автоматический откат возможен, предыдущая ревизия восстанавливается. При параллельных изменениях вместо принудительного сброса потребуется ручной разбор.
- Состояние обновлений хранится вне Git-копии: `%LOCALAPPDATA%\ADT-Personal\updater\state\state.json`.

## Отключение

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$target\adt-personal\Enable-ADT-AutoUpdate.ps1" -Disable
```

Или, если папка с ZIP удалена:

```powershell
Unregister-ScheduledTask -TaskName ADT-Personal-Toolkit-Update -Confirm:$false
```

Отключение задания не удаляет локальную копию Toolkit и не отключает MCP. При удалении задачи `-Disable` не требуется повышенных полномочий в обычной пользовательской конфигурации Windows.

## Ограничения проверки

Тесты Linux покрывают Git-переходы, валидацию архива, целостность и обнаружение ошибок. Реальная регистрация Windows Scheduled Task должна быть отдельно подтверждена на пользовательском устройстве. Нельзя считать её успешной лишь потому, что скрипт прошёл статические проверки.
