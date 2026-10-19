# Установка и перенос навыков между ИИ-клиентами (офлайн)

[Русская документация](README.md) | [Установка](INSTALLATION.md) | [Английский оригинал](../CLIENT_MIGRATION.md)

Здесь описана **установка файлов**, а не гарантированное обнаружение навыков клиентом, их активация или полезность. Все команды запускаются из каталога Toolkit. Целевые пути в примерах - **временные демонстрационные папки**: заменять их настоящим проектом допустимо только после изучения правил проекта и пользовательских навыков.

## Матрица поддерживаемых вариантов

| Клиент | Локальная папка навыков проекта | Способ установки | Что действительно подтверждено |
| --- | --- | --- | --- |
| Codex | `.agents/skills/<name>/SKILL.md` | Skill Manager, `--layout codex` | Корректная структура файлов, без проверки реального клиента |
| Claude Code | `.claude/skills/<name>/SKILL.md` | Skill Manager, `--layout claude` | Корректная структура файлов, без проверки реального клиента |
| Пользовательский клиент | Явно указанный доверенный `--skills-dir` | Только прежний `install.py` | Копирование, **без гарантий обнаружения и учёта владения** |
| Hermes Agent | Задокументированные `.agents/skills/` или `.hermes/skills/` | Возможно совпадение с расположением Codex | Совместимость только на уровне документации, **установка и запуск Hermes не проверялись** |

