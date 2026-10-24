# Local Toolkit MCP for Codex and Claude Code

[Русский](ru/MCP_INSTALL.md) · [Installation](INSTALLATION.md) · [Updates](UPDATING.md) · [Choose an integration](INTEGRATIONS.md)

## Features and boundaries

Toolkit includes a real **stdio MCP server** (`scripts/toolkit_mcp.py`) built with Python 3.12+ standard library, no paid APIs or model requests. Its eight tools provide skill catalog/search/reading, specialist and QA role listing/reading, advisory task routing, Skill Manager installation preview, and managed skill status. Roles are guidance documents, **not** automatically started autonomous agents.

**All MCP tools are read-only.** They do not install skills or alter a user's project. When an agent needs to add skills, it can show a preview and ask the operator to use Skill Manager with explicit `--apply`. The separate installer below writes only a project-scoped MCP configuration **after the user executes --apply**. Neither process automatically installs an AI client.

## Before you start

1. Install Codex or Claude Code separately. MCP is not an AI client.
2. Open a terminal **in the cloned Toolkit root**. Python 3.12+ is required; `py -3.12` and `python3.12` below are examples. Replace **all** commands with your actual 3.12+ interpreter (for example `py -3.14` or `python3.14`).
3. Replace example project paths with **existing directories**. The installer does not create projects.
4. Choose `--client codex` or `--client claude`. Review the plan **without `--apply`** before authorizing a write.

## Windows PowerShell

Run from the Toolkit checkout; the selected project directory must already exist.

~~~powershell
$project = 'C:\Work\existing-project'
py -3.12 scripts/toolkit_mcp.py install --client codex --project $project
~~~

**Stop and review the preview.** Verify the project path, MCP server name and proposed config changes, then run the following command separately:

~~~powershell
py -3.12 scripts/toolkit_mcp.py install --client codex --project $project --apply
py -3.12 scripts/toolkit_mcp.py doctor --client codex --project $project
~~~

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
