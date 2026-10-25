# I already have a project: where do I start?

[Русская версия](ru/EXISTING_PROJECT.md) · [Start without a terminal](BEGINNER_START.md) · [Home](../README.md)

**You don't have to install Toolkit to ask for help with an existing app, site or repository.** Toolkit is an instruction library, not a client that automatically sees your files. Choose a way to share the project and describe one task.

## 1. Choose how the AI can access your project

| What you have | How to share it | What to verify |
| --- | --- | --- |
| ChatGPT or Claude in the browser | Use **+ / paperclip / Add files** where available and attach permitted files or a small ZIP. If uploads are unavailable, paste the relevant text | Ask which files were actually read. This does not grant access to your entire computer or run local tests |
| A public GitHub repository | Provide **two links**: your project and [Toolkit](https://github.com/MikeMoore1337/ai-development-toolkit) | Confirm the AI can open both links; a URL does not grant access to private files |
| An open project in Codex / Claude Code | Describe the task in the selected project and provide the Toolkit link | Confirm the correct folder is available. Actual changes require permission |
| ChatGPT Work, if offered to your account | Use Work for supported, multi-step tasks with connected apps and approved files | **Work** is a separate working mode; **Chat** is for discussion and analysis of shared material. Neither automatically accesses your computer |

**Do not share passwords, tokens, secret keys or customer data.** Begin with a README, one or two relevant files, an error message or short reproduction steps. For large projects ask the AI which files are needed.

## 2. Describe the goal and permissions

Copy this into your available client:

> Use the project files I provide and https://github.com/MikeMoore1337/ai-development-toolkit. My goal is: **[describe your problem]**. First tell me exactly what you can access and what is missing. Do not delete data, deploy, spend money or edit files without separate approval. Propose a small plan and report only the work and checks you actually performed.

For bugs add **expected behavior → actual behavior → reproduction steps → error message**. You do not need paid APIs, Git or a terminal to send this request.

## 3. Understand the result

| Status | Plain-language meaning |
| --- | --- |
| `PASS` | A check really ran and succeeded; ask for its output |
| `FAIL` | A check really ran and found a failure |
| `NOT_RUN` | The check was not executed; working software is not proven |
| `NOT_VERIFIED` | A claim has not been confirmed by evidence |
| `GUIDANCE_ONLY` | The AI read instructions; this is not proof that a skill was used or code was fixed |
| `BLOCKED` | The action cannot proceed without access, tools or permission |

You need not understand `MCP` (AI tool connection) or `profile` (task-specific group of instructions) to get started. The technical flag `--apply` means **write the reviewed changes**; you do not need it in a regular chat.

**Important:** skill files copied ≠ skill discovered ≠ skill used ≠ application fixed and tested. Ask for actual file changes and executed checks, and keep unrun tests `NOT_RUN`.

For details see the [client comparison](BEGINNER_CLIENT_DETAILS.md). The [coding agent instructions](../AGENT_START.md) are **written for the agent**, not the user's first step. More examples are in the [beginner guide](BEGINNER_START.md).
