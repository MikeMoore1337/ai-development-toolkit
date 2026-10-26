# AI Development Toolkit integrations - capabilities and environments

AI Development Toolkit offers **two equally important integrations** built on shared skill, role and workflow guidance: the [ChatGPT plugin](../integrations/chatgpt-plugin/README.md) and the [local Codex MCP](../integrations/personal-mcp/README.md). **Choose by where the project and authorized tools are available**, not by a ranking of users or clients. Neither route requires a paid API.

## What you can do

- **Match a task to relevant skills and roles.** Each integration helps select a focused Toolkit workflow rather than loading the entire catalog. Selection does not prove that every referenced skill was executed.
- **Use missing guidance on demand.** The ChatGPT plugin uses bundled skills or currently accessible, verified GitHub instructions. Codex can obtain targeted guidance through `toolkit_prepare_task`, using the existing skill names supplied by its host. A role is a set of instructions, **not** a new agent process.
- **Work without copying Toolkit files into the project.** Both integrations can provide guidance without changing the project. Installing native project skills is a separate, explicitly authorized Skill Manager action.
- **Access updated Toolkit sources.** The plugin can read a consistent GitHub revision at task time *when supported tools and required verification are available*; otherwise it reports a bundled fallback. The local MCP reads a separately maintained checkout, with an optional scheduled updater. **Neither automatically upgrades its own installed package.**
- **Respect project boundaries.** Work occurs only with project content the selected host is authorized to access. Skills and MCP tools alone do not grant new filesystem, repository or execution permissions.

## Choose one of four paths first

Choose by **where the task is performed**. The ChatGPT and Codex integrations are equally important; the other two paths serve different setup needs.

| Need | Route | Required environment | How to verify |
| --- | --- | --- | --- |
| Advice **inside ChatGPT** | [ChatGPT plugin](../integrations/chatgpt-plugin/README.md) | Host account/client supports plugin import; no local Python or MCP | Select the imported plugin, ask for a specific skill, inspect the actual source revision or declared fallback; uploaded/connected project files still need separate authorization |
| Read-only Toolkit guidance **across Codex projects** | [Personal MCP](../integrations/personal-mcp/README.md) (global user registration) | Codex, Git, **Python 3.10+**, separate Toolkit reference checkout | Restart Codex, inspect `codex mcp get ai-development-toolkit`, then call real `toolkit_info` and `toolkit_prepare_task` **inside Codex** |
| Read-only MCP **in one Codex or Claude Code project** | [Project MCP](MCP_INSTALL.md) (`scripts/toolkit_mcp.py`) | Existing project, Toolkit checkout, **Python 3.12+**; preview configuration, explicit `--apply` | Run the installer's `doctor --client codex|claude --project <existing-path>`, reconnect, inspect actual client MCP tools |
| **Copy native skill files** into an existing project (no MCP) | [Skill Manager v2](INSTALLATION.md) | Existing project and Toolkit checkout, **Python 3.12+**; preview and explicit `--apply` | `python scripts/adt.py status --target <existing-path>` verifies files/drift, **not** client activation |

If you only want to describe your task without installing anything, use [the beginner guide](BEGINNER_START.md). Other conversational clients can follow [AGENT_START.md](../AGENT_START.md); a ChatGPT plugin ZIP is **not** a universal plugin or MCP package.

### Verify versions and updates independently

- **Source:** compare the Git SHA and `MANIFEST.json.version` in the specific Toolkit checkout; publishing a new source tag does **not** install anything on user computers.
- **Personal MCP:** `toolkit_info` exposes the installed MCP adapter version separately from its source checkout. Optional Windows Task Scheduler, Linux systemd user and macOS launchd jobs refresh **only the separate checkout**. They do **not** upgrade installed MCP files.
- **Project MCP:** uses the configured checkout; it has **no background updater**. `doctor` proves the on-disk config only, not that the client invoked the tools.
- **ChatGPT plugin:** source ZIP version, installed personal plugin version and dynamically loaded GitHub revision can differ. GitHub read-on-demand is not automatic installed-plugin upgrade.
- **Skill Manager:** file changes happen only after preview plus explicit `--apply`; `status` proves the managed file state, not that an AI client used the skills.
- **Evidence:** local configuration/stdio checks are not L4 live client discovery, L5 actual skill use or L6 measured benefit. Use `NOT_VERIFIED` / `NOT_MEASURED` when evidence is missing.

