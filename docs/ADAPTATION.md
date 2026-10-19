# Процедура адаптации к новому проекту

Универсальное здесь означает переносимость базовых методов, **не автоматическую применимость каждого правила**.

1. Найдите реальное `AGENTS.md`, `README.md`, CI, пакетный менеджер и конфигурацию тестов. Заполните `profiles/project-profile.example.json` проверенными данными в своём проекте.
2. Подключите минимальный core (`task-scoping`, `implementation`, `qa-strategy`, `code-review`, `research-verification`), остальные - только по задаче.
3. При необходимости подключите конкретные профильные навыки из **оригинального** архива после отдельной проверки языка, лицензии, ссылок, окружения и требований.
4. Никогда не переносите project-specific `AGENTS product app.md`, `AGENTS knowledge base.md`, прописанный `origin/master`, текущий Python runtime или фиксированные CI названия напрямую.
5. Используйте `scripts/install.py` для dry-run и безопасной выборочной установки только универсальных навыков. Он не меняет `AGENTS.md` и существующие навыки.
6. Выполните проверку `python scripts/validate_pack.py`, выборочные сценарии и независимую проверку реальной задачи в целевом репозитории.

| Тип проекта | Рекомендуемый старт | Не предполагать |
|---|---|---|
| Python backend | task-scoping, implementation, qa-strategy | Python версии, pytest, FastAPI, GitHub |
| Frontend/mobile | implementation, qa-strategy, code-review | React, Telegram, браузерные тесты |
| CLI/библиотека | implementation, code-review, documentation-maintenance | production deploy, HTTP, UI |
| Data/ML | research-verification, architecture-decisions, qa-strategy | хранение ПД, LLM API, GPU |
| Документация/контент | research-verification, documentation-maintenance | ветки, релизы и даже наличие исходного кода |

Все project-specific роли, навыки и внешние инструменты устанавливаются отдельно. Для других агентных сред требуется проверка механизма обнаружения `.agents/skills` и инструкций.

## Навыки для Codex и Claude Code одновременно

Для управляемых установок предпочитайте `scripts/skill_manager.py`: выбор
профиля (`catalog --profile qa-python`), dry-run, явный `--apply`, отдельный
`status --layout codex` или `status --layout claude`. Команда `migrate`
копирует проверенные **управляемые** навыки между этими двумя layout без
удаления исходных файлов. Пользовательские и legacy-навыки автоматически
не переносятся и во владение не принимаются.

Точные команды Windows/Linux, модель lockfile и механизм восстановления:
[CLIENT_MIGRATION.md](CLIENT_MIGRATION.md). Установленный файл не подтверждает
фактическое использование навыка конкретным AI-клиентом.
