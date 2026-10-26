# AI Development Toolkit для DeepSeek Harness

[English](README.md) | [Обычный DeepSeek Chat](../deepseek-chat/README.ru.md)

Здесь реализован **локальный конфигурационный плагин Cordis Bundle** для DeepSeek Harness. Он подключает **существующий read-only MCP-сервер Toolkit** по stdio. Второй MCP-сервер и платный DeepSeek API не нужны.

## Установка на Linux / macOS

Нужны проверенная локальная копия Toolkit, Python 3.12+, Node.js и DeepSeek Harness (`dsh`). Каталога `$HOME/adt-harness-bundle` ещё не должно быть.

```bash
cd /path/to/ai-development-toolkit
bundle="$HOME/adt-harness-bundle"
python3.12 integrations/deepseek-harness/prepare_bundle.py --output "$bundle"
# Посмотрите план: файловые изменения пока не выполняются.
python3.12 integrations/deepseek-harness/prepare_bundle.py --output "$bundle" --apply
dsh plugin --profile web add "link:$bundle"
dsh --profile web --dump-config
```

## Windows PowerShell

```powershell
cd D:\path\to\ai-development-toolkit
$bundle = Join-Path $env:USERPROFILE "adt-harness-bundle"
py -3.14 integrations/deepseek-harness/prepare_bundle.py --output $bundle
py -3.14 integrations/deepseek-harness/prepare_bundle.py --output $bundle --apply
dsh plugin --profile web add "link:$bundle"
dsh --profile web --dump-config
```

Генератор берёт абсолютный путь к запущенному Python и `scripts/toolkit_mcp.py` из той же копии Toolkit. До `--apply` выполняется только просмотр плана. Генерация не изменяет рабочий проект, профили Harness или исходники Toolkit. **Установка через `dsh plugin` - отдельное явное действие**, которое меняет выбранный профиль Harness. При необходимости перезапустите сеанс и проверьте реальное появление и вызов `mcp__adt__toolkit_catalog` и `mcp__adt__toolkit_read_skill`. Одна запись конфигурации этого не подтверждает.

Исходные `package.json` и `cordis.patch.yml` в репозитории - **отключённый шаблон**. Не устанавливайте его напрямую в расчёте на работающее подключение. Сначала создайте персональный пакет. Храните полученную папку постоянно: установка `link:` ссылается на неё. После переноса Python или Toolkit создайте пакет заново в другом каталоге и явно обновите установленный.

## Нативные навыки Harness

Harness обнаруживает `<git-проект>/.agents/skills/<имя>/SKILL.md` и `<git-проект>/.dsh/skills/<имя>/SKILL.md`. Для согласованной установки в `.agents/skills` используется прежний Skill Manager с размещением Codex; каталог `.dsh/skills` он не обслуживает. Одна ссылка на Toolkit ничего не устанавливает. При одинаковых именах навыков `.dsh/skills` имеет приоритет согласно исходникам Harness. Не дублируйте навыки без необходимости.

## Ограничения и диагностика

- Генератор создаёт рабочий конфигурационный пакет только во внешней **новой папке** с `--apply`, не перезаписывая чужие файлы.
- MCP Toolkit отдаёт инструкции только для чтения; не запускает код, не устанавливает навыки и не меняет проект.
- Подключение MCP в Harness относится к **профилю**, а не автоматически к отдельной рабочей папке. Учитывайте область доступности инструментов.
- При отсутствии `adt-mcp` в `--dump-config` проверьте профиль, путь Python, путь Toolkit и конфликты идентификатора. Удаление: `dsh plugin --profile web remove @local/ai-development-toolkit-harness`, затем при необходимости перезапуск.
- Офлайн-проверки подтвердят контракт и генерацию пакета. Живое обнаружение/применение навыков в Harness - **NOT_TESTED**, сравнительная польза - **NOT_MEASURED**.

Официальная ревизия: [навыки Harness](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/docs/subsystems/skills.md), [шаблон Cordis Bundle](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/preset/agent-preset/skills/cordis-plugin-development/templates/mcp/package.json).