**Minimal diagnostic record (#317):** call `toolkit_info` in the **actual connected Codex client** and inspect `diagnostics.version_boundaries`. This exposes the running Personal MCP adapter, the exact local Toolkit manifest and the local Git SHA when available; it does **not** detect installed ChatGPT plugins or prove the latest published GitHub Release. The statuses `published_github_release`, `installed_chatgpt_plugin` and `public_chatgpt_plugin_source` are deliberately `NOT_VERIFIED` from Personal MCP. Cross-check the published Toolkit tag on GitHub and the separately installed ChatGPT plugin version using its own client/Plugin Creator UI. Never copy a public ZIP version into the installed plugin field. The optional checkout updater and the installed adapters are separate; neither installed MCP nor ChatGPT plugin is upgraded by a source checkout update. The returned diagnostic is read-only and does not establish actual skill activation or effectiveness.

## Compare ChatGPT and Codex conversational integrations

| Capability | ChatGPT plugin | Codex local MCP |
| --- | --- | --- |
| Where it runs | In ChatGPT when the account supports custom plugins | On a computer with Codex CLI and Python |
| Windows | ChatGPT plugin interface | PowerShell install; Windows Task Scheduler updater |
| Linux | ChatGPT plugin interface | Shell install; systemd user timer updater |
| macOS | ChatGPT plugin interface | Shell install; launchd user agent updater |
| Mobile | Available only where the ChatGPT client supports the plugin | Not a mobile local Codex installation |
| Project context | Uploaded files, approved connected repositories or other host-provided sources | Current workspace files accessible to Codex, **not** directly to MCP |
| Skill selection | Plugin routing and available Toolkit source | `toolkit_route_task` / `toolkit_prepare_task` |
| Updating reference skills | On-demand verified GitHub read, if available; bundled fallback otherwise | Scheduled update of local Toolkit checkout, when enabled |
| Update installed integration | Separate plugin release/import/update | Separate MCP release/reinstallation |
| Installs native skills or modifies project automatically | No | No |
| Paid API requirement | None for this skills-only package | None for this local server |

## Bounded on-demand guidance and source-byte measurements (#276)

`toolkit_prepare_task` now returns at most **three** priority `SKILL.md` instructions by default (formerly five); callers needing a larger initial load may explicitly set `max_skills=4..8`. The unchanged `selected_skills` and `remaining_skills_to_consult` identify all eligible skills: request deferred instructions through `toolkit_get_skill` and optional references individually through `toolkit_get_reference`. File-based native skill installations and the ChatGPT plugin's own context handling are **not modified**.

`context_load_metrics` measures only UTF-8 instruction bytes **actually returned** by Personal MCP: skill bytes, role bytes, total bytes, count deferred and zero automatically loaded reference files. No additional source is read to produce the metric. The metric excludes JSON-RPC envelope/duplicate text-vs-structured serialization, and is **not** a network payload byte count. `model_tokens=NOT_MEASURED` and `client_usefulness=NOT_TESTED`; smaller source output is **not** proof of fewer billed model tokens or unchanged live-model effectiveness.

Reproducible baseline proxy at Toolkit commit `053a200f4215162340ab5d1d4ff7ac9c13c8db5e` (manifest-list order, `SKILL.md` sizes, **not** priority-adjusted runtime payload):

| Profile | First five source bytes | First three source bytes | Source bytes omitted initially |
| --- | ---: | ---: | ---: |
| backend | 5,502 | 2,727 | 2,775 |
| fullstack | 6,994 | 4,441 | 2,553 |
| general | 5,664 | 3,477 | 2,187 |

Actual selection can reorder skills; run `toolkit_prepare_task` with explicit `max_skills=5` and compare its `context_load_metrics` against the default to measure the specific request. Earlier profile byte metrics account for all installed files, including references, and therefore must **not** be equated with MCP request payload.

## Installation and usage

**ChatGPT:** [English instructions](../integrations/chatgpt-plugin/README.md) · [Инструкция на русском](../integrations/chatgpt-plugin/README.ru.md)

**Codex MCP (Windows, Linux, macOS):** [English instructions](../integrations/personal-mcp/README.md) · [Инструкция на русском](../integrations/personal-mcp/README.ru.md)

**Other conversational clients:** The ChatGPT plugin ZIP is not a universal plugin format. For clients without a compatible plugin mechanism, use [AGENT_START.md](../AGENT_START.md) with the Toolkit URL and authorized project files. Do not claim a client installed, loaded or executed a skill without evidence.

**Trust boundaries:** A ChatGPT skills-only plugin cannot connect to a private laptop's stdio MCP without a separate authorized integration. Do not publish account plugin identifiers, tokens, or employer source files. Repository publication does not install either integration for existing users.

## DeepSeek Chat - reference-only route (2026-10-26)

[DeepSeek Chat (web/app)](../integrations/deepseek-chat/README.md): separate RU/EN instructions, historical owner-reported ZIP+URL result, no verified native Skill plugin, client-run tests or paid API. DeepSeek Harness is a different filesystem/MCP/plugin client and must not be confused with ordinary chat.
