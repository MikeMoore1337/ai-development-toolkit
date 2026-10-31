# AI Development Toolkit local Codex MCP for Windows, Linux and macOS

## Personal MCP 0.1.13 — newly discovered risk reassessment for opt-in Model Advisor #401

The `toolkit_model_review_checkpoint` read-only tool lets an opted-in
client reassess actual newly discovered risks after inspecting source/diff.
Arguments: original task, up to 8 bounded findings, `stage`, and explicit
`proactive_model_advice=true`. The return is only a lexical risk hint;
no host model inventory, native call, execution or persistent logging.
When native model availability is UNKNOWN, Codex should communicate this
honestly rather than inventing model options or silently suppressing important
risk advice. Others remain opt-out. The installed MCP adapter is updated
separately using `-McpOnly`.
See [#401 guidance](../../docs/PROACTIVE_MODEL_ADVISOR.md).

## Personal MCP 0.1.12 — opt-in proactive Model Advisor #401

`toolkit_prepare_task` now accepts optional `proactive_model_advice` (default
`false`) and returns bounded `model_advisor` risk metadata only for opted-in
clients. It does not attest host model availability, obtain user consent, or
invoke additional models. Install the updated persistent MCP source separately
with `Install-ADT-Personal.ps1 -McpOnly` (no Codex CLI), refresh the existing
user-enabled Advisor managed block and restart Codex Desktop. See
[Proactive Model Advisor](../../docs/PROACTIVE_MODEL_ADVISOR.md).

## Personal MCP 0.1.11 — Codex #357 read-only orchestration

Source version 0.1.11 adds `toolkit_codex_prepare_delegation` and
`toolkit_codex_review_delegation` to the existing ten Personal MCP tools.
Both call the **local Toolkit source** `scripts/codex_host_orchestration.py`
with per-call SHA256SUMS integrity verification. They cannot invoke Codex
Desktop session tools, consume model credits, authorize a host atomic lease,
or independently attest backend model identity or billing.

On Windows, the existing `Install-ADT-Personal.ps1 -McpOnly` mode can upgrade
only the installed user-local MCP module pair with backup/rollback and no Codex
CLI, re-registration, or global instruction edits. Preview with `-WhatIf`.
The dedicated source checkout must also contain the current orchestration
contract and valid checksums. Source updates do not automatically upgrade the
MCP launcher. Restart Codex Desktop and check *live* `toolkit_info` and
`tools/list` before calling the new read-only tools. Unknown incremental
cost must remain blocked, and native host model calls are separate actions.


This is a local read-only stdio MCP for Codex, independent of the [ChatGPT plugin](../chatgpt-plugin/README.md), not a hosted ChatGPT integration. It uses a **separate** Toolkit reference checkout and does not write to your work project.

Prerequisites for **automatic user-level registration**: Codex CLI, Python 3.10+, Git and organization-approved GitHub access. The connected client can be **Codex Desktop or CLI**; verify it in the surface you actually use. Desktop without the CLI can instead use [Project MCP or native skills](../../docs/INSTALLATION.md#codex-desktop). `-McpOnly` only updates package files and does not create a new registration. Copy the installer files outside of your work repository. Your Codex client is responsible for reading project-level skill/role names; the MCP only uses the inventory provided.

## Windows (PowerShell)

```powershell
$package = 'C:\path\to\ai-development-toolkit\integrations\personal-mcp\adt-personal'
powershell.exe -NoProfile -File "$package\Install-ADT-Personal.ps1" -Codex
py -3 "$package\diagnose_mcp.py"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$package\Enable-ADT-AutoUpdate.ps1"
```

The command respects the host execution policy. If it is blocked, use an organization-approved signed/package route; do not weaken policy. Source-update scheduling is an independent opt-in.

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

## Check source version or roll back the dedicated reference checkout

From an **installed** Personal MCP package (not the moving development checkout), use its updater in your user data directory:

- **Windows:** `py -3 "$env:LOCALAPPDATA\ADT-Personal\updater\update_toolkit.py" --preflight`
- **Linux/macOS:** `python3 "${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal/updater/update_toolkit.py" --preflight`

The offline `--preflight` command reports actual local Toolkit version/SHA, last known Git revision/version, and whether a previously saved clean revision can be restored. It does not fetch, update the binary, or touch the work project. `--status` shows only the saved update log.

To undo **only** a last successful reference-checkout update, use the same path with `--rollback` to preview, then `--rollback --apply` after reviewing revisions. A dirty or noncanonical checkout, changed state, or missing previous-good revision blocks the operation. Pause its scheduled updater to keep a rollback pinned; otherwise the next permitted refresh can fast-forward again. The separately installed MCP files and ChatGPT plugin are not changed or confirmed compatible by preflight. Hashes and the Git origin are not a cryptographic signature; see [RU/EN updating instructions](../../docs/UPDATING.md).

Finally restart Codex. Run `codex mcp get ai-development-toolkit`, then **actually invoke** `toolkit_info` and `toolkit_prepare_task` in Codex. Direct stdio diagnostics alone cannot prove Codex activation. Loaded instructions are not native installed skills or spawned agents. The updater refreshes **only Toolkit source**, not the MCP executable or ChatGPT plugin. Respect employer security restrictions and avoid connecting corporate repositories without permission.

[Russian guide](README.ru.md) | [Comparison](../../docs/INTEGRATIONS.md)

## Smaller initial guidance responses (#276)

The Personal MCP `toolkit_prepare_task` tool reads **three** priority `SKILL.md` files by default instead of five. It retains the complete `selected_skills` and `remaining_skills_to_consult` lists. Ask for up to eight with `max_skills`, or read a particular remaining skill through `toolkit_get_skill`; `references` remain on-demand via `toolkit_get_reference`. `context_load_metrics` measures only the actually returned skill/role UTF-8 source bytes (not model tokens). The installed MCP adapter must be updated separately to acquire this behavior; a source checkout refresh alone does not change the installed adapter.

## Prompt refinement and SEO routing

With an up-to-date Toolkit source, `toolkit_prepare_task` can select the `prompt-refinement` and `seo-audit` profiles from plain-language requests. For example, "write a good prompt for Codex from these notes" selects prompt export, while "audit my site's SEO" selects evidence-based SEO guidance. An ordinary "build a site" request **must be fulfilled**, not converted into a prompt for resubmission; new design remains subject to UX/UI approval.

These are read-only **MCP routing and guidance** features: Codex must invoke the tools and perform actual project or website checks using its available permissions. A source-level or offline MCP test is not proof that the user’s Codex installation activated the new skills.

## MCP 0.1.10: bundled launcher and safe upgrade (#190)

For the v0.1.10 source MCP, **both** `mcp/adt_mcp.py` and
`mcp/adt_discovery.py` must be installed beside each other. Copying only the
old single-file launcher makes its `adt_discovery` import fail. The Windows
PowerShell and Linux/macOS shell installers stage and self-check the pair
before updating the persistent user directory. They back up previous files,
check the relocated launcher and restore the prior files on an upgrade
failure. Existing MCP registrations are not deliberately replaced.

The separate daily Toolkit updater does **not** update these two Python files.
The upgrade should use a reviewed, pinned MCP package, not the moving
`main` checkout. Do not consider the install verified until the relocated
launcher's own `--check` and a real invocation in a restarted client both
succeed. Linux has a synthetic installer test; PowerShell has source/contract
tests, not a real Windows user-profile test. macOS native installation and
real Codex model calls remain `NOT_VERIFIED`.

No third-party Skill code is installed or executed by this change.

## Existing Windows MCP: offline package update without Codex CLI (#190)

For a known existing global user launcher at
`%LOCALAPPDATA%\ADT-Personal\mcp\adt_mcp.py`, a reviewed
MCP package's `Install-ADT-Personal.ps1 -McpOnly` updates the
`adt_mcp.py` / `adt_discovery.py` pair after a self-check, with
backups and rollback. `-McpOnly` does not call client CLIs, clone
Toolkit, edit Codex/Claude config or global agent guidance, or install
skills into a project. An existing local Toolkit source checkout is
required. If the Codex registration uses a nonstandard path, stop and
inspect its path first; `-McpOnly` does not re-register MCP.

Use the verified versioned source ZIP from a [passing CI
artifact](https://github.com/MikeMoore1337/ai-development-toolkit/actions/workflows/validate.yml)
**whose commit contains the `-McpOnly` switch**
and validate the expected ZIP SHA-256 before extraction. On an
unrestricted Windows PowerShell installation, from the extracted
`adt-personal` directory run:

```powershell
powershell.exe -NoProfile -File ".\Install-ADT-Personal.ps1" -McpOnly -WhatIf
powershell.exe -NoProfile -File ".\Install-ADT-Personal.ps1" -McpOnly
py -3 "$env:LOCALAPPDATA\ADT-Personal\mcp\adt_mcp.py" --source "$env:LOCALAPPDATA\ADT-Personal\toolkit-source" --check
```

Do not bypass corporate execution policies. Restart Codex Desktop
and actually call `toolkit_info` / `toolkit_prepare_task` in a
new session. A direct self-check is not native client activation evidence.

## Pinned integration source releases (#190)

See [manual SHA-pinned publishing and rollback](../../docs/INTEGRATION_SOURCE_RELEASES.md). CI artifacts expire after 14 days; published source GitHub Release assets are separate from live Codex/ChatGPT plugin installation.
