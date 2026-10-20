# Бизнес- и системный анализ: от PRD к проверяемым требованиям

[English source](../BUSINESS_SYSTEM_ANALYSIS.md) | [Product Discovery](PRODUCT_DISCOVERY.md) | [Delivery Management](PROJECT_DELIVERY_MANAGEMENT.md) | [Каталог](SKILLS_CATALOG.md)

**Product Discovery** определяет, что и зачем создавать. **Delivery Management** составляет план, отслеживает зависимости и реальные доказательства готовности. **Business & System Analysis** уточняет, какое поведение, правила, сценарии, предметная область и ограничения нужны для разработки, сохраняя исходные R-ID и AC-ID. QA отвечает за реализованные тесты и результаты выполнения. Это не новый контроллер, не BPMN-движок и не независимая система QA-трассировки.

## Начало без терминала

В клиенте, умеющем читать Toolkit, напишите:

> Используй https://github.com/MikeMoore1337/ai-development-toolkit. Помоги описать системные требования и бизнес-правила для небольшого приложения учёта расходов. Сделай короткую спецификацию, помечай допущения и неизвестные условия, сохрани критерии приёмки. Не создавай файлы.

Для начала не нужны PRD, ссылка на собственный репозиторий, установка, API-ключи или платные сервисы. Если клиент не читает GitHub, предоставьте ему текст SKILL.md. Это не является доказательством автоматической активации навыка.

Для профессионального формата предоставьте PRD и при наличии план разработки. Попросите анализ заинтересованных сторон, бизнес-правила BR, сценарии UC, системные требования SR, измеримые NFR, текстовые процессы, границы предметной области, потребности интеграций с явными CONTRACT_PENDING, журнал решений, трассировку R->SR->AC и передачу в UX/UI, Backend, Frontend, QA. [Навык](../../extensions/analysis/skills/business-system-analysis/SKILL.md), [контракт](../../extensions/analysis/skills/business-system-analysis/references/SYSTEM_SPEC_CONTRACT.json), [синтетический пример](../../extensions/analysis/skills/business-system-analysis/references/EXAMPLE_EXPENSES.json) и [негативные случаи](../../extensions/analysis/skills/business-system-analysis/references/MANUAL_ACCEPTANCE.md) помогают проверить результат.

Бизнес-правило получает CONFIRMED только при наличии источника. Иначе ASSUMPTION или UNRESOLVED. Если точный API неизвестен - CONTRACT_PENDING. Неопределённая производительность - UNKNOWN, а не выдуманный SLA. Спецификация описывает ожидаемое поведение, а не готовое ПО; текстовая схема процесса не становится проверенной BPMN 2.0.

## Связи и открытые вопросы

Исходное R1 может порождать несколько SR с неизменным parent R1 и исходными AC. В матрице видны QA-проверки со статусами NOT_WRITTEN, NOT_RUN или PASS - их нельзя смешивать. При противоречиях сохраняются оба источника до решения владельца. Решения с пометкой PROPOSED нельзя выдавать за APPROVED.

## Необязательная установка

Действующий Skill Manager показывает предварительный состав без записи; только явное --apply изменяет выбранную папку проекта:

    python scripts/skill_manager.py catalog --profile business-system-analysis
    python scripts/skill_manager.py install --target /path/to/project --profile business-system-analysis
    python scripts/skill_manager.py install --target /path/to/project --profile business-system-analysis --apply

Для разрешённого JSON вне Toolkit:

    python scripts/validate_system_spec.py /path/to/spec.json

Проверяются структура, ID, связи, статусы и простые структурированные противоречия, но не истинность заявлений, реальные API, результаты внешних тестов или активация в ИИ-клиентах. **По умолчанию результат возвращается в чате.** Копии Toolkit остаются только для чтения при работе с чужим проектом. Отчёты и временные файлы нельзя записывать в Toolkit, а в проект пользователя - без его разрешения.

Дальше в Issue #56 UX/UI передаются акторы, пути, состояния, ошибки и проверяемые условия взаимодействия. Разработка и QA получают отдельные соответствующие части.
