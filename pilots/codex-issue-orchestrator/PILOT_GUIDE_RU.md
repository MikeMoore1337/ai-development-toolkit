# Проверка Codex Issue Orchestrator: изолированный пилот

Проверяем не реальный проект, а **новый временный публичный репозиторий** `MikeMoore1337/adt-orchestrator-pilot` с синтетическим кодом. Скрипт ничего не удаляет и не меняет в существующих репозиториях.

## Подготовка

Проверь в PowerShell, что GitHub CLI авторизован и Toolkit обновлён:

```powershell
gh auth status
Set-Location 'D:\Pet-projects\ai-development-toolkit'
git status --short
git fetch origin main
git merge --ff-only origin/main
py -3.14 .\scripts\issue_orchestrator.py --help
```

Обновляй Toolkit только при чистом рабочем дереве. В справке должен быть параметр `--issues`. Старый `stash` не восстанавливай автоматически.

## 1. Локальная проверка (без записи на GitHub)

Сохрани `setup_codex_issue_pilot.py` в `D:\Pet-projects` и выполни:

```powershell
Set-Location 'D:\Pet-projects'
py -3.14 .\setup_codex_issue_pilot.py --dry-run
```

Ожидается `OFFLINE_PREFLIGHT_PASS`.

## 2. Создание тестового репозитория и трёх Issues

**Внимание:** следующая команда создаст **публичный** репозиторий GitHub, выполнит начальный push и создаст три Issues. Исходники синтетические, секретов в них нет; GitHub опубликует стандартные метаданные Git-коммитов (автора и email из Git config). Если публичность не подходит, не запускай эту команду. Никакие сторонние платные API не используются.

```powershell
py -3.14 .\setup_codex_issue_pilot.py --create `
    --repo MikeMoore1337/adt-orchestrator-pilot `
    --root 'D:\Pet-projects' `
    --toolkit 'D:\Pet-projects\ai-development-toolkit'
```

Скрипт **не перезаписывает** существующие локальные или удалённые репозитории. Если репозиторий уже существует или настройка была частично выполнена, повторное создание остановится и ничего не удалит. Создание всегда выполняется вручную, только по команде `--create`.

После успеха:
- Папка проекта: `D:\Pet-projects\adt-orchestrator-pilot`.
- Промпт для Codex Desktop: `D:\Pet-projects\adt-orchestrator-pilot-CODEX-PROMPT.txt`.
- Отчёт подготовки: `D:\Pet-projects\adt-orchestrator-pilot-MANIFEST.json`.
- GitHub репозиторий: `https://github.com/MikeMoore1337/adt-orchestrator-pilot`.

Созданные Issues связаны последовательно: вторая зависит от первой, третья - от второй. В начальном `plan` **доступна только первая**, а две другие исключены с `OPEN_DEPENDENCY`. Это ожидаемо и проверяется скриптом.

## 3. Запуск настоящего Codex Desktop

1. В приложении Codex выбери проект `D:\Pet-projects\adt-orchestrator-pilot`.
2. Открой содержимое созданного `adt-orchestrator-pilot-CODEX-PROMPT.txt`, скопируй целиком в **один** новый чат Codex.
3. Разрешай только доступ, действительно необходимый для локальной работы и GitHub; не разрешай неопределённые опасные действия.
4. Codex должен последовательно создать три отдельных PR, дождаться CI каждого, слить их и закрыть соответствующие Issues. Параметр `--issues` не позволяет захватить задачи вне пилотного набора.
5. Сохрани отчёт Codex с тремя URL PR, точными SHA, проверками CI и состоянием очереди.

Это тест **одного активного сеанса Codex**, а не фонового исполнителя v2. Если Codex завершит сеанс посреди задачи, состояние сохранится, но самостоятельный перезапуск ещё не реализован.

## 4. Независимая приёмка

В PowerShell:

```powershell
$repo = 'MikeMoore1337/adt-orchestrator-pilot'
$tool = 'D:\Pet-projects\ai-development-toolkit\scripts\issue_orchestrator.py'

# Получить состояние всех тестовых Issues и PR
gh issue list -R $repo --state all --limit 20 --json number,title,state
gh pr list -R $repo --state merged --limit 20 --json number,title,mergedAt,baseRefName,headRefName

# Проверить сохранённое состояние управляющей очереди
py -3.14 $tool status --repo $repo --branch main
py -3.14 $tool plan --repo $repo --branch main
```

Критерий успеха: три Issues `CLOSED`, три разных PR `MERGED` в `main`, CI на точном HEAD каждого PR успешен, `active: null`, сохранённые статусы Issues `DONE`, отсутствует запуск задач вне тестовой очереди.

**Возможные ограничения:** запрос сетевого разрешения от песочницы Codex, неготовность `gh` внутри Codex, лимиты модели, требования GitHub к PR. В этих случаях нужно честно записать BLOCKED и его причину, а не подменять проверку фиктивными результатами.

## 5. Очистка

Тестовый репозиторий специально **не удаляется автоматически**. После приёмки можно самостоятельно архивировать его в GitHub. До завершения QA сохраняй Issues, PR, журнал CI и состояние оркестратора как доказательства.
