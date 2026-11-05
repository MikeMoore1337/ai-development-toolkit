# AI Development Toolkit for Cursor

A native **Cursor Plugin** with four Agent Skills, concise routing rules, four task commands and a stdio launcher **reusing the already-installed read-only ADT Personal MCP**. This source package is not an installed Marketplace plugin and does not grant execution rights.

## manage.py not found in the local checkout

Your local Toolkit source is **out of date**, not your Python interpreter. Inspect git status --short --branch before touching it. Never run git reset --hard or pull into a dirty checkout just to fix this error. From the parent of the original Toolkit folder, create a separate clean source:

    Set-Location ..
    git clone --depth 1 --branch main https://github.com/MikeMoore1337/ai-development-toolkit.git ai-development-toolkit-cursor
    Set-Location .\ai-development-toolkit-cursor
    Test-Path .\integrations\cursor-plugin\scripts\manage.py

Do not overwrite an existing destination. Only update a clean approved dedicated checkout with git pull --ff-only.

## Progressive skill use and agent context

The plugin ships four **small routing skills**, not a second copy of the full ADT catalog. Cursor sees each skill's description and decides whether to load it. An always-on, concise adt-routing.mdc rule asks it to use ADT for substantive development, QA, security and UI tasks even without an explicit ADT mention. This is **guidance**, not a guaranteed client-side trigger.

**On-demand workflow:**
1. Identify ONE authorized project and project rules, without scanning all repositories. Ask once when the target is ambiguous.
2. When ADT guidance helps, call toolkit_prepare_task with concrete task and max_skills=1. This response may already contain the full SKILL.md. Avoid routine toolkit_info/catalog calls and duplicate reads.
3. Load a second skill using toolkit_get_skill or a reference using toolkit_get_reference only when the current step needs it. Fetch missing segments if text is truncated.
4. On a real stage change (analysis -> implementation -> regression), call toolkit_prepare_stage with max_skills=1 and confirmed complete consulted_skills name:sha256 digests. Never invent or reuse hashes after context loss.
5. Distinguish guidance, actual Cursor tool calls, real test execution and verified results. MCP stays READ_ONLY.

**Skip ADT** for trivial explanations, tiny standalone edits, user opt-out or an explicitly selected native third-party controller. No paid model/API calls, broad scans, hidden monitoring or automatic releases.

**Live acceptance:** in Cursor Agent with one project open, ask for a read-only FastAPI test-fixture/regression review without mentioning ADT. Inspect actual ADT MCP calls in the tool trace. On a subsequent testing phase check for toolkit_prepare_stage. If a call is absent, automatic routing is NOT_VERIFIED. Static tests and byte measurements do not prove lower Cursor token usage or subscription consumption.

## Prerequisites

Cursor, Python 3.10+ available as `python`, and an existing [ADT Personal MCP](../personal-mcp/README.md) installation with its separate Toolkit checkout. Windows defaults to `%LOCALAPPDATA%\ADT-Personal\mcp\adt_mcp.py` and `%LOCALAPPDATA%\ADT-Personal\toolkit-source`. Linux/macOS default to `${XDG_DATA_HOME:-~/.local/share}/adt-personal`. Override with absolute environment paths `ADT_PERSONAL_MCP` and `ADT_TOOLKIT_SOURCE` if necessary.

### Reuse an existing global Cursor ADT MCP

If ~/.cursor/mcp.json already registers ai-development-toolkit, avoid a duplicate plugin MCP server:

    python integrations/cursor-plugin/scripts/manage.py install --reuse-global-mcp
    python integrations/cursor-plugin/scripts/manage.py install --reuse-global-mcp --apply
    python integrations/cursor-plugin/scripts/manage.py doctor

This preserves the global MCP registration and omits the bundled mcp.json from the installed plugin. The unflagged installer fails closed on duplicate registration. The reuse flag requires an existing compatible global ADT server.

## Install / update / rollback

From the root of a verified clean Toolkit checkout:

```bash
python integrations/cursor-plugin/scripts/manage.py install
python integrations/cursor-plugin/scripts/manage.py install --apply
python integrations/cursor-plugin/scripts/manage.py doctor
python integrations/cursor-plugin/scripts/manage.py update
python integrations/cursor-plugin/scripts/manage.py update --apply
python integrations/cursor-plugin/scripts/manage.py rollback
python integrations/cursor-plugin/scripts/manage.py rollback --apply
```

The default target is `~/.cursor/plugins/local/ai-development-toolkit`. Each mutation requires `--apply`. Unmanaged, symlinked or locally modified destinations are rejected; replaced managed versions are backed up outside Cursor's plugin discovery directory. `rollback` restores the last managed version or removes a first install. No project files or MCP registrations are changed.

Reload Cursor using **Developer: Reload Window**, then open **Customize** and independently confirm components (skills, rules, commands, MCP). Make actual `toolkit_info` and `toolkit_prepare_task` calls in Cursor Agent; `doctor` only validates local files and does not prove real invocation. Avoid registering ADT again in `~/.cursor/mcp.json` if the plugin MCP is already active.

Native skills: `adt-development`, `adt-qa`, `adt-security`, `adt-ux-ui`. Commands: `/adt-build`, `/adt-qa`, `/adt-security`, `/adt-ui`. The installed MCP remains **READ_ONLY**, model use is governed by Cursor separately, and no paid API is introduced. Source updates do not update the installed Personal MCP executable.

[Русский](README.ru.md) · [Cursor Plugin reference](https://cursor.com/docs/reference/plugins) · [Personal MCP](../personal-mcp/README.md)
