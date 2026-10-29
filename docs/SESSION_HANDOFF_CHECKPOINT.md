# Session continuity - explicit Git checkpoint (#374)

Selected upstream inspiration: https://github.com/iamneilroberts/claude-session-handoff
Pin: `2d7f7018b80ecffe6f8ee9fa466cf01f0694fdad`; MIT, copyright 2026 Neil Roberts.

This is a **manual Git-state handoff**, not an installation of Claude Code hooks, transcript collection, context auto-injection, or self-starting assistant. The original automatic monitor relies on Claude Code, jq, hooks, byte/turn estimates and raw-session context. No client integration is enabled or claimed by this source release. No third-party code is copied.

## Why

The existing Toolkit task/issue and orchestration contracts record decisions and acceptance; they do not provide a small, local, fail-closed guard proving that the next session is working in the same repository, branch, commit and worktree state. This optional utility adds precisely that missing check, without new canonical memory.

## Explicit usage / Явное использование

```sh
python scripts/session_handoff_checkpoint.py capture --repo . --issue https://github.com/OWNER/REPO/issues/123 --file ./handoff-local.json
python scripts/session_handoff_checkpoint.py verify --repo . --file ./handoff-local.json
python -m unittest discover -s tests -p test_session_handoff_checkpoint.py -v
```

The output file is created *only* by explicit capture; overwrite is refused and file mode is 0600 on POSIX. Keep it outside Git (or delete it after use). The repository filesystem path appears only as a local SHA-256 identifier, not as text; no raw prompts, command arguments, diffs, filenames, secrets or original session history are included. Status hash includes tracked-file state, but intentionally does not inspect untracked files. When commit/branch/status changes, verification returns `STALE`, never an invented resume success.

**Important:** This does not capture or restore reasoning, task context, actual work done, GUI state, nor untracked files. For those, link the authoritative GitHub Issue/PR, explicit decisions and verified evidence in the fresh session. A checkpoint is not an authorization token. No paid API, Codex CLI, personal vault or production access.

## RU

Пользователь явно создаёт контрольную точку и передаёт в новую сессию ссылку на Issue. Проверка совпадения Git-состояния предотвращает некорректное продолжение на другой ветке или SHA. Автоматического восстановления переписки нет.

## EN

Explicit opt-in capture/verify of Git metadata prevents silent cross-project or stale-ref continuation. No raw transcripts, hooks, auto-resume, or client activation.


## Toolkit Native Observability / Git snapshot (#434, EN)

The existing Toolkit Project MCP now offers the opt-in read-only \`toolkit_observe_project\` tool. Pass exactly \`project\` (an existing **absolute Git repository root**, not a parent or nested folder) and \`client\` (\`codex\`, \`claude-code\`, or \`hermes\`). The tool reuses the local #374 Git checkpoint reader and returns only: SHA-256 identifier for local repo path, branch, Git HEAD SHA, SHA-256 of **tracked** status, tracked dirty flag and count of declared Git worktrees. No names/paths of changed files or worktrees, original transcripts, prompts, account tokens, task content, process list, UI windows, session history or model calls are captured.

Unlike the original ECC session inspector, this is not a runtime session adapter. \`session_adapter=NOT_CONNECTED\`, \`session_active=NOT_OBSERVED\`, \`L4/L5=NOT_VERIFIED\`, \`L6=NOT_MEASURED\`, and \`authorization=NOT_GRANTED\` are intentionally fixed. A legitimate Git status change is measured; it does **not** imply an AI agent worked, nor that a model/tool/hook is available. Project MCP must already be explicitly installed and called in the client; this source code does not establish Codex Desktop access. No new MCP service, external ECC runtime, background observer, paid API, daemon or network is used.

For an offline self-test, use \`python -m unittest tests.test_toolkit_mcp tests.test_session_handoff_checkpoint -v\`. The new tool is read-only; uninstalling Toolkit Project MCP or reverting its Git revision restores the prior surface. Git is expected in the user's existing project environment. Git commands set \`GIT_OPTIONAL_LOCKS=0\` to avoid index refresh writes; this is still a local Git inspection, not a filesystem sandbox.

## Нативная диагностика Toolkit / снимок Git (#434, RU)

Существующий Project MCP предоставляет добровольный инструмент \`toolkit_observe_project\`. Его аргументы - строго \`project\` (абсолютный путь к **корню Git-репозитория**) и \`client\` (\`codex\`, \`claude-code\`, \`hermes\`). Используется уже реализованное чтение контрольной точки Git #374. Ответ содержит только идентификатор локального репозитория в виде SHA-256, ветку, коммит, SHA-256 статуса **отслеживаемых** файлов, признак изменений и количество Git worktree. Имена файлов, локальные пути, историю переписки, содержимое задач, секреты, процессы ОС и сведения об окнах клиента не собирает.

Это **не** полноценный адаптер живой сессии ECC. Значения \`session_adapter=NOT_CONNECTED\`, \`session_active=NOT_OBSERVED\`, \`L4/L5=NOT_VERIFIED\`, \`L6=NOT_MEASURED\` и \`authorization=NOT_GRANTED\` не меняются на положительные по одному Git-снимку. Изменение Git означает изменение исходников, а не доказанный запуск агента. Клиент должен отдельно и добровольно подключить штатный Toolkit MCP; данный PR не подтверждает наличие доступа к Codex Desktop и не включает скрытый фон, демоны, ECC, платные вызовы или сеть.

Проверка: \`python -m unittest tests.test_toolkit_mcp tests.test_session_handoff_checkpoint -v\`. Откат - отключить Project MCP либо вернуть предыдущую Git-ревизию. Команды Git запускаются локально с \`GIT_OPTIONAL_LOCKS=0\`, но это не замена изоляции ОС.
