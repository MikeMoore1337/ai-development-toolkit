# Local Toolkit MCP for Codex and Claude Code

[Русский](ru/MCP_INSTALL.md) · [Installation](INSTALLATION.md) · [Updates](UPDATING.md) · [Choose an integration](INTEGRATIONS.md)

## Features and boundaries

Toolkit includes a real **stdio MCP server** (`scripts/toolkit_mcp.py`) built with Python 3.12+ standard library, no paid APIs or model requests. Its eight tools provide skill catalog/search/reading, specialist and QA role listing/reading, advisory task routing, Skill Manager installation preview, and managed skill status. Roles are guidance documents, **not** automatically started autonomous agents.

**All MCP tools are read-only.** They do not install skills or alter a user's project. When an agent needs to add skills, it can show a preview and ask the operator to use Skill Manager with explicit `--apply`. The separate installer below writes only a project-scoped MCP configuration **after the user executes --apply**. Neither process automatically installs an AI client.

## Before you start

1. Install Codex or Claude Code separately. Choose [Desktop, CLI, IDE or cloud instructions](INSTALLATION.md) first. MCP is not an AI client.
2. Open a terminal **in the cloned Toolkit root**. Python 3.12+ is required; `py -3.12` and `python3.12` below are examples. Replace **all** commands with your actual 3.12+ interpreter (for example `py -3.14` or `python3.14`).
3. Replace example project paths with **existing directories**. The installer does not create projects.
4. Choose `--client codex` or `--client claude`. Review the plan **without `--apply`** before authorizing a write.

## Desktop and CLI use the same project installer

- **Codex Desktop:** select the local project, use `--client codex` below, restart Desktop and verify its actual MCP tools. A separately installed Codex CLI is **not required** by this project installer.
- **Codex CLI:** use the same `--client codex` commands, start `codex` from the target project and inspect `/mcp`.
- **Claude Code Desktop:** select the local project in the **Code tab**, use `--client claude`, start a new session and review the project MCP approval.
- **Claude Code CLI:** use the same `--client claude` commands, start `claude` from the target project and inspect `/mcp`.

The installer writes `.codex/config.toml` or `.mcp.json` in that project; it does not invoke either client CLI. In IDE/WSL/SSH/container sessions the interpreter and absolute Toolkit paths must exist in the actual execution host. The command templates below do not set up a cloud host or ordinary Claude/ChatGPT chat.

**Project MCP verification:** request `toolkit_catalog`, then `toolkit_read_skill` for `qa-strategy`, inside the chosen client. `toolkit_info` and `toolkit_prepare_task` belong to the separate [Personal MCP](ONE_COMMAND_SETUP.md); they are not Project MCP tools. Do not install both scopes under the same registration name without resolving the conflict.

## Windows PowerShell

**Two different paths are required:** `$toolkit` is the checkout of **AI Development Toolkit** (the folder containing `scripts\toolkit_mcp.py`); `$project` is the **existing project where you want Codex to use Toolkit**, for example `your-fitness-coach`. Point `$project` to the Toolkit repository only when you intentionally want MCP inside Toolkit itself. The installer configures that project, not all Codex workspaces.

**1. Check Python first.** Run `py --list-paths` and `py -3 --version` in PowerShell. The selected Python must be **3.12 or newer**. `py -3.12` works only if that exact version is installed; `py -3` selects the available Python 3 runtime. If `py` is unavailable, check `python --version` and use `python` instead of `py -3` in the examples below, provided the version is 3.12+. Otherwise install Python from [python.org](https://www.python.org/downloads/windows/), reopen PowerShell and repeat the check. A `No suitable Python runtime found` message means the installer **has not started**.

**2. Set the paths and validate them.** The examples below use Windows folders; replace both with your actual paths. You may run this block from **any** PowerShell directory because the installer script is referenced by its absolute path.

~~~powershell
$toolkit = 'D:\Pet-projects\ai-development-toolkit'
$project = 'D:\Pet-projects\your-fitness-coach'
$script = Join-Path $toolkit 'scripts\toolkit_mcp.py'
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) { throw 'Toolkit not found: check $toolkit' }
if (-not (Test-Path -LiteralPath $project -PathType Container)) { throw 'Project not found: check $project' }
py -3 -c "import sys; assert sys.version_info >= (3, 12), 'Python 3.12+ required'; print(sys.version)"
~~~

