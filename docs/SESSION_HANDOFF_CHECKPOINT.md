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
