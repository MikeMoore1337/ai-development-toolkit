# AI Development Toolkit for DeepSeek Harness

[Русский](README.ru.md) | [Ordinary DeepSeek Chat](../deepseek-chat/README.md)

This is a **local, configuration-only Cordis Bundle** for the official DeepSeek Harness. It mounts the Toolkit's **existing read-only stdio MCP server**, not a second server. No paid DeepSeek API is used by the bundle generator or the MCP server.

## Prepare and install (Linux / macOS)

Prerequisites: a trusted Toolkit checkout, Python 3.12+, Node.js, and an installed DeepSeek Harness (`dsh`). The sample output folder must **not exist**; it is created only with `--apply`.

```bash
cd /path/to/ai-development-toolkit
bundle="$HOME/adt-harness-bundle"
python3.12 integrations/deepseek-harness/prepare_bundle.py --output "$bundle"
# Read the preview; this step alone changes nothing.
python3.12 integrations/deepseek-harness/prepare_bundle.py --output "$bundle" --apply
dsh plugin --profile web add "link:$bundle"
dsh --profile web --dump-config
```

## Windows PowerShell

```powershell
cd D:\path\to\ai-development-toolkit
$bundle = Join-Path $env:USERPROFILE "adt-harness-bundle"
py -3.14 integrations/deepseek-harness/prepare_bundle.py --output $bundle
py -3.14 integrations/deepseek-harness/prepare_bundle.py --output $bundle --apply
dsh plugin --profile web add "link:$bundle"
dsh --profile web --dump-config
```

The generator uses the **absolute path of the executing Python interpreter** and this checkout's `scripts/toolkit_mcp.py`, with safe YAML encoding. No project, Harness profile or source file is changed by generation. **Installing the generated bundle with `dsh plugin` is a separate explicit action** that changes the selected Harness profile. Restart the Harness session/profile when required, then check that tools `mcp__adt__toolkit_catalog` / `mcp__adt__toolkit_read_skill` are actually listed and callable. A config row alone proves neither discovery nor invocation.

The checked-in `package.json` and `cordis.patch.yml` are a disabled template. **Do not install that unconfigured source directly and assume success**. Generate a local bundle first. Keep that generated folder in place: `link:` installation references its path. If you move or update Python/Toolkit, regenerate into a new directory after checking the source and update the installed bundle explicitly.

## Native project Skills

Harness reads `<git-project>/.agents/skills/<name>/SKILL.md` and `<git-project>/.dsh/skills/<name>/SKILL.md`. Use the existing Toolkit Skill Manager in Codex layout for an explicitly approved managed copy into `.agents/skills`; it does not manage `.dsh/skills`. An ordinary Toolkit URL does **not** install a Skill. Project `.dsh/skills` wins same-name precedence over `.agents/skills` according to upstream documentation. Avoid conflicting copies and verify client discovery separately.

## Boundaries and troubleshooting

- The source template is disabled by design; the generator writes an enabled configuration **only** to a fresh external output directory, after `--apply`.
- The MCP server itself is read-only. It returns Skill/role guidance but does not run code, install Skills or edit user projects.
- A Harness MCP connection is **profile-scoped**, not intrinsically isolated per workspace. Review tool exposure and any other profile policies before enabling it.
- If the generated config is missing from `--dump-config`, check the active profile, Python executable, absolute Toolkit path and duplicate `adt-mcp` rows; remove the bundle with `dsh plugin --profile web remove @local/ai-development-toolkit-harness` and restart as needed.
- Offline verification covers bundle generation and client contracts; native Harness detection/use is **NOT_TESTED**, benefit **NOT_MEASURED**. No actual account or Harness process was started as part of the repository change.

Official pinned source: [DeepSeek Harness Skills](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/docs/subsystems/skills.md), [Cordis plugin template](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/preset/agent-preset/skills/cordis-plugin-development/templates/mcp/package.json).
