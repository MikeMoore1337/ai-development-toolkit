# Оригинальный Harness² - необязательная установка

Подключаем **неизменённый** [google-research/harness2](https://github.com/google-research/harness2), закреплённый на `1cfe254e8d25b15f37048c3730134686abe60335` (пакет `0.1.0`, Apache-2.0). Код Propose–Probe–Compose, агентные исполнители и подсистемы тестирования **не копируются** в Toolkit и не переписываются.

## Установка и проверка

Нужны **Linux** или **Ubuntu в WSL2** на Windows, `python3.12`, Git, доступ к GitHub/PyPI, непривилегированная учётная запись. Основной Python 3.14 и зависимости Toolkit не изменяются.

```bash
# Явное разрешение на скачивание и установку оригинального внешнего кода.
bash integrations/harness2/install.sh install
bash integrations/harness2/install.sh status
```

Путь установки: `~/.local/share/ai-development-toolkit/harness2-1cfe254e8d25b15f37048c3730134686abe60335/`. Исходники upstream закрепляются точным SHA. Скрипт не запускает `harness2-demo`, модели, тестовые задания, Codex CLI или Claude CLI. Ничего не записывает в другие проекты, конфигурацию Codex Desktop или Toolkit MCP.

## Штатный режим работы

После установки используются **оригинальные CLI**, без самописного движка или обёртки для самой оптимизации:

```bash
source="$HOME/.local/share/ai-development-toolkit/harness2-1cfe254e8d25b15f37048c3730134686abe60335/source"
bin="$HOME/.local/share/ai-development-toolkit/harness2-1cfe254e8d25b15f37048c3730134686abe60335/.venv/bin"
cd "$source"
"$bin/harness2-setup" lab --dry-run
# Только после отдельного разрешения на зависимости, сеть и модельные расходы:
# "$bin/harness2-setup" lab
# "$bin/harness2-check" --bench lab
# "$bin/harness2" --bench lab --k 1 --mode parallel --only-domains antitrust-competition --max-tasks 1
# "$bin/harness2-judge" --bench lab --k 1 --mode parallel
# "$bin/harness2-report" --bench lab --k 1 --mode parallel
```

Закомментированные команды не получают разрешение только вследствие установки. Upstream поддерживает JobBench, LAB и WorkBuddy-Bench, OpenCode и Codex CLI. **Codex Desktop не является подтверждённым штатным исполнителем Harness².** Upstream Codex запускается без песочницы. Модельные испытания требуют соответствующего доступа к провайдерам и могут быть платными.

**Для владельца:** нулевые дополнительные расходы, запрет Codex/Claude CLI, запрет платных API. Эта установка не разрешает модельные вызовы. Для других пользователей допустимость собственного native-маршрута определяется индивидуальной политикой, отдельным согласием и реальной изоляцией среды.

```bash
bash integrations/harness2/install.sh status
bash integrations/harness2/install.sh remove --confirm
```

Удаляется только точно закреплённая установка после проверки SHA, origin и маркера. При прерванной установке необходимо вручную проверить неполную папку перед её удалением.

## Проверки и ограничения

`status` проверяет установленный оригинал, SHA, origin, наличие официального CLI и версию Python-пакета. **Установка ≠ реальный запуск модели и ≠ доказанный прирост качества**. Полноценные задания запускаются только по правилам [официальной установки](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/SETUP.md) и [экспериментов](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/EXPERIMENTS.md). Данные бенчмарков и зависимости имеют отдельные лицензии. Git SHA подтверждает идентификатор исходника, а не криптографическую подпись издателя.

Это отдельный необязательный инструмент разработчика, а не новый Skill Manager, агентный движок или автоматически подключаемый MCP.
