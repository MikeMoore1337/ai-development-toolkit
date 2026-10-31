# Install Toolkit MCP in one paste; install the ChatGPT plugin from a local marketplace

[Русский](ru/ONE_COMMAND_SETUP.md) | [MCP lifecycle](../integrations/personal-mcp/README.md) | [ChatGPT plugin](../integrations/chatgpt-plugin/README.md)

## Before starting

Install Git, Python 3.10+ and **Codex CLI** first; check `codex --version`. These one-paste installers use the CLI to register **Personal MCP for Codex** in the user profile, even if you will work in Desktop. They install neither native skills nor the ChatGPT plugin. They need access to the official public GitHub repository. No sudo, paid API, copied skills in a work project, or elevated execution-policy bypass. Run from a normal terminal on your own device. Corporate policy applies.

**Codex Desktop without CLI:** use [Project MCP](MCP_INSTALL.md) with Python 3.12+ or [native managed skills](INSTALLATION.md#codex-desktop). Those routes do not require `codex`. A Windows installer warning that CLI registration was skipped is **not** a successful MCP connection. `-McpOnly` updates package files only; it does not register a new server. Other AI clients have [separate installation instructions](INSTALLATION.md).

The one-paste command obtains Toolkit source once, checks the repository origin and clean worktree, then calls the existing platform installer. It does **not** silently update an existing checkout; [upgrades have a separate review process](UPDATING.md). Cloning `main` is **not** an immutable, SHA-pinned release or a cryptographic signature. For higher-assurance environments use [reviewed SHA-pinned integration source archives](INTEGRATION_SOURCE_RELEASES.md) instead.

## Windows / PowerShell - one paste

~~~powershell
& { $ErrorActionPreference='Stop'; $u='https://github.com/MikeMoore1337/ai-development-toolkit.git'; $d=Join-Path $env:LOCALAPPDATA 'ADT-Personal\toolkit-source'; if (Test-Path -LiteralPath $d) { if ((Get-Item -LiteralPath $d -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Refusing linked Toolkit source' } } else { New-Item -ItemType Directory -Force -Path (Split-Path -Parent $d) | Out-Null; & git clone --depth 1 -- $u $d; if ($LASTEXITCODE -ne 0) { throw 'Git clone failed' } }; $origin=& git -C $d remote get-url origin; if ($LASTEXITCODE -ne 0 -or $origin -ne $u) { throw 'Unexpected Toolkit origin' }; $dirty=& git -C $d status --porcelain; if ($LASTEXITCODE -ne 0 -or $dirty) { throw 'Toolkit source is modified' }; & powershell.exe -NoProfile -File (Join-Path $d 'integrations\personal-mcp\adt-personal\Install-ADT-Personal.ps1') -ToolkitPath $d -Codex; if ($LASTEXITCODE -ne 0) { throw 'MCP installer failed' } }
~~~

Uses the existing tested PowerShell installer. `-File` respects the host execution policy; do not weaken your organization's restrictions. The installer preserves other MCP registrations; a pre-existing registration with the same name is not replaced.

## Linux and macOS / shell - one paste

~~~sh
sh -c 'set -eu; u=https://github.com/MikeMoore1337/ai-development-toolkit.git; d="${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/toolkit-source"; [ ! -L "$d" ] || { echo "Refusing linked Toolkit source" >&2; exit 2; }; if [ ! -e "$d" ]; then mkdir -p "$(dirname "$d")"; git clone --depth 1 -- "$u" "$d"; fi; actual=$(git -C "$d" remote get-url origin); [ "$actual" = "$u" ] || { echo "Unexpected Toolkit origin" >&2; exit 2; }; [ -z "$(git -C "$d" status --porcelain)" ] || { echo "Toolkit source is modified" >&2; exit 2; }; sh "$d/integrations/personal-mcp/adt-personal/Install-ADT-Personal.sh" --source "$d"'
~~~

The Linux/macOS installer currently registers **Codex**, not Claude Code. For a Claude Code project use the independent [project-scoped MCP installer](MCP_INSTALL.md) with `--client claude`. macOS execution of this fresh one-paste command has not been independently verified on a real device.

## Check the installation

**Desktop:** fully restart the app, open the intended local project, inspect its MCP server/tool list, then request real `toolkit_info` and `toolkit_prepare_task` calls there. **CLI:** inspect `codex mcp get ai-development-toolkit`, start a new `codex` session in the project and check `/mcp`, then make the same calls. If you use both surfaces, verify both. A successful file write, installer self-check or CI smoke test does **not** prove model invocation. On Windows you may also run `py -3 "$env:LOCALAPPDATA\ADT-Personal\toolkit-source\integrations\personal-mcp\adt-personal\diagnose_mcp.py"`.

The command is safe to repeat with an **unchanged clean** dedicated checkout. It neither updates the local Git source nor installs skills into projects. If the destination is owned by unrelated content or has modifications, stop and inspect rather than deleting or overwriting it. Source auto-update is [a separate opt-in](UPDATING.md); installed MCP launcher upgrades are separate too.

## Install the plugin directly from the GitHub repository

**No public plugin-directory publication is needed.** The Toolkit repository contains a valid `.agents/plugins/marketplace.json`, whose local plugin entry resolves to `integrations/chatgpt-plugin/ai-development-toolkit`. The marketplace is an installation source, not a local MCP server.

On a machine with Codex CLI and the supported ChatGPT desktop Work/Codex experience, register the **GitHub repository** as a marketplace source with a single command:

~~~sh
codex plugin marketplace add MikeMoore1337/ai-development-toolkit
~~~

This command **adds the marketplace source only**. It does not install the plugin or upgrade an existing personal plugin. In the ChatGPT desktop app, restart the app, open the **Plugins Directory**, select **AI Development Toolkit (local)** as the source, select **AI Development Toolkit**, and choose **Install**. Start a new chat and test a task that should activate a bundled skill. Verify real use separately; source/CI validation does not prove successful installation on another device.

Alternatively, if the user already has a trusted local checkout, open that repository as the workspace in the supported desktop client (or run `codex plugin marketplace add ./path/to/ai-development-toolkit` with a real path). The same checked-in marketplace exposes the plugin. Use `codex plugin marketplace list` to inspect configured sources.

This installation path applies to **supported local Codex/ChatGPT desktop surfaces**, not to ChatGPT web, iOS or Android. Those may allow independent ZIP import through their own UI, depending on account and client support: [ChatGPT ZIP import](../integrations/chatgpt-plugin/README.md). The checked-in source plugin version is `0.1.2`; an existing private installed shell `0.1.8` is a separate installation. Do not overwrite it.

**Scope:** self-service distribution from GitHub only. No universal-public-directory listing, developer review or publication is necessary or planned.

Status: `REPO_SELF_INSTALL_SOURCE_READY`; `LIVE_DESKTOP_INSTALL_NOT_VERIFIED`.
