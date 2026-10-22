# Установка AI Development Toolkit - macOS

[English](../INSTALL_MACOS.md) · [Все платформы](INSTALLATION.md) · [Обновление](UPDATING.md)

## Без терминала

Если хотите просто пользоваться инструкциями через ChatGPT, Claude или агент в IDE, локальная установка не обязательна: [начните здесь](BEGINNER_START.md). Одна ссылка не активирует навыки автоматически.

## Подготовка

Нужны Git, Python 3.12+, доступ к GitHub и **уже существующая** папка проекта. ИИ-клиент устанавливается отдельно.

На Apple Silicon и Intel команды одинаковые. `python` и системный `python3` могут не соответствовать требованию 3.12+. Для установки используйте разрешённый пакет Python с python.org либо уже имеющийся Homebrew. Git при необходимости устанавливается отдельно через одобренный способ или Command Line Tools Apple.

## Установка в существующий проект

Из каталога Toolkit. Перед применением проверьте AGENTS.md / CLAUDE.md и чужие навыки в своём проекте:

~~~bash
python3.12 --version
command -v python3.12
git --version
uname -m
git clone https://github.com/MikeMoore1337/ai-development-toolkit.git
cd ai-development-toolkit
project="$HOME/Projects/existing-project"
python3.12 scripts/adt.py profile list
python3.12 scripts/adt.py doctor --target "$project"
python3.12 scripts/skill_manager.py install --target "$project" --layout codex --profile general
# Только после проверки предпросмотра:
python3.12 scripts/skill_manager.py install --target "$project" --layout codex --profile general --apply
python3.12 scripts/skill_manager.py status --target "$project" --layout codex
~~~

Для Claude Code используйте `--layout claude` вместо `--layout codex`. Менеджер отказывается перезаписывать неуправляемые навыки и не изменяет AGENTS.md/CLAUDE.md.

## Обновление и проверка

Обновление исходников Toolkit, обновление управляемых копий навыков, восстановление, плагин ChatGPT и MCP имеют **разные процедуры**. [Пошаговое обновление](UPDATING.md) · [Миграция Codex / Claude Code](CLIENT_MIGRATION.md).

Успешный `status` доказывает только файловое состояние. Реальная активация навыков в Codex/Claude Code и QA приложения проверяются отдельно. Виртуальная машина macOS в CI - не личный Mac.
