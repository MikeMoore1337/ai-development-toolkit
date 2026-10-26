# Updating Toolkit, managed skills, MCP and ChatGPT plugin

[Русская версия](ru/UPDATING.md) · [Installation](INSTALLATION.md) · [Migration](CLIENT_MIGRATION.md)

| Component | Update mechanism |
| --- | --- |
| Toolkit checkout | Review Git status and fetch an approved repository revision |
| Skills managed in a project | Update from the **currently checked-out local Toolkit**, using Skill Manager |
| ChatGPT plugin | Can retrieve approved current instructions when supported; **cannot replace its own installed shell automatically** |
| Local Toolkit MCP | Ships a Python stdio server and project-scoped Codex/Claude Code installer; source code updates only after explicit reviewed Git action, no background updater |

## 1. Update the checked-out Toolkit deliberately

~~~bash
git status --short
git rev-parse HEAD
git fetch --tags origin
git log --oneline HEAD..origin/main
~~~

Fetching updates Git metadata, not worktree files. Review differences before intentionally moving a clean local main branch with `git pull --ff-only origin main`. If you require a published release rather than development main, use a clean clone and the exact reviewed tag (example: `git switch --detach v5.5.4`); verify tag contents and `MANIFEST.json.version`. Never discard local changes just to update.

## Dedicated Personal MCP reference-checkout preflight and rollback

The optional **Personal MCP reference-source updater** is separate from a general developer checkout and from the installed MCP adapter or ChatGPT plugin. Run it only against the dedicated copy created by the Personal MCP installer.

~~~bash
# Offline, no network and no file changes:
python3 integrations/personal-mcp/adt-personal/updater/update_toolkit.py --preflight
# Saved last known Git information only:
python3 integrations/personal-mcp/adt-personal/updater/update_toolkit.py --status
# Explicitly preview an eligible previous-good Git revision:
python3 integrations/personal-mcp/adt-personal/updater/update_toolkit.py --rollback
# Only after checking the exact revisions, allow changes to that dedicated checkout:
python3 integrations/personal-mcp/adt-personal/updater/update_toolkit.py --rollback --apply
~~~

When using source code directly instead of an installed updater, supply the **actual** dedicated `--source` and `--state-dir` paths; defaults refer to the installed Personal MCP layout. Windows can use `py -3`; use a verified Python 3.12+ interpreter for repository tooling.

`--preflight` verifies a clean checkout, expected Git origin, current Toolkit version, last *known* (not necessarily current remote) revision/version, and availability of a previously pinned commit. **It never fetches GitHub**. An unrecorded version is `NOT_VERIFIED`; installed MCP binary, ChatGPT plugin version and client runtime compatibility are independently `NOT_VERIFIED` / `NOT_TESTED`. The official Git remote, commit hashes and SHA256 checks are source-integrity signals, **not cryptographic signatures or a guarantee that source code is safe**. The updater rejects linked/reparse source and state paths, disables repository Git hooks, and treats malformed state as a fail-closed condition.

Unattended refresh permits only fast-forward and rejects a manifest version downgrade. It fetches the expected origin into a private Git ref rather than using shared `FETCH_HEAD`; the configured origin must contain exactly one expected URL. A persistent OS-held lock serializes updater and rollback mutations; its file may remain after a process exit and is not itself proof that another run is active. A durable pending journal allows a clean interrupted update or explicit rollback to be reconciled; ambiguous or damaged state blocks further mutation.

Rollback is a separate user-requested operation on a clean, pinned reference checkout: preview by default, `--apply` required to change files, and no writes to the working project. Local changes, origin mismatch, source-state divergence, missing previous-good ref and a concurrent updater block rollback. The rollback journal also reconciles a clean interruption after `reset --hard`; a dirty or ambiguous checkout remains manual-review-only. Disable automatic source refresh before rollback if an older revision must remain pinned; the next scheduled update can otherwise fast-forward again. The installed MCP adapter and ChatGPT plugin **never** update through these commands.

## 2. Preview project skill changes before applying

Use the **reviewed checkout** and an existing target folder. The examples use Python 3.12, replace the invocation only when a newer Python is verified.

~~~bash
python3.12 scripts/skill_manager.py status --target /path/to/project --layout codex
python3.12 scripts/skill_manager.py update --target /path/to/project --layout codex
# Review file_diffs, ownership and SHA256 first.
python3.12 scripts/skill_manager.py update --target /path/to/project --layout codex --apply
python3.12 scripts/skill_manager.py status --target /path/to/project --layout codex
python3.12 scripts/skill_manager.py rollback --target /path/to/project --layout codex
~~~

On Windows PowerShell, substitute `py -3.12` and a quoted Windows target. On macOS, verify `python3.12 --version` rather than assuming `python3` is new enough. For Claude Code consistently use `--layout claude`. Rollback writes only with an explicit `--apply` and restores the last eligible managed transaction. Interrupted operations require `recover --target PROJECT` preview before any `--apply`. Legacy `install.py` copies are not automatically adopted, and unmanaged skills are preserved. Review backups and lockfiles under `PROJECT/.adt/`.

## 3. Different installation boundaries

The ChatGPT plugin's `MANIFEST.json.chatgpt_personal_live` contract may allow verified live reading of Toolkit instructions. Updating the installed plugin package/shell remains a separate action in Plugin Creator. This is account-level, not an OS executable update.

The repository includes a [local MCP installer](MCP_INSTALL.md) for Codex and Claude Code. It uses absolute paths into a trusted checkout, updated only by a deliberate reviewed Git action followed by a client reconnect. This is **not** unattended auto-updating or remote HTTP MCP. Do not invent `pip`/`npm`/`docker` commands or claim background MCP updates. A concrete MCP implementation needs its own verified install guide, permission scope and version evidence.

## 4. Evidence by environment

Linux and Windows run the general offline CI. Standard GitHub-hosted macOS ARM and Intel runners perform targeted file installation/ownership/rollback checks using Python 3.12. Passing CI does **not** verify a physical Mac, a real Codex/Claude Code runtime or application behavior. GitHub documents [standard hosted runners as free for public repositories](https://docs.github.com/en/actions/reference/runners/github-hosted-runners); this workflow uses no larger or paid runner, AI model, API key or user device.
