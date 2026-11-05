# AI Development Toolkit for Cursor

A native **Cursor Plugin** with four Agent Skills, concise routing rules, four task commands and a stdio launcher **reusing the already-installed read-only ADT Personal MCP**. This source package is not an installed Marketplace plugin and does not grant execution rights.

## Prerequisites

Cursor, Python 3.10+ available as `python`, and an existing [ADT Personal MCP](../personal-mcp/README.md) installation with its separate Toolkit checkout. Windows defaults to `%LOCALAPPDATA%\ADT-Personal\mcp\adt_mcp.py` and `%LOCALAPPDATA%\ADT-Personal\toolkit-source`. Linux/macOS default to `${XDG_DATA_HOME:-~/.local/share}/adt-personal`. Override with absolute environment paths `ADT_PERSONAL_MCP` and `ADT_TOOLKIT_SOURCE` if necessary.

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
