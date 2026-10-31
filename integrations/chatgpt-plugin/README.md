# AI Development Toolkit - ChatGPT plugin

**ChatGPT workflow:** use the portable skills-only ChatGPT plugin to route engineering, QA, UX/UI and DevOps tasks without installing a local server, supplying an API key, or copying skills into projects. It provides **instructions**, not filesystem/terminal/IDE access.

## Install from GitHub (recommended on supported desktop clients)

You do **not** need a public Plugin Directory listing. The repository includes `.agents/plugins/marketplace.json`, so a user with Codex CLI can register the GitHub marketplace source in one command:

```sh
codex plugin marketplace add MikeMoore1337/ai-development-toolkit
```

**This registers the source; it does not install the plugin.** Restart the supported ChatGPT desktop Work/Codex client, select **AI Development Toolkit (local)** in Plugins Directory, and install **AI Development Toolkit**. Test it in a new chat. A local checkout can also be opened directly, or added with `codex plugin marketplace add ./path/to/ai-development-toolkit`. See the [step-by-step setup](../../docs/ONE_COMMAND_SETUP.md).

This repo-marketplace route is not an automatic installer for ChatGPT web or mobile. The source plugin version `0.1.5` is separate from privately installed plugin releases. No public submission or moderation is needed.

## Windows, Linux, macOS and mobile

On **Windows, Linux and macOS**, ZIP import (where supported) takes place inside ChatGPT, not in the operating system. GitHub repo marketplaces are a separate desktop-only distribution path described above.

1. Build `AI-Development-Toolkit-ChatGPT-Plugin-0.1.5.zip` from a reviewed clone with `python3 integrations/build_packages.py` (`py -3` on Windows), or obtain that exact package from a verified release if it has been published.
2. In ChatGPT, open plugin creation/import **if available to your account** and import the ZIP. Publishing source code alone does not install a plugin. Follow the host's installation UI.
3. Select or mention the plugin in a task. Example: “Using Toolkit, review the Python API files I attached, recommend tests and do not modify source.” Verify the source files were actually available.

**Projects:** supply uploaded files, a supported connected GitHub repository, or other authorized workspace context. The plugin cannot see local IDE files, corporate repos, a local Codex MCP, or the host terminal unless those capabilities are separately provided. Respect employer policy before connecting work data.

**Freshness:** when live tools are available, read relevant GitHub files at one verified revision and follow `MANIFEST.json` rules; otherwise use bundled instructions with an explicit fallback status. This does not auto-upgrade the installed plugin package. A selected role is guidance, not an automatically spawned subagent.

## Other chatbots

The ChatGPT plugin ZIP is **not a universal plugin standard** for Claude, DeepSeek, Qwen, or other chat clients. For chat-only clients without this plugin format, use [`AGENT_START.md`](../../AGENT_START.md) and provide the Toolkit URL plus available project files. If GitHub reading is inaccessible, attach only the needed `SKILL.md` files. Never claim installed plugins, connected repos, or skills were loaded without evidence.

[Russian](README.ru.md) | [Comparison and Codex integration](../../docs/INTEGRATIONS.md)

## Messy requests, explicit prompt exports and SEO

For a normal informal request ("build a site", "fix this bug", "audit SEO"), the plugin should understand the intent internally and **fulfill the task** within available tools and permissions, not ask the user to resubmit a rewritten prompt. The bundled `toolkit-seo-audit` produces evidence-labelled observations with unknown index/rank data marked `NOT_VERIFIED`.

For an explicit "turn these notes into a better prompt for Codex" request, the bundled `toolkit-prompt-refinement` produces one copy-ready prompt without pretending to execute it. Both modes are skills-only and require no paid API.

## Public source release vs owned ChatGPT plugin (#190)

The [pinned source ZIP release](../../docs/INTEGRATION_SOURCE_RELEASES.md) is **not** a replacement for the installed personal ChatGPT plugin. Verify its independently managed identity and version before any separately authorized update.
