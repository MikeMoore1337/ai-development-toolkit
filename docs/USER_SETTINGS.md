# Personal and project settings (offline preview)

[Русская версия](ru/USER_SETTINGS.md) | [Issue #394](https://github.com/MikeMoore1337/ai-development-toolkit/issues/394)

Toolkit ships **no owner's personal settings**. Its universal skill catalog and client capability guides are not execution permissions. A user can select local preferences without rebuilding Toolkit or changing another project's `AGENTS.md`.

## Layers

1. **Defaults**: read-only, no CLI agent execution, no paid API, no network execution and no extra spending. Merely listing a client never claims it is installed.
2. **User**: optional local `preferences.json` outside Toolkit checkout. On Linux/macOS: `${XDG_CONFIG_HOME:-~/.config}/ai-development-toolkit/preferences.json`; on Windows: `%APPDATA%\AI Development Toolkit\preferences.json`. A sample is in `profiles/user-preferences.example.json`.
3. **Project**: optional `.adt/config.json` in the target project, intentionally shareable **only if it has no private values**; existing `AGENTS.md` and release policies remain authoritative. Project preferences may only narrow client routes and permissions.
4. **Task**: optionally supplied JSON for one preview; can only narrow project/user permissions.

Non-security language, preferred client and skill-selection choices follow defaults < user < project < task. Security booleans cannot be raised from `false` to `true` by project or task. Approval modes are `deny` or `ask`, never silent allow. Unknown keys and secrets are rejected, not stored. Excluded skill IDs are unioned.

## Preview (no installation)

```sh
python scripts/toolkit_preferences.py --target /path/to/project
python scripts/toolkit_preferences.py --target /path/to/project --user-config /private/preferences.json
python scripts/toolkit_preferences.py --task-config /private/task.json
```

For project configuration, create `.adt/config.json` yourself only after reviewing it. The command never creates, rewrites, installs, contacts an API or invokes an agent. It returns `READ_ONLY_PREFERENCES_PREVIEW`, provenance for effective values and `execution_authorized=false`; it does **not** grant runtime consent. Existing Skill Manager preview/apply commands remain separate.

An explicit user opt-in for CLI routes or paid API merely makes those routes **eligible for subsequent human-controlled routing**, not executable. Actual providers, secrets, spend-enforced caps, client installation and task consent must be verified by their own adapters before any action. This feature never checks or charges an account. Do not include tokens, passwords, local business data or private project names in committed examples.

## Compatibility

Uses only Python 3.12+ standard library and supports Windows, Linux and macOS. An ordinary ChatGPT plugin cannot automatically see a workstation's local JSON; preferences must be provided through a supported, authorized client interface. Existing `profiles/project-profile.example.json` remains a separate template for **verified project facts**, not global preferences. Client-routing integration is tracked in [#395](https://github.com/MikeMoore1337/ai-development-toolkit/issues/395).
