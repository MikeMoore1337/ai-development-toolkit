# AI Development Toolkit local Codex MCP for Windows, Linux and macOS

This is a local read-only stdio MCP for Codex, independent of the [ChatGPT plugin](../chatgpt-plugin/README.md), not a hosted ChatGPT integration. It uses a **separate** Toolkit reference checkout and does not write to your work project.

Prerequisites: Codex CLI, Python 3.10+, Git and organization-approved GitHub access. Copy the installer files outside of your work repository. Your Codex client is responsible for reading project-level skill/role names; the MCP only uses the inventory provided.

## Windows (PowerShell)

```powershell
$package = 'C:\path\to\ai-development-toolkit\integrations\personal-mcp\adt-personal'
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$package\Install-ADT-Personal.ps1" -Codex
py -3 "$package\diagnose_mcp.py"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$package\Enable-ADT-AutoUpdate.ps1"
```

## Linux (systemd user timer)

```bash
package="$HOME/ai-development-toolkit/integrations/personal-mcp/adt-personal"
sh "$package/Install-ADT-Personal.sh"
sh "$package/Enable-ADT-AutoUpdate.sh"
python3 "$package/diagnose_mcp.py" \
  --launcher "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/mcp/adt_mcp.py" \
  --source "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/toolkit-source"
systemctl --user list-timers adt-personal-toolkit-update.timer
```

## macOS (launchd user agent)

```bash
package="$HOME/ai-development-toolkit/integrations/personal-mcp/adt-personal"
sh "$package/Install-ADT-Personal.sh"
sh "$package/Enable-ADT-AutoUpdate.sh"
python3 "$package/diagnose_mcp.py" \
  --launcher "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/mcp/adt_mcp.py" \
  --source "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/toolkit-source"
launchctl print "gui/$(id -u)/com.ai-development-toolkit.personal-updater"
```

Replace the sample checkout path with the location of the extracted package or repository. The Linux/macOS shell installer registers a global `ai-development-toolkit` MCP and maintains a bounded global `AGENTS.md` block, with backups. The updater is optional: Linux uses systemd --user, macOS uses launchd in an interactive GUI session. On machines without these supported schedulers, do not claim automatic updates; run the updater manually with explicit `--source` and `--state-dir`.

Finally restart Codex. Run `codex mcp get ai-development-toolkit`, then **actually invoke** `toolkit_info` and `toolkit_prepare_task` in Codex. Direct stdio diagnostics alone cannot prove Codex activation. Loaded instructions are not native installed skills or spawned agents. The updater refreshes **only Toolkit source**, not the MCP executable or ChatGPT plugin. Respect employer security restrictions and avoid connecting corporate repositories without permission.

[Russian guide](README.ru.md) | [Comparison](../../docs/INTEGRATIONS.md)
