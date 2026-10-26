# AI Development Toolkit in DeepSeek Chat

[Русский](README.ru.md) | [Integration overview](../../docs/INTEGRATIONS.md)

This applies to the **ordinary DeepSeek web/mobile chat**, not to DeepSeek Harness and not to the paid API. No special Toolkit plugin or MCP installation is verified in this chat surface.

## Use without a terminal

1. Open the official [DeepSeek Chat](https://chat.deepseek.com/).
2. Provide the task and the Toolkit URL below. If the chat cannot actually read GitHub, attach only the required **public** `SKILL.md`/reference files from a fixed Toolkit revision. Do not assume a link has been fetched.
3. If needed, supply an allowed project snippet or archive. Check that the client can actually read it; do not upload credentials, private work data or other secrets.
4. Require an explicit report of sources actually read, files accessible, work performed, tests actually executed and limitations.

```text
Use https://github.com/MikeMoore1337/ai-development-toolkit as a read-only
source of development and QA guidance for this task: <YOUR TASK>.
Identify the relevant skill instructions only if you can read them.
Report the source files and exact revision if verified.
If GitHub or attachments are unavailable, say so and work from the
materials I supplied. Do not claim installed skills, code execution,
file changes, separate agents or passed tests without observed evidence.
Do not use paid API services.
```

## Evidence and limitations

- **URL_READ**: the content was actually retrieved. URL pasted into chat alone is not evidence.
- **GUIDANCE_ONLY**: externally read `SKILL.md` content is task guidance, not native Skill discovery or installation.
- **L4/L5/L6** (native discovery/activation/measured advantage): **NOT_TESTED / NOT_TESTED / NOT_MEASURED** for Toolkit in ordinary DeepSeek Chat.
- User-reported ZIP + URL trial from 2026-10-20 is **OWNER_REPORTED_PASS**, not independently validated client activation.
- DeepSeek officially advertises chat/file-upload features, but access to a specific archive, GitHub fetch, tools and file writes depends on the actual session.
- This workflow does not call the DeepSeek API, requires no subscription purchase and does not alter the user's project by itself.

Official product reference: [DeepSeek App announcement](https://api-docs.deepseek.com/news/news250115/). This is a documentation-supported route, **not** a live DeepSeek session test.
