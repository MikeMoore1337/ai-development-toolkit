# Безопасная установка навыков

[Русская документация](README.md) | [Начало работы](GETTING_STARTED.md) | [English source](../INSTALLATION.md)

Это перевод [исходного руководства по установке](../INSTALLATION.md). Технические названия, команды и значения флагов оставлены без изменений. О фактически проверенной совместимости клиентов и ограничениях см. [CLIENT_COMPATIBILITY.md (EN)](../CLIENT_COMPATIBILITY.md).

**Новый проект? Начните с Skill Manager v2.** Потребуются Python 3.12+, клонированный Toolkit и существующий каталог целевого проекта. Toolkit **не устанавливает ИИ-клиент**. Посмотрите профили с помощью `python scripts/skill_manager.py catalog` и выберите подходящий:

~~~bash
python scripts/skill_manager.py install --target /path/to/repo --profile qa-core
python scripts/skill_manager.py install --target /path/to/repo --profile qa-core --apply
python scripts/skill_manager.py status --target /path/to/repo
~~~

Первая команда показывает изменения в файлах, **не выполняя запись**. Только `--apply` применяет изменения. Сначала изучите существующие `AGENTS.md`, `CLAUDE.md` и каталоги навыков в целевом проекте: менеджер не переписывает эти файлы автоматически. Для Claude Code последовательно используйте `--layout claude`. Учёт владения файлами и резервные копии Skill Manager распространяются только на его собственные установки.

**Разовое копирование без управляемых обновлений:** сначала запустите `python scripts/install.py --target /path/to/repo --profile qa-core`, затем повторите с `--apply`. Старый установщик по-прежнему поддерживается, не перезаписывает существующие навыки и принимает доверенный путь `--skills-dir PATH`. При этом он **не создаёт** историю владения и отката. Skill Manager не принимает такую установку под управление автоматически.

**Как проверить:** выполните `status` для управляемых навыков, откройте скопированный `SKILL.md`, после чего **отдельно** убедитесь, что установленный и настроенный ИИ-клиент действительно обнаруживает и применяет навык. Копирование файлов, соответствие формату и реальная активация - разные вещи. Роли QA в репозитории - справочные инструкции, они не превращаются в самостоятельно работающих агентов при установке.

**Перед размещением в публичном репозитории:** выполните проверки качества и публикации, изучите `extensions/qa/SOURCE_MAPPING.md`, лицензии и строки, которые могут содержать учётные данные.

## Необязательный подбор профиля без записи

Toolkit умеет предложить профиль по указанной задаче и ограниченному набору известных имён конфигурационных файлов проекта. При этом он **не читает приватный исходный код**, не обращается к сервисам, не устанавливает навыки и не принимает решений о выпуске.

~~~bash
python scripts/recommend_profile.py --target /path/to/repo --task qa
python scripts/recommend_profile.py --target /path/to/repo --task feature
~~~

Поддерживаемые задачи: `feature`, `ui`, `qa`, `ci`, `release`, `docs`, `agent`, `backend`, `frontend`, `research`, `provider`.

Для QA профиль определяется по признакам проекта: Python - `qa-python`, Python и JavaScript - `qa-fullstack`, JavaScript и Playwright - `qa-ui`. Если стек не распознан, используется `qa-core`.

В результате выдаются объяснение выбора, `read_only: true` и отдельные `optional_skills` и `optional_profiles` (они никогда не устанавливаются автоматически). Пять тематических направлений и метрики размера/пересечения описаны в [наборах навыков](CURATED_SKILL_PACKS.md). `python scripts/profile_metrics.py` измеряет объём **байтов файлов**, а не количество токенов модели.

Рекомендация **эвристическая**: обязательно сравните её с правилами своего проекта. Для установки используйте предварительный просмотр Skill Manager и явный `--apply`.

## Skill Manager v2: управляемая установка

Для простого разового копирования остаётся `install.py`. Новый `skill_manager.py` хранит **файл учёта владения** и локальную историю только для тех навыков, которые были установлены самим менеджером. Он не принимает под управление и не перезаписывает чужие навыки и не редактирует `AGENTS.md` / `CLAUDE.md`.

