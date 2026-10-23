<div align="center">

[![AI Development Toolkit: навыки, роли, разработка, тестирование и решение человека](docs/visuals/hero-evidence.svg)](docs/ru/BEGINNER_START.md)

[English](README.md) · **Русский**

[![CI](https://github.com/MikeMoore1337/ai-development-toolkit/actions/workflows/validate.yml/badge.svg)](https://github.com/MikeMoore1337/ai-development-toolkit/actions/workflows/validate.yml) · [Последний релиз](https://github.com/MikeMoore1337/ai-development-toolkit/releases/latest) · [Каталог навыков](docs/ru/SKILLS_CATALOG.md)

**[Начать без терминала](docs/ru/BEGINNER_START.md)** · **[Использовать в своём проекте](AGENT_START.ru.md)** · **[Локальная установка](#быстрый-старт)** · **[Документация](#документация-и-участие)**

</div>

**Интеграции Toolkit:** [плагин ChatGPT](integrations/chatgpt-plugin/README.ru.md) · [MCP для Codex](integrations/personal-mcp/README.ru.md) · [инструкции Windows, Linux и macOS](docs/ru/INTEGRATIONS.md).

## Начните с задачи

AI Development Toolkit - **переносимая библиотека навыков, специализированных ролей и QA-процессов** для разработки с ИИ. Это не отдельный ИИ-агент, не хостинг и не разрешение на доступ к вашему проекту.

| Что нужно сделать | Куда перейти | Что получите |
| :--- | :--- | :--- |
| **Обсудить идею без терминала** | [Путь новичка](docs/ru/BEGINNER_START.md) | Пять готовых запросов и реальные ограничения клиентов |
| **Поработать с уже открытым проектом** | [Дать агенту ссылку на Toolkit](AGENT_START.ru.md) | Инструкции по задаче без обязательной установки Toolkit |
| **Управлять локальными навыками** | [Безопасная установка](docs/ru/INSTALLATION.md) | Выбор профиля, предпросмотр, подтверждение записи, проверка и откат |

Если ИИ-агент **имеет доступ к вашему проекту**, можно написать:

```text
Используй https://github.com/MikeMoore1337/ai-development-toolkit
для выполнения задачи в текущем проекте. Сначала изучи проект,
выбери только нужные навыки, выполни работу и сообщи, что реально проверено.
```

Toolkit служит **источником инструкций, а не местом хранения чужого кода, журналов или отчётов**. Изменять проект агент может только при наличии инструментов и разрешений. Одна ссылка не гарантирует активацию навыков или выполнение команд.

## Как это работает на практике

Это **примеры маршрутов, а не заявления о проведённых испытаниях**.

| Исходный запрос | Маршрут | Условие готовности |
| :--- | :--- | :--- |
| «Создай необычный сайт фитнес-клуба» | [UX/UI Design Orchestra](docs/ru/UX_UI_DESIGN.md): концепции, критика, настоящие эскизы | Владелец согласует визуальный вариант **до** изменения интерфейса |
| «Найди причину падения API-теста» | [QA Engineering Pack](docs/ru/CURATED_SKILL_PACKS.md): воспроизведение, диагностика, правка | Результаты тестов и список изменённых файлов |
| «Помоги подготовить выпуск» | [Контроль качества релиза](docs/ru/RELEASE_PROCESS.md): риски, прослеживаемость и доказательства | Решение о публикации принимает человек |

## Что входит?

**Навыки** для Frontend, Backend, Fullstack, QA, безопасности, сопровождения и UX/UI; **специализированные роли**; **профили** под конкретные задачи и клиенты. Актуальное количество см. в [каталоге](docs/ru/SKILLS_CATALOG.md) - цифры больше не встраиваются в рекламные изображения. [Матрица совместимости](docs/ru/CLIENT_COMPATIBILITY.md) разделяет заявленные возможности и реальные проверки.

[Тематические наборы навыков](docs/ru/CURATED_SKILL_PACKS.md) · [Оценка навыков](docs/ru/SKILL_EVALS.md) · [Make Feature](docs/ru/MAKE_FEATURE_INTEGRATION.md) · [Clear Voice](docs/ru/CLEAR_VOICE_INTEGRATION.md)

<details>
<summary>Состав каталога (количества проверяются в CI)</summary>

[![Skills](https://img.shields.io/badge/skills-82-0E7A6B?style=flat-square)](docs/SKILLS_CATALOG.md)
[![Roles](https://img.shields.io/badge/roles-16-5162A9?style=flat-square)](docs/SKILLS_CATALOG.md)
[![Profiles](https://img.shields.io/badge/profiles-45-0E7A6B?style=flat-square)](docs/SKILLS_CATALOG.md)

| Раздел | Количество |
| :--- | ---: |
| **Core skills** | 24 |
| **Frontend / Backend / Fullstack** | 14 |
| **QA Engineering Pack** | 27 |

</details>

## Локальный MCP для ИИ-агентов

[Установить Toolkit MCP на Windows, Linux или macOS](docs/ru/MCP_INSTALL.md) - подключение к Codex / Claude Code, поиск навыков без записи и настройка только после подтверждения. Плагин ChatGPT устанавливается отдельно.

## Установка по операционным системам

[Windows](docs/ru/INSTALL_WINDOWS.md) · [Linux](docs/ru/INSTALL_LINUX.md) · [macOS (Apple Silicon / Intel)](docs/ru/INSTALL_MACOS.md) · [Безопасные обновления](docs/ru/UPDATING.md)

Менеджер навыков общий, различаются вызов Python и команды оболочки. macOS проверяется на виртуальных runner CI, не на личном Mac и не с настоящим ИИ-клиентом.

## Быстрый старт

**Локальная установка не обязательна.** Для командного способа нужны Python 3.12+, папка проекта и отдельно установленный ИИ-клиент. Если хотите только сформулировать задачу, начните с [варианта без терминала](docs/ru/BEGINNER_START.md).

**Последний опубликованный релиз:** [v5.5.3](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.3) (22 октября 2026 года). SHA тега `14b96569528ab9544c0d28aa1a00343496066445`; `MANIFEST.json.version = 5.5.3`. Исторические расхождения v5.5.0/v5.5.1 описаны в [CHANGELOG.md](CHANGELOG.md). В `main` могут появляться ещё не опубликованные изменения.


Для новой установки рекомендуется **Skill Manager v2**: предпросмотр, учёт установленных им файлов, безопасное обновление и восстановление.

```bash
# 1. Клонировать существующий репозиторий
git clone https://github.com/MikeMoore1337/ai-development-toolkit.git
cd ai-development-toolkit

# 2. Посмотреть профили без установки
python scripts/skill_manager.py catalog

# 3. Предпросмотр без записи файлов
python scripts/skill_manager.py install --target /path/to/project --profile general

# 4. Установить после проверки изменений
python scripts/skill_manager.py install --target /path/to/project --profile general --apply

# 5. Проверить состояние
python scripts/skill_manager.py status --target /path/to/project
```

Для Codex используется `.agents/skills/`, для Claude Code - `.claude/skills/` (добавь `--layout claude` к командам установки и проверки). Чужие навыки и `AGENTS.md` / `CLAUDE.md` не перезаписываются. Установка файлов не подтверждает их обнаружение или использование моделью. Подробнее об [установке, обновлении и откате](docs/ru/INSTALLATION.md), а также о простом одноразовом `install.py`.

## Какой профиль выбрать

| Задача | Профиль | Подробнее |
| :--- | :--- | :--- |
| Реализовать существующую функцию | `codex-feature` | [Маршрут разработки](docs/ru/END_TO_END_WORKFLOW.md) |
| Фронтенд, сервер или интеграция | `frontend` / `backend` / `fullstack` | [Инженерные навыки](docs/ru/UNIVERSAL_ENGINEERING.md) |
| Спроектировать или улучшить интерфейс | `ui-orchestra` | [UX/UI Design](docs/ru/UX_UI_DESIGN.md) |
| Тесты, нестабильный CI, релиз | `qa-python` / `qa-ci` / `qa-release` | [QA-навыки](docs/ru/CURATED_SKILL_PACKS.md) |
| Безопасность, доступность и инциденты | Профиль под задачу | [Полный каталог](docs/ru/SKILLS_CATALOG.md) |

См. [все навыки и профили](docs/ru/SKILLS_CATALOG.md) и [миграцию между клиентами](docs/ru/CLIENT_MIGRATION.md). Профиль не выдаёт разрешений и не доказывает, что клиент активировал навыки.

## Проверка перед использованием

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_pack.py
python scripts/check_public_package.py
python -m unittest discover -s tests -v
```

В обязательном CI на Ubuntu/Python 3.12 также работает официальный
[валидатор Agent Skills](docs/AGENT_SKILLS_SPEC.md): все навыки из актуального MANIFEST.json
из реестра, включая QA и Make Feature. Локальный запуск в изолированном
виртуальном окружении:

```bash
python -m pip install "git+https://github.com/agentskills/agentskills.git@69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref"
python scripts/validate_with_skills_ref.py --scope all
```

Установка производится из закреплённого коммита официального GitHub-репозитория,
а не из одноимённого стороннего пакета PyPI. Структурная валидация не доказывает
безопасность исполнения или эффективность навыков на реальных моделях.
Правила целевого репозитория и разрешения на выпуск остаются обязательными.

## Документация и участие

[Все русские материалы](docs/ru/README.md) · [Первый запуск](docs/ru/GETTING_STARTED.md) · [Словарь терминов](docs/ru/GLOSSARY.md) · [Установка](docs/ru/INSTALLATION.md) · [Каталог](docs/ru/SKILLS_CATALOG.md) · [Проверка первого запуска](docs/ru/ACCEPTANCE.md) · [Маршрут новичка](docs/ru/BEGINNER_WORKFLOW.md) · [Совместимость клиентов](docs/ru/CLIENT_COMPATIBILITY.md)

[Make Feature](docs/ru/MAKE_FEATURE_INTEGRATION.md) · [Clear Voice](docs/ru/CLEAR_VOICE_INTEGRATION.md) · [Актуальность переводов](docs/ru/LANGUAGE_POLICY.md) · [Качество навыков](docs/ru/SKILL_QUALITY_V2.md) · [Универсальная разработка](docs/ru/UNIVERSAL_ENGINEERING.md) · [Agent Skills](docs/ru/AGENT_SKILLS_SPEC.md) · [Порядок релиза](docs/ru/RELEASE_PROCESS.md)

[Методика оценки (EN)](docs/QUALITY_RUBRIC.md) · [Политика публикации](docs/ru/PUBLICATION_POLICY.md) · [Дорожная карта (EN)](docs/ROADMAP.md) · [Участие в проекте](CONTRIBUTING.ru.md)

Ядро распространяется по MIT. Отдельные компоненты, включая Make Feature, имеют собственные сведения об авторах и лицензиях. См. [политику публикации](docs/PUBLICATION_POLICY.md). Проект не является официальным дистрибутивом Codex, Claude Code или Agent Skills.

**Права на распространение:** см. [аудит происхождения (EN)](docs/PROVENANCE_AUDIT.md) и [реестр](provenance/skills.json). Владелец сообщил о разрешении ID1337 для текущих файлов Make Feature, QA Pack и графики. Их SHA256 закреплены в реестре, но независимая юридическая проверка **не заявляется**. Для нового релиза требуется отдельное согласование владельцем конкретного архива. Успешный CI не подтверждает права на публикацию.
