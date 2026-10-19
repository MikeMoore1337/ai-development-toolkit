# Первый запуск AI Development Toolkit

[Русская документация](README.md) | [Главная](../../README.ru.md) | [English quick start](../../README.md)

Это пошаговое руководство для первого знакомства. Вы установите **профиль навыков в пустой учебный проект**, не затрагивая свой рабочий репозиторий.

## Что потребуется

- Git и Python **3.12 или новее**. Python должен вызываться командой `python`; на Windows можно использовать `py -3`.
- Доступ к GitHub для клонирования репозитория.
- Пустая папка учебного проекта. Не выбирайте папку с существующими навыками, пока не изучите правила установки.
- Если хотите реально использовать навыки в работе - отдельно установленный и настроенный Codex или Claude Code. Для копирования и проверки файлов ИИ-клиент не нужен.

Toolkit не устанавливает ИИ-клиента и не предоставляет агенту доступ к файлам, сервисам или публикации.

## Шаг 1. Получите Toolkit

Linux / macOS (терминал):

~~~bash
git clone https://github.com/MikeMoore1337/ai-development-toolkit.git
cd ai-development-toolkit
python --version
~~~

Windows (PowerShell):

~~~powershell
git clone https://github.com/MikeMoore1337/ai-development-toolkit.git
Set-Location ai-development-toolkit
py -3 --version
~~~

Проверьте версию Python. Для повторяемой установки **опубликованной** версии используйте соответствующий тег, а не считайте `main` релизом. Последний опубликованный релиз указан в [README](../../README.ru.md).

## Шаг 2. Посмотрите доступные профили

Linux / macOS:

~~~bash
python scripts/skill_manager.py catalog
~~~

Windows:

~~~powershell
py -3 scripts/skill_manager.py catalog
~~~

Для первой установки подойдёт `general`. Позднее можно выбрать `frontend`, `backend`, `qa-python` или другой профиль. Профиль - заранее подобранный набор навыков, а не отдельная модель ИИ.

## Шаг 3. Создайте отдельный учебный проект

Находясь в каталоге `ai-development-toolkit`, создайте рядом с ним **новую** папку. Не используйте эту команду, если `toolkit-demo` уже существует с важными файлами.

Linux / macOS:

~~~bash
mkdir ../toolkit-demo
~~~

Windows:

~~~powershell
New-Item -ItemType Directory -Path ..\toolkit-demo
~~~

## Шаг 4. Проверьте будущие изменения без записи

Linux / macOS:

~~~bash
python scripts/skill_manager.py install --target ../toolkit-demo --profile general
~~~

Windows:

~~~powershell
py -3 scripts/skill_manager.py install --target ..\toolkit-demo --profile general
~~~

Команда покажет план установки и изменения файлов. **На этом шаге запись не выполняется.** Проверьте путь, выбранный профиль, перечень файлов и отсутствие конфликтов.

## Шаг 5. Установите навыки после проверки

Выполняйте только если предварительный просмотр соответствует вашим ожиданиям.

Linux / macOS:

~~~bash
python scripts/skill_manager.py install --target ../toolkit-demo --profile general --apply
python scripts/skill_manager.py status --target ../toolkit-demo
~~~

Windows:

~~~powershell
py -3 scripts/skill_manager.py install --target ..\toolkit-demo --profile general --apply
py -3 scripts/skill_manager.py status --target ..\toolkit-demo
~~~

По умолчанию применяется схема Codex (`.agents/skills/` внутри учебного проекта). Для Claude Code к командам `install` и `status` добавляют `--layout claude` (каталог `.claude/skills/`). Не смешивайте схемы и не переносите примеры в свой рабочий проект без предварительного просмотра.

## Шаг 6. Проверьте результат и ограничения

1. Убедитесь, что команда `status` завершилась успешно, а в учебной папке появились `SKILL.md` выбранных навыков.
2. Если у вас уже есть ИИ-клиент, отдельно проверьте по его документации, обнаруживает ли он установленные навыки. **Копирование файлов не подтверждает их реальную активацию.**
3. Не считайте наличие навыка разрешением изменять проект, отправлять данные внешним сервисам, объединять PR или публиковать релизы.

Не получилось? См. [руководство по установке и восстановлению](INSTALLATION.md). Менеджер поддерживает безопасный предварительный просмотр операций обновления, удаления и отката, но управляет только файлами, которые он сам установил.

## Что дальше

Откройте [словарь](GLOSSARY.md) и [русский каталог навыков](SKILLS_CATALOG.md), вернитесь к [каталогу руководств](README.md) и выберите профиль под свою задачу. Для повторного использования выбирайте существующий проект только после ознакомления с его локальными инструкциями `AGENTS.md` / `CLAUDE.md`.