Пример для Windows PowerShell (запускайте из каталога Toolkit):

~~~powershell
$project = "D:\Work\example-project"

# Без --apply команды, способные менять файлы, только показывают план:
py -3 scripts/skill_manager.py install --target $project --profile qa-python
py -3 scripts/skill_manager.py install --target $project --profile qa-python --apply
py -3 scripts/skill_manager.py status --target $project
py -3 scripts/skill_manager.py update --target $project
py -3 scripts/skill_manager.py update --target $project --apply
py -3 scripts/skill_manager.py uninstall --target $project --skills api-testing
py -3 scripts/skill_manager.py uninstall --target $project --skills api-testing --apply
# Откат последней управляемой операции:
py -3 scripts/skill_manager.py rollback --target $project
py -3 scripts/skill_manager.py rollback --target $project --apply
# После прерванной операции сначала просмотрите восстановление:
py -3 scripts/skill_manager.py recover --target $project
py -3 scripts/skill_manager.py recover --target $project --apply
~~~

Для первого клиента менеджер использует файл учёта схемы v1 `.adt/skills-lock.json`. Для второго клиента применяются независимые файлы `.adt/skills-lock-codex.json` или `.adt/skills-lock-claude.json`. Общий `.adt/manager.lock` и снимки операций в `.adt/history/` хранятся **внутри целевого проекта**.

Резервные копии могут включать установленные файлы навыков. При необходимости исключайте `.adt/` из коммитов. Менеджер не меняет `.gitignore` автоматически.

**Защитные механизмы:** управление только своими файлами, контроль локальных изменений содержимого, просмотр без записи, эксклюзивная блокировка процессов, поэтапная замена, восстановление после прерываний, отсутствие скрытых загрузок из сети. Если управляемый навык локально изменён, изменение через менеджер блокируется.

Навыки, ранее установленные `install.py`, не принимаются под управление. Для миграции сначала сохраните резервную копию, изучите содержимое и только после этого устанавливайте управляемые экземпляры в свободные каталоги. **Нельзя удалять пользовательские изменения ради прохождения команды менеджера.**

### Предварительный просмотр изменений по файлам

Любая изменяющая операция в режиме предварительного просмотра выводит `file_diffs`: относительные пути добавляемых, изменяемых и удаляемых файлов, а также SHA256 до и после. Это локальное сравнение байтов: оно не раскрывает содержимое файлов и не отменяет проверку владения. Просмотрите список до `--apply`.

Если повторное обновление ничего не меняет, набор изменений пуст. Если содержимое локального файла не совпадает с сохранённым SHA256, операция прекращается, а не перезаписывает изменения.

### Просмотр профилей и копирование управляемых навыков между клиентами

~~~bash
python scripts/skill_manager.py catalog
python scripts/skill_manager.py catalog --profile qa-python
python scripts/skill_manager.py migrate --target /path/to/repo --from-layout codex --layout claude
python scripts/skill_manager.py migrate --target /path/to/repo --from-layout codex --layout claude --apply
python scripts/skill_manager.py status --target /path/to/repo --layout claude
~~~

`migrate` **копирует**, а не удаляет исходные навыки, только если они принадлежат менеджеру, не изменены и их SHA256 совпадает с исходниками актуального Toolkit. Команда не допускает конфликтов путей, рассинхронизации, старых/неуправляемых каталогов или несовпадающих байтов.

`status`, `update`, `uninstall` и `rollback` используют `--layout` для выбора независимого клиента; `recover` обрабатывает незавершённые операции по обоим клиентам.

Полные сценарии миграции Windows/Linux и ограничения описаны в [CLIENT_MIGRATION.md (EN)](../CLIENT_MIGRATION.md). Копирование файлов само по себе не доказывает обнаружение навыков клиентом, их активацию моделью или полезность.

Для произвольных путей `--skills-dir` продолжайте пользоваться старым `install.py`: Skill Manager не заявляет управление этими каталогами.
