# Оригинальный Ponytail 5.3.2 - необязательные навыки

[English](en/PONYTAIL_UPSTREAM.md) | [Issue #422](https://github.com/MikeMoore1337/ai-development-toolkit/issues/422) | [Официальный проект](https://github.com/DietrichGebert/ponytail)

## Поставка и проверяемое происхождение

Это **точные, неизменённые** шесть `skills/*/SKILL.md` из `DietrichGebert/ponytail`, тег `v5.3.2`, коммит `16352ac229eb08a9598dcae48fe9f2b342567d86` (тот же SHA уже закреплён в `MANIFEST.json`). Исходные файлы лежат в `third_party/ponytail-v5.3.2/skills/{ponytail,ponytail-review,ponytail-audit,ponytail-debt,ponytail-gain,ponytail-help}/SKILL.md`; авторская MIT-лицензия без изменений - `third_party/ponytail-v5.3.2/LICENSE`. Тест `tests/test_public_distribution.py` проверяет Git blob SHA каждого файла. Ничего не переписывалось под Toolkit.

Upstream `SKILL.md` использует непереносимое поле `argument-hint`: строгий валидатор Agent Skills Toolkit не принимает его без изменений. Поэтому каталог `third_party/` - версионированный **исходный снимок**, а не набор объявленных переносимых навыков Toolkit. Используйте копии в совместимом клиенте; не объявляйте успех L1/L4 без реальной проверки.

Эта копия **не включена** в основные профили Toolkit и не устанавливает официальный плагин с hooks. Это поддерживаемый upstream **skill-only fallback**, а не доказанная установка Ponytail на компьютере или активация в клиенте.

## Подключение без Codex CLI на Windows

1. Убедиться, что в `%USERPROFILE%\.agents\skills\` нет одноимённых навыков. При конфликте сначала выяснить источник и не перезаписывать каталог.
2. Через Проводник Windows скопировать **шесть каталогов** из `third_party/ponytail-v5.3.2/skills/` в `%USERPROFILE%\.agents\skills\` (кроме других каталогов; файл LICENSE остаётся в репозитории). Изменять оригинальные `SKILL.md` не нужно.
3. Перезапустить **Codex Desktop** и проверить, видит ли он навыки `ponytail`, `ponytail-review` и `ponytail-audit`. По необходимости вызвать конкретный навык вручную. До наблюдения в клиенте статус **HOST_NOT_VERIFIED**.
4. Для отката удалить **только эти шесть установленных каталогов**, если они были скопированы именно на шаге 2. Не удалять одноимённые навыки, установленные ранее из другого источника.

Официальный полноценный плагин Ponytail для Codex использует штатный marketplace и два lifecycle hooks - см. upstream [INSTALL.md](https://github.com/DietrichGebert/ponytail/blob/v5.3.2/INSTALL.md). В рамках этого изменения **не** запускались `codex plugin ...`, Codex CLI, Claude CLI, hooks, платные API, внешние процессы или живые модельные вызовы. Нельзя считать ручное копирование шести SKILL.md эквивалентом полного плагина: нет автоматической инъекции правил в каждую сессию и нет гарантированного переключения режимов.

### Предпочтительно: оригинальный нативный плагин Codex Desktop

Toolkit теперь публикует оригинальный Ponytail v5.3.2 (закреплённый SHA `16352ac229eb08a9598dcae48fe9f2b342567d86`) как `AVAILABLE` в **существующем локальном каталоге плагинов** `.agents/plugins/marketplace.json`. Это ссылка на оригинальный GitHub-репозиторий, не форк и не изменённый SKILL.md.

В **Codex Desktop** откройте Plugins, выберите marketplace **AI Development Toolkit (local)**, затем **ponytail** и штатную установку. Проверьте разрешения на lifecycle hooks; не устанавливайте одновременно skill-only копию ниже (избегайте дублирования). Этот шаг требует реального клиента и явного пользовательского подтверждения; **не выполнялся удалённо** и остаётся `HOST_NOT_VERIFIED`. Никакого Codex CLI или платного API не требуется. Если marketplace не обнаруживается клиентом, используйте проверяемый skill-only fallback далее.

## Подключение через Toolkit: Codex Desktop, без Codex CLI

В актуальном каталоге Toolkit на Windows выполните в PowerShell:

- Проверка: `py -3.14 -B scripts/ponytail_codex_skills.py --status`
- Установка: `py -3.14 -B scripts/ponytail_codex_skills.py --install`
- Откат: `py -3.14 -B scripts/ponytail_codex_skills.py --uninstall`

Скрипт использует **только шесть неизменённых SKILL.md** из `third_party/ponytail-v5.3.2/skills`, сверяет их Git blob SHA и помещает в `%USERPROFILE%\.agents\skills` для всех проектов, включая Hermes. Установка не запускает Codex CLI, Claude CLI, hooks, модель, сеть и дополнительный Gateway. Дубли в `%USERPROFILE%\.codex\skills`, симлинки, посторонние файлы и неправильные SHA вызывают отказ без перезаписи. Удаляются только файлы с маркером, созданным этим скриптом.

После установки перезапустите/откройте Codex Desktop и проверьте отображение навыков `ponytail`, `ponytail-review`, `ponytail-audit`, `ponytail-debt`, `ponytail-gain`, `ponytail-help`. По описанию задачи Codex **может** выбрать навык автоматически, но это не гарантируется. Это **skill-only**, без нативных lifecycle hooks и гарантии постоянного режима Full/Lite. До физической проверки Codex Desktop: `HOST_NOT_VERIFIED`.

Запущенный ранее на VPS изолированный Hermes Agent не подключает Ponytail к Codex Desktop или Hermes BRC. Резидентные BRC-сервисы здесь не изменяются.

## Границы

- `AGENTS.md`, запрос пользователя, проектные ограничения, тесты, права, проверка безопасности и правила релиза приоритетнее необязательного навыка.
- `minimal-safe-change` уже реализован внутри Toolkit и не переименовывается/не удаляется. Не подключать его и `ponytail` автоматически одновременно: использовать Ponytail только по явному выбору, чтобы избежать конкурирующих правил.
- Не включать режим `ultra` автоматически. Не выполнять `ponytail-review`/`ponytail-audit` без запроса.
- Для пользователей других клиентов доступны **оригинальные** варианты из upstream INSTALL.md. Персональный запрет владельца на Codex CLI, Claude CLI и дополнительные расходы не является универсальным ограничением Toolkit.
- Изменения source/CI, проверка скопированных файлов, ручная установка на ПК и реальное L4-L6 использование - **разные** уровни доказательств. В этой задаче нет подтверждения последним двум.
