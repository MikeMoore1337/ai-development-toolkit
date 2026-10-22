# AI Development Toolkit integrations

**Two equal integration paths, one Toolkit skill and role catalog.** Choose based on where your work happens and which project sources the client is allowed to access:

| Integration | What it adds | Setup |
| --- | --- | --- |
| **[ChatGPT plugin](chatgpt-plugin/README.md)** | Task-driven guidance from bundled or verified available Toolkit skills, without a local server | ChatGPT plugin interface on supported accounts (Windows, Linux, macOS and supported mobile clients) |
| **[Local Codex MCP](personal-mcp/README.md)** | Task routing and on-demand skill/role guidance for the current Codex workspace | Install on Windows, Linux or macOS; optional automatic local Toolkit updates |

Both support focused skill selection without copying files into a project. Neither grants undocumented access, automatically modifies projects, or uses a paid API. The ChatGPT plugin and Codex MCP are **independent** and neither is a prerequisite for the other.

**Two local MCP variants exist:** the existing [project-scoped Toolkit MCP](../docs/MCP_INSTALL.md) configures one Codex/Claude Code project, while the personal package above configures a **user-level Codex MCP** and may add a clearly marked block to global `AGENTS.md`. Both use the registration name `ai-development-toolkit` but expose **different tool sets**. Choose one scope per client; do not assume registrations can be combined or have verified precedence. The personal updater updates only its dedicated skill-source checkout, not the MCP executable, project files or ChatGPT plugin.


[Русский](README.ru.md) · [Detailed feature comparison](../docs/INTEGRATIONS.md) · [Other chat clients](chatgpt-plugin/README.md#other-chatbots)

Do not publish private tokens, account plugin IDs or corporate project files.
