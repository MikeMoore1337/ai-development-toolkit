<div align="center">

![AI Development Toolkit](assets/branding/hero.png)

**Разрабатывай с ИИ. Выпускай с доказательствами качества.**

Переносимая библиотека навыков, ролей и рабочих процессов для разработки программного обеспечения с ИИ-агентами.

![Agent Skills](https://img.shields.io/badge/Agent_Skills-compatible-253B50?style=flat-square)
![Skills](https://img.shields.io/badge/skills-73-0E7A6B?style=flat-square)
![Roles](https://img.shields.io/badge/roles-16-5162A9?style=flat-square)
![Profiles](https://img.shields.io/badge/profiles-36-0E7A6B?style=flat-square)
[![CI](https://github.com/MikeMoore1337/ai-development-toolkit/actions/workflows/validate.yml/badge.svg)](https://github.com/MikeMoore1337/ai-development-toolkit/actions/workflows/validate.yml)

[English](README.md) · **Русский**

[Toolkit по ссылке - без установки](AGENT_START.ru.md) · [Начать без терминала](docs/ru/BEGINNER_START.md) · [Путь от идеи до результата](docs/ru/BEGINNER_WORKFLOW.md) · [Clear Voice - руководство](docs/ru/CLEAR_VOICE_INTEGRATION.md) · [Make Feature - руководство](docs/ru/MAKE_FEATURE_INTEGRATION.md) · [Спецификация Agent Skills](docs/ru/AGENT_SKILLS_SPEC.md) · [Порядок релиза](docs/ru/RELEASE_PROCESS.md) · [Качество навыков v2](docs/ru/SKILL_QUALITY_V2.md) · [Полнота переводов](docs/ru/LANGUAGE_POLICY.md) · [Первый запуск с нуля](docs/ru/GETTING_STARTED.md) · [Проверка первого запуска](docs/ru/ACCEPTANCE.md) · [Русская документация](docs/ru/README.md) · [Словарь](docs/ru/GLOSSARY.md) · [Бизнес- и системный анализ](docs/ru/BUSINESS_SYSTEM_ANALYSIS.md) · [Проектирование UX/UI](docs/ru/UX_UI_DESIGN.md) · [Каталог навыков](docs/ru/SKILLS_CATALOG.md) · [Установка и восстановление](docs/ru/INSTALLATION.md) · [Планы (EN)](docs/ROADMAP.md)

</div>

---

## Для чего нужен Toolkit

**Ваш проект уже открыт в IDE с Codex?** Напишите просто: «Используй https://github.com/MikeMoore1337/ai-development-toolkit, чтобы выполнить задачу в текущем проекте». [Toolkit служит источником навыков](AGENT_START.ru.md), **не местом хранения пользовательских файлов и отчётов**. Код, тесты и запрошенные отчёты относятся к проекту пользователя или другому выбранному месту, но никогда к репозиторию Toolkit. Установка Toolkit в проект не обязательна.

**Впервые знакомишься с проектом или не хочешь использовать терминал?** Открой [«Начните без терминала»](docs/ru/BEGINNER_START.md): выбери клиента, скопируй один из пяти запросов и пойми, что ИИ реально сможет сделать. Python и Git для обсуждения идеи не нужны. Если требуется установить навыки в локальный проект, используй [технический первый запуск](docs/ru/GETTING_STARTED.md) с предварительным просмотром и проверкой. [Все русские материалы](docs/ru/README.md).

Задача не просто в том, чтобы агент быстрее написал код. Нужно понять требования, не затронуть лишнее, проверить реальные сценарии и отличать успешное выполнение теста от корректной работы функции.

| Задача | Что предлагает Toolkit |
| :--- | :--- |
| **Разработка без лишних изменений** | Анализ требований, архитектурных решений и границ задачи |
| **Осмысленные проверки** | Проектирование тестов, test oracle, анализ CI и контроль выпуска |
| **Последовательный UI** | Проверка дизайн-системы, скриншотов и анимаций |
| **Качественный текст** | Clear Voice для ясной документации и сообщений интерфейса |
| **Доставка функций** | Make Feature 0.3.0 или feature-delivery, но не оба одновременно |
| **Бережная установка** | Выбор профиля, предварительный просмотр и запрет перезаписи |

## Что входит

| Раздел | Состав | Подробнее |
| :--- | :--- | :--- |
| **Core** | 23 навыка разработки, проверки, безопасности, UI и работы с текстом | [Основные навыки](docs/SKILLS_CATALOG.md#core-skills) |
| **Frontend / Backend / Fullstack** | 14 новых универсальных навыков проектирования и реализации | [Инженерные навыки RU](docs/ru/UNIVERSAL_ENGINEERING.md) |
| **QA Engineering Pack** | 27 навыков API/UI/CI, надёжности тестирования и управления качеством | [QA-навыки](docs/SKILLS_CATALOG.md#qa-engineering-pack) |
| **Make Feature** | 1 самостоятельный подключаемый навык работы над функциями | [Интеграция](docs/MAKE_FEATURE_INTEGRATION.md) |
| **Роли** | 5 основных и 11 специализированных ролей QA | [Каталог ролей](docs/SKILLS_CATALOG.md#agent-roles) |
| **Профили** | 35 наборов навыков под конкретные задачи | [Все профили](docs/SKILLS_CATALOG.md#profiles) |

Навыки оформлены по формату [Agent Skills](https://agentskills.io/specification). Наличие навыка не даёт агенту автоматически права менять файлы, подключаться к сервисам или выпускать изменения.

## Быстрый старт

**Что понадобится:** Python 3.12+, папка своего проекта и отдельно установленный ИИ-клиент. Toolkit предоставляет инструкции для агента, а не самого агента. Выбери профиль под задачу - не нужно разбирать все навыки.

**Версии:** последний опубликованный релиз - [v5.4.0](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.4.0). В `main` есть **ещё не выпущенные** изменения; см. [историю изменений](CHANGELOG.md). Для воспроизводимой установки конкретного релиза переключись на его тег.

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

| Сценарий | Профиль |
| :--- | :--- |
| Реализовать функцию | `codex-feature` |
| Разработать интерфейс | `frontend` |
| Разработать серверный сервис | `backend` |
| Интегрировать UI и API | `fullstack` |
| Исправить визуальные расхождения | `ui-fix` |
| Проверить анимации | `ui-motion` |
| Спроектировать Python/API-тесты | `qa-python` |
| Разобраться с нестабильным CI | `qa-ci` |
| Проверить готовность к релизу | `qa-release` |
| Отредактировать текст | `editorial` |
| Вести задачу через Make Feature | `make-feature` |

[Полный каталог из 72 навыков и 35 профилей](docs/ru/SKILLS_CATALOG.md). Для независимых управляемых установок Codex и Claude Code см. [миграцию и восстановление (EN)](docs/CLIENT_MIGRATION.md) и команду `python scripts/skill_manager.py catalog`.

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

[Первый запуск](docs/ru/GETTING_STARTED.md) · [Словарь терминов](docs/ru/GLOSSARY.md) · [Установка](docs/ru/INSTALLATION.md) · [Каталог](docs/ru/SKILLS_CATALOG.md) · [Методика оценки (EN)](docs/QUALITY_RUBRIC.md) · [Политика публикации](docs/ru/PUBLICATION_POLICY.md) · [Дорожная карта (EN)](docs/ROADMAP.md) · [Участие (EN)](CONTRIBUTING.md)

Ядро распространяется по MIT. Отдельные компоненты, включая Make Feature, имеют собственные сведения об авторах и лицензиях. См. [политику публикации](docs/PUBLICATION_POLICY.md). Проект не является официальным дистрибутивом Codex, Claude Code или Agent Skills.

**Права на распространение:** см. [аудит происхождения (EN)](docs/PROVENANCE_AUDIT.md) и [реестр](provenance/skills.json). Владелец сообщил о разрешении ID1337 для текущих файлов Make Feature, QA Pack и графики. Их SHA256 закреплены в реестре, но независимая юридическая проверка **не заявляется**. Для нового релиза требуется отдельное согласование владельцем конкретного архива. Успешный CI не подтверждает права на публикацию.
