# Updating Toolkit, managed skills, MCP and ChatGPT plugin

[Русская версия](ru/UPDATING.md) · [Installation](INSTALLATION.md) · [Migration](CLIENT_MIGRATION.md)

| Component | Update mechanism |
| --- | --- |
| Toolkit checkout | Review Git status and fetch an approved repository revision |
| Skills managed in a project | Update from the **currently checked-out local Toolkit**, using Skill Manager |
| ChatGPT plugin | Can retrieve approved current instructions when supported; **cannot replace its own installed shell automatically** |
| MCP server | The repository does **not** ship a verified cross-platform Toolkit MCP installer or generic auto-update service |

## 1. Update the checked-out Toolkit deliberately

~~~bash
git status --short
git rev-parse HEAD
git fetch --tags origin
git log --oneline HEAD..origin/main
~~~

Fetching updates Git metadata, not worktree files. Review differences before intentionally moving a clean local main branch with `git pull --ff-only origin main`. If you require a published release rather than development main, use a clean clone and the exact reviewed tag (example: `git switch --detach v5.5.2`); verify tag contents and `MANIFEST.json.version`. Never discard local changes just to update.

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

The current repo provides MCP/tool integration contracts, **not** an installer for a documented Toolkit MCP service. Do not invent `pip`/`npm`/`docker` commands or claim background MCP updates. A concrete MCP implementation needs its own verified install guide, permission scope and version evidence.

## 4. Evidence by environment

Linux and Windows run the general offline CI. Standard GitHub-hosted macOS ARM and Intel runners perform targeted file installation/ownership/rollback checks using Python 3.12. Passing CI does **not** verify a physical Mac, a real Codex/Claude Code runtime or application behavior. GitHub documents [standard hosted runners as free for public repositories](https://docs.github.com/en/actions/reference/runners/github-hosted-runners); this workflow uses no larger or paid runner, AI model, API key or user device.
