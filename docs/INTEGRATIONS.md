# AI Development Toolkit integrations - capabilities and environments

AI Development Toolkit offers **two equally important integrations** built on shared skill, role and workflow guidance: the [ChatGPT plugin](../integrations/chatgpt-plugin/README.md) and the [local Codex MCP](../integrations/personal-mcp/README.md). **Choose by where the project and authorized tools are available**, not by a ranking of users or clients. Neither route requires a paid API.

## What you can do

- **Match a task to relevant skills and roles.** Each integration helps select a focused Toolkit workflow rather than loading the entire catalog. Selection does not prove that every referenced skill was executed.
- **Use missing guidance on demand.** The ChatGPT plugin uses bundled skills or currently accessible, verified GitHub instructions. Codex can obtain targeted guidance through `toolkit_prepare_task`, using the existing skill names supplied by its host. A role is a set of instructions, **not** a new agent process.
- **Work without copying Toolkit files into the project.** Both integrations can provide guidance without changing the project. Installing native project skills is a separate, explicitly authorized Skill Manager action.
- **Access updated Toolkit sources.** The plugin can read a consistent GitHub revision at task time *when supported tools and required verification are available*; otherwise it reports a bundled fallback. The local MCP reads a separately maintained checkout, with an optional scheduled updater. **Neither automatically upgrades its own installed package.**
- **Respect project boundaries.** Work occurs only with project content the selected host is authorized to access. Skills and MCP tools alone do not grant new filesystem, repository or execution permissions.

## Choose an integration for the actual environment

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
