# Спецификация Agent Skills и проверка официальным CLI

[English source](../AGENT_SKILLS_SPEC.md) | [Установка](INSTALLATION.md) | [Языковая политика](LANGUAGE_POLICY.md)

**Авторитетные источники:**

- [Спецификация Agent Skills](https://agentskills.io/specification).
- [Исходный код официального эталонного валидатора](https://github.com/agentskills/agentskills/tree/main/skills-ref).
- [Закреплённый upstream commit](https://github.com/agentskills/agentskills/commit/69ef37e9424c0a7ea9dd2293b559e43ec8176379).
- Версия исходников на этом commit: `0.1.0`, требуется Python **3.11+**.

## Структурный контракт

У каждого навыка есть `SKILL.md` с YAML frontmatter. Обязательные поля:

- `name` — совпадает с именем каталога, строчные буквенно-цифровые символы Unicode и дефисы; не допускаются дефисы в начале/конце и два подряд; не более **64 символов**.
- `description` — непустая строка длиной не более **1024 символов**.

Необязательные поля верхнего уровня: `license`, `compatibility` (не более 500 символов), `metadata`, `allowed-tools`. Точные правила разбора устанавливает **закреплённая версия официального upstream-валидатора**, не описание на этой странице.

## Локальная проверка

Используйте официальный проект GitHub. Одноимённый пакет `skills-ref` в PyPI **не принадлежит** сопровождающим upstream-реализации; см. [обсуждение #355](https://github.com/agentskills/agentskills/issues/355).

Создайте одноразовую виртуальную среду Python и устанавливайте эталонную версию непосредственно из закреплённого GitHub commit. Не запускайте неподтверждённые `install.sh` и сторонние скрипты.

```bash
python -m venv .venv
# POSIX: source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -r requirements-dev.txt
python -m pip install "git+https://github.com/agentskills/agentskills.git@69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref"
skills-ref --version
python scripts/validate_pack.py
python scripts/validate_with_skills_ref.py --scope all
python -m unittest discover -s tests -p integration_skills_ref.py -v
```

`--scope all` охватывает **все навыки из текущего `MANIFEST.json`** (82 в проверенной ревизии: 24 Core, 27 QA, 1 Make Feature, 5 Frontend, 6 Backend, 3 Fullstack, 1 Product, 1 Management, 1 Analysis, 1 Design, 2 AI, 1 SEO, 1 Reliability, 1 Performance, 1 Security, 1 DevOps и 1 Accessibility и 3 Operations и 1 Data Engineering). Это снимок состава, **не исторический результат** выполнения всех проверок. Runner сопоставляет манифест и каталоги, отклоняет отсутствующие и лишние записи и требует явного успешного ответа эталонного CLI для каждого навыка. Отсутствующий исполняемый файл, ненулевой код, неожиданный/пустой вывод, ошибка subprocess или таймаут отдельного навыка — **FAIL**. `--scope core` подходит лишь для локальной диагностики и **не заменяет обязательный CI gate**.

`python scripts/validate_pack.py` остаётся обязательным: проверяет состав Toolkit, пути, локальные ссылки и согласованность. `skills-ref validate` проверяет upstream-формат frontmatter и каталогов.

В GitHub Actions официальный закреплённый CLI устанавливается и выполняется **только** в уже существующей обязательной матрице `tests` для Ubuntu/Python 3.12; другие обязательные задания выполняют собственные межплатформенные проверки.

Upstream README характеризует реализацию как демонстрационную, а **не инструмент production-безопасности**. Ни один валидатор не доказывает безопасность вспомогательных скриптов, действительность лицензии, обнаружение или активацию навыка ИИ-клиентом, корректное поведение модели и улучшение результата. Модель и AI API в этих проверках **не используются**.
