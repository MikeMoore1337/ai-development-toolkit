<div align="center">

![AI Development Toolkit](assets/branding/hero.png)

**Разрабатывай с ИИ. Выпускай с доказательствами качества.**

Переносимая библиотека навыков, ролей и рабочих процессов для разработки программного обеспечения с ИИ-агентами.

![Agent Skills](https://img.shields.io/badge/Agent_Skills-compatible-253B50?style=flat-square)
![Skills](https://img.shields.io/badge/skills-51-0E7A6B?style=flat-square)
![Roles](https://img.shields.io/badge/roles-16-5162A9?style=flat-square)
![Profiles](https://img.shields.io/badge/profiles-23-0E7A6B?style=flat-square)
[![CI](https://github.com/MikeMoore1337/ai-development-toolkit/actions/workflows/validate.yml/badge.svg)](https://github.com/MikeMoore1337/ai-development-toolkit/actions/workflows/validate.yml)

[English](README.md) · **Русский**

[Быстрый старт](#быстрый-старт) · [Каталог навыков](docs/SKILLS_CATALOG.md) · [Установка](docs/INSTALLATION.md) · [Участие](CONTRIBUTING.md) · [Планы](docs/ROADMAP.md)

</div>

---

## Для чего нужен Toolkit

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
| **QA Engineering Pack** | 27 навыков API/UI/CI, надёжности тестирования и управления качеством | [QA-навыки](docs/SKILLS_CATALOG.md#qa-engineering-pack) |
| **Make Feature** | 1 самостоятельный подключаемый навык работы над функциями | [Интеграция](docs/MAKE_FEATURE_INTEGRATION.md) |
| **Роли** | 5 основных и 11 специализированных ролей QA | [Каталог ролей](docs/SKILLS_CATALOG.md#agent-roles) |
| **Профили** | 23 набора навыков под конкретные задачи | [Все профили](docs/SKILLS_CATALOG.md#profiles) |

Навыки оформлены по формату [Agent Skills](https://agentskills.io/specification). Наличие навыка не даёт агенту автоматически права менять файлы, подключаться к сервисам или выпускать изменения.

## Быстрый старт

**Для локальной валидации нужен Python 3.12+** и существующая папка проекта для установки навыков.

```bash
# После публикации проекта на GitHub
git clone https://github.com/MikeMoore1337/ai-development-toolkit.git
cd ai-development-toolkit

# Посмотреть профили
python scripts/install.py --list-profiles

# Сначала посмотреть план без изменений
python scripts/install.py --target /path/to/project --profile general

# Применить после проверки
python scripts/install.py --target /path/to/project --profile general --apply
```

По умолчанию навыки устанавливаются в `.agents/skills/`. Для Claude Code используй `--layout claude`, для других клиентов - `--skills-dir`. Существующие навыки не перезаписываются, `AGENTS.md` целевого проекта не изменяется.

## Какой профиль выбрать

| Сценарий | Профиль |
| :--- | :--- |
| Реализовать функцию | `codex-feature` |
| Исправить визуальные расхождения | `ui-fix` |
| Проверить анимации | `ui-motion` |
| Спроектировать Python/API-тесты | `qa-python` |
| Разобраться с нестабильным CI | `qa-ci` |
| Проверить готовность к релизу | `qa-release` |
| Отредактировать текст | `editorial` |
| Вести задачу через Make Feature | `make-feature` |

[Полный каталог из 51 навыка и 23 профилей](docs/SKILLS_CATALOG.md)

## Проверка перед использованием

```bash
python -m pip install -r requirements-dev.txt
python scripts/validate_pack.py
python scripts/check_public_package.py
python -m unittest discover -s tests -v
```

Валидация формата и тесты комплекта не заменяют испытаний на реальных проектах. Правила целевого репозитория и разрешения на выпуск имеют приоритет над универсальными инструкциями.

## Документация и участие

[Установка](docs/INSTALLATION.md) · [Каталог навыков](docs/SKILLS_CATALOG.md) · [Методика оценки](docs/QUALITY_RUBRIC.md) · [Политика публикации](docs/PUBLICATION_POLICY.md) · [Дорожная карта](docs/ROADMAP.md) · [Как помочь](CONTRIBUTING.md)

Ядро распространяется по MIT. Отдельные компоненты, включая Make Feature, имеют собственные сведения об авторах и лицензиях. См. [политику публикации](docs/PUBLICATION_POLICY.md). Проект не является официальным дистрибутивом Codex, Claude Code или Agent Skills.