Первоисточники: [Codex](https://developers.openai.com/blog/skills-agents-sdk), [Claude Code](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [Hermes](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md). Перед использованием проверьте установленную версию клиента, доверие к проекту и правила активации. Hermes может изменять доступные для записи внешние навыки через собственный менеджер: общий каталог **не становится автоматически доступным только для чтения**.

## Поддерживаемые сценарии и ограничения

| Сценарий | Поддержка и ограничения |
| --- | --- |
| Новый Python-проект (`qa-python`) | Предпросмотр, применение, состояние, обновление |
| Новый интерфейсный проект (`ui-fix`) | Те же операции для любого из двух поддерживаемых расположений |
| Codex → Claude Code и обратно | `migrate` **копирует** только управляемые и неизменённые навыки, сохраняя оригинал |
| Оба клиента в одном репозитории | Раздельное владение для каждого расположения; независимые проверки состояния, обновления, удаления и отката |
| Между двумя произвольными пользовательскими папками | Не управляется Skill Manager; для новой свободной папки подходит прежний установщик после проверки |
| Старый `install.py` → Skill Manager v2 | **Автоматического принятия под управление нет**: требуются резервная копия, проверка и ручное устранение конфликтов |
| Чужие неуправляемые навыки | **Не переносятся и не принимаются под управление автоматически** |
| Байты установленных файлов отличаются от текущих исходников Toolkit | Перенос **отклоняется**, чтобы предотвратить незаметную смену версии |
| Реальное обнаружение навыков клиентом и использование моделью | **Не проверялось**; тесты файлов не подтверждают это |

Первая установка Manager сохраняет `.adt/skills-lock.json` **схемы v1**, независимо от выбранного расположения. Для второго расположения создаётся собственный v1-файл `.adt/skills-lock-codex.json` или `.adt/skills-lock-claude.json`. Первый файл блокировки не переназначается автоматически.

Оба расположения используют общий `.adt/manager.lock` и `.adt/history/` с восстановлением и откатом последней операции каждого клиента. **Не изменяйте и не удаляйте эти файлы вручную.** При необходимости сохраняйте резервные копии `.adt/` вне публикуемого исходного кода.

## Linux / macOS (bash)

```bash
mkdir -p /tmp/adt-cli-python-demo /tmp/adt-cli-ui-demo
python scripts/skill_manager.py catalog
python scripts/skill_manager.py catalog --profile qa-python
python scripts/recommend_profile.py --target /tmp/adt-cli-python-demo --task qa
python scripts/skill_manager.py install --target /tmp/adt-cli-python-demo --layout codex --profile qa-python
python scripts/skill_manager.py install --target /tmp/adt-cli-python-demo --layout codex --profile qa-python --apply
python scripts/skill_manager.py status --target /tmp/adt-cli-python-demo --layout codex

# Copy the exact installed Toolkit-managed skill set to Claude Code.
python scripts/skill_manager.py migrate --target /tmp/adt-cli-python-demo --from-layout codex --layout claude
python scripts/skill_manager.py migrate --target /tmp/adt-cli-python-demo --from-layout codex --layout claude --apply
python scripts/skill_manager.py status --target /tmp/adt-cli-python-demo --layout claude

# Independent update, safe removal and last-transaction undo.
python scripts/skill_manager.py update --target /tmp/adt-cli-python-demo --layout claude
python scripts/skill_manager.py update --target /tmp/adt-cli-python-demo --layout claude --apply
python scripts/skill_manager.py uninstall --target /tmp/adt-cli-python-demo --layout claude --skills api-testing
python scripts/skill_manager.py uninstall --target /tmp/adt-cli-python-demo --layout claude --skills api-testing --apply
python scripts/skill_manager.py rollback --target /tmp/adt-cli-python-demo --layout claude
python scripts/skill_manager.py rollback --target /tmp/adt-cli-python-demo --layout claude --apply

# Separate frontend project, Claude Code only:
python scripts/skill_manager.py install --target /tmp/adt-cli-ui-demo --layout claude --profile ui-fix
python scripts/skill_manager.py install --target /tmp/adt-cli-ui-demo --layout claude --profile ui-fix --apply
```

## Windows (PowerShell)

```powershell
$project = Join-Path $env:TEMP "adt-cli-python-demo"
New-Item -ItemType Directory -Force -Path $project | Out-Null
py -3 scripts/skill_manager.py catalog --profile qa-python
py -3 scripts/skill_manager.py install --target $project --layout codex --profile qa-python
py -3 scripts/skill_manager.py install --target $project --layout codex --profile qa-python --apply
py -3 scripts/skill_manager.py migrate --target $project --from-layout codex --layout claude
py -3 scripts/skill_manager.py migrate --target $project --from-layout codex --layout claude --apply
py -3 scripts/skill_manager.py status --target $project --layout codex
py -3 scripts/skill_manager.py status --target $project --layout claude
py -3 scripts/skill_manager.py update --target $project --layout claude
py -3 scripts/skill_manager.py recover --target $project
# Run this only if an interrupted transaction is reported:
py -3 scripts/skill_manager.py recover --target $project --apply
```

Для переноса в обратном направлении используйте `--from-layout claude --layout codex`; исходные навыки при этом не удаляются. Перенос в уже занятую папку намеренно завершается отказом.

Для пользовательских клиентов используйте `python scripts/install.py --target PATH --skills SKILL --skills-dir ABSOLUTE_DIRECTORY` (сначала просмотр без записи, затем `--apply`). Это простое копирование без учёта владения; команда `migrate` его не обслуживает.

## Предпросмотр, конфликты и восстановление

- **Никогда не выполняйте `--apply` без просмотра плана**: `changes` показывает каталоги навыков, а `file_diffs` - изменяемые пути и SHA256, но не содержимое приватных файлов.
- Существующая неуправляемая папка, символическая ссылка, junction, локально изменённый исходный управляемый навык либо повреждённый файл владения приводят к отказу. `AGENTS.md` и `CLAUDE.md` не изменяются.
- `status` сообщает состояние каждого расположения отдельно. `update` и `uninstall` по умолчанию работают без записи; `rollback` откатывает последнюю операцию **только указанного клиента** и не затрагивает другой.
- Если операция прервана, сначала изучите `recover --target PATH`, затем при необходимости явно запустите `recover --target PATH --apply`. Восстановление анализирует незавершённые операции **обоих** клиентов и может отказаться продолжать при неоднозначных локальных изменениях.
- Не используйте реальный ИИ-клиент или его внутренние команды управления навыками для этих файловых проверок. Навыки, установленные через `install.py`, **не считаются управляемыми Manager**. Сначала создайте резервную копию и сравните вручную: менеджер откажется перезаписывать конфликтующие каталоги.
- Копирование не означает, что модель обнаружила, загрузила, использовала навык или получила от него пользу. Испытания реального клиента ограничены отдельной [Issue #11](https://github.com/MikeMoore1337/ai-development-toolkit/issues/11).
