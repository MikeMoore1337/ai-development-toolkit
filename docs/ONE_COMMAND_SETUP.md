# Install Toolkit MCP in one paste; install the ChatGPT plugin from a local marketplace

[Русский](ru/ONE_COMMAND_SETUP.md) | [MCP lifecycle](../integrations/personal-mcp/README.md) | [ChatGPT plugin](../integrations/chatgpt-plugin/README.md)

## Before starting

Install Git, Python 3.10+ and the Codex client first. The command below installs **Personal MCP for Codex** to the user profile, not a native skill and not the ChatGPT plugin. It needs access to the official public GitHub repository. No sudo, paid API, copied skills in a work project, or elevated execution-policy bypass. Run from a normal terminal on your own device. Corporate policy applies.

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

Restart Codex, inspect `codex mcp get ai-development-toolkit`, then actually ask Codex to call `toolkit_info` and `toolkit_prepare_task`. A successful file write, installer self-check or CI smoke test does **not** prove model invocation. On Windows you may also run `py -3 "$env:LOCALAPPDATA\ADT-Personal\toolkit-source\integrations\personal-mcp\adt-personal\diagnose_mcp.py"`.

The command is safe to repeat with an **unchanged clean** dedicated checkout. It neither updates the local Git source nor installs skills into projects. If the destination is owned by unrelated content or has modifications, stop and inspect rather than deleting or overwriting it. Source auto-update is [a separate opt-in](UPDATING.md); installed MCP launcher upgrades are separate too.

## ChatGPT/Codex local plugin - installation from the interface

The repository now includes `.agents/plugins/marketplace.json`. In a **supported ChatGPT desktop Work/Codex surface**, open a trusted local checkout of this repository, restart the desktop app, open Plugins, choose **AI Development Toolkit (local)** as the marketplace source and install **AI Development Toolkit**. The marketplace references the existing skills-only plugin directly and does not copy, execute or register a local MCP server. Check the result in a new session.

This is a repository-local marketplace, **not** a public listing and not an automatic installation for ChatGPT web, Android or iOS. The existing privately owned plugin version `0.1.8` and the public source plugin manifest version `0.1.2` are distinct; do **not** overwrite one with the other. Users without the local marketplace surface can use the [documented ZIP import](../integrations/chatgpt-plugin/README.md) when their account allows it.

## Public plugin directory - separate publication gate

OpenAI requires an owner-initiated [plugin submission and review](https://developers.openai.com/plugins/deploy/submission): developer identity/permissions, reviewed package, positive/negative test cases, walkthrough, automated checks, review and subsequent explicit publish. Only **after approval and actual publication** can other users install it by searching the universal directory. Source code, a repo marketplace and an installed PRIVATE plugin do not complete this gate. No publish action or public listing is claimed here.

Status: `REPO_MARKETPLACE_READY_FOR_CLIENT_TEST` / `PUBLIC_DIRECTORY_NOT_SUBMITTED`. Live ChatGPT desktop marketplace installation and public-directory review remain independent acceptance steps.