**3. Preview the changes (read-only).** In the **same PowerShell session**, run:

~~~powershell
py -3 $script install --client codex --project $project
~~~

Review the target folder, MCP registration name and exact proposed changes. A preview is not an installation.

**4. Apply only if the preview is correct.**

~~~powershell
py -3 $script install --client codex --project $project --apply
~~~

This writes the project-scoped `.codex/config.toml` while preserving unrelated configuration.

**5. Validate the configuration.**

~~~powershell
py -3 $script doctor --client codex --project $project
~~~

Then restart **Codex Desktop** with the chosen project open and request `toolkit_catalog` followed by `toolkit_read_skill` for `qa-strategy`. The `doctor` result verifies configuration, not live client discovery. The project-scoped installer does **not** require Codex CLI. If you open a new terminal between steps, repeat step 2 to restore the variables.

If you want Toolkit available across **all** your Codex projects instead of configuring each one separately, see [Personal MCP](ONE_COMMAND_SETUP.md); it has different installation commands and tool names.

## Linux bash

~~~bash
project="$HOME/projects/existing-project"
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project"
~~~

**Stop and review the preview.** Verify the project path, MCP server name and proposed config changes, then run the following command separately:

~~~bash
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project" --apply
python3.12 scripts/toolkit_mcp.py doctor --client codex --project "$project"
~~~

## macOS (Apple Silicon and Intel)

~~~bash
python3.12 --version
project="$HOME/Projects/existing-project"
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project"
~~~

**Stop and review the preview.** Verify the project path, MCP server name and proposed config changes, then run the following command separately:

~~~bash
python3.12 scripts/toolkit_mcp.py install --client codex --project "$project" --apply
python3.12 scripts/toolkit_mcp.py doctor --client codex --project "$project"
~~~

For **Claude Code**, replace `--client codex` with `--client claude`. Codex uses project `.codex/config.toml`, Claude Code project `.mcp.json`. The installer preserves unrelated entries, refuses conflicts or linked paths, and never edits global settings. Restart/reconnect your client, enable project trust as needed and inspect its MCP tool list. `codex mcp list` may assist, but config existence alone **does not prove client activation**.

**Verify the result:** `doctor` checks configuration state. Reconnect Codex/Claude Code and inspect **the client's actual MCP tool list**. If Toolkit is missing, check Python executable paths, the Toolkit checkout path, project trust and client settings. A written config file alone does not prove tool discovery or use by the model.

## Removal and updating

First preview; then, only if correct, remove a matching Toolkit entry with `--apply`:

~~~bash
python3.12 scripts/toolkit_mcp.py uninstall --client codex --project /absolute/existing-project
~~~

**Stop and review the preview.** Verify the project path, MCP server name and proposed config changes, then run the following command separately:

~~~bash
python3.12 scripts/toolkit_mcp.py uninstall --client codex --project /absolute/existing-project --apply
~~~

On Windows use `py -3.12` and a real Windows project path. Removing the MCP entry does not remove copied skills.

The generated config contains **absolute paths** to the existing Toolkit checkout. If it moves, the config must be recreated after removing the previous entry. The MCP server **never fetches updates in the background**. Update the approved Toolkit checkout with the reviewed Git fast-forward instructions in [UPDATING.md](UPDATING.md), then reconnect the client; separately preview/update managed skills through Skill Manager.

The server implements MCP stdio JSON-RPC (2025-11-25/legacy initialization). It does **not** provide an HTTP endpoint for ChatGPT web, OAuth, daemon, OS package manager or remotely downloaded skills. The separately installed ChatGPT plugin is independent. CI checks the stdio handshake and safe local configuration; live Codex/Claude Code activation must be independently tested.
