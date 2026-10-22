# Установка AI Development Toolkit - Windows

[English](../INSTALL_WINDOWS.md) · [Все платформы](INSTALLATION.md) · [Обновление](UPDATING.md)

## Без терминала

Если хотите просто пользоваться инструкциями через ChatGPT, Claude или агент в IDE, локальная установка не обязательна: [начните здесь](BEGINNER_START.md). Одна ссылка не активирует навыки автоматически.

## Подготовка

Нужны Git, Python 3.12+, доступ к GitHub и **уже существующая** папка проекта. ИИ-клиент устанавливается отдельно.

Установите Python 3.12+ и Git разрешённым способом. `py -3.12` требует установленной 3.12; для 3.13/3.14 замените номер. Для Toolkit не нужны права администратора.

## Установка в существующий проект

Из каталога Toolkit. Перед применением проверьте AGENTS.md / CLAUDE.md и чужие навыки в своём проекте:

~~~powershell
py -3.12 --version
git --version
git clone https://github.com/MikeMoore1337/ai-development-toolkit.git
Set-Location ai-development-toolkit
$project = Join-Path $HOME "Projects\existing-project"
py -3.12 scripts/adt.py profile list
py -3.12 scripts/adt.py doctor --target $project
py -3.12 scripts/skill_manager.py install --target $project --layout codex --profile general
# Только после проверки предпросмотра:
py -3.12 scripts/skill_manager.py install --target $project --layout codex --profile general --apply
py -3.12 scripts/skill_manager.py status --target $project --layout codex
~~~

Для Claude Code используйте `--layout claude` вместо `--layout codex`. Менеджер отказывается перезаписывать неуправляемые навыки и не изменяет AGENTS.md/CLAUDE.md.

## Обновление и проверка

Обновление исходников Toolkit, обновление управляемых копий навыков, восстановление, плагин ChatGPT и MCP имеют **разные процедуры**. [Пошаговое обновление](UPDATING.md) · [Миграция Codex / Claude Code](CLIENT_MIGRATION.md).

Успешный `status` доказывает только файловое состояние. Реальная активация навыков в Codex/Claude Code и QA приложения проверяются отдельно. Виртуальная машина macOS в CI - не личный Mac.
