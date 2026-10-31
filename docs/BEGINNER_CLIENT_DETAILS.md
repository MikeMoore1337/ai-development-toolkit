# Detailed AI client comparison

[Русская версия](ru/BEGINNER_CLIENT_DETAILS.md) · [Short beginner route](BEGINNER_START.md) · [I already have a project](EXISTING_PROJECT.md)

This reference contains advanced client details, official links and limitations. **You do not need to read it to get started.** Feature access depends on account settings and permissions.

## Choose your AI client

For installation, use the [client-by-client guide](INSTALLATION.md): separate Codex Desktop and CLI steps, Claude Code Desktop and CLI, hosted chats and other compatible coding clients. The Codex example below describes the **cloud route**; local Skill Manager commands need Python, not a separately installed Codex CLI.

| Client / mode | Easiest supported start | Can change your app? | Can run tests? | Toolkit skills | Terminal for that route |
| --- | --- | --- | --- | --- | --- |
| [OpenAI Codex](#openai-codex), cloud environment | Open Codex Cloud and select a connected, prepared GitHub project | Yes, in the authorized cloud checkout; local Desktop tasks can work in selected folders | Yes, when tools/dependencies and permission exist | Repository `.agents/skills` is documented for Codex; you must actually provide the skills in that repository/environment | **Not required** for the cloud UI path after environment setup; local managed Toolkit install runs Python commands, without requiring Codex CLI |
| [ChatGPT](#chatgpt), Chat / Work | Start a chat or a permitted Work task, then attach relevant files | Chat can prepare text/files; Work can modify supported accessible sources with connected tools and permissions, not arbitrary local files from web/mobile | Only in an execution-capable mode with tools, not guaranteed in ordinary Chat | Workspace/plugin skills are **not** the same as local Toolkit `SKILL.md`; automatic discovery from this repo is **not established** | **Not required** to discuss or upload; code execution/repository writes depend on tools |
| [Claude Code](#claude-code), Desktop Code / cloud | Open the Code tab, select an existing local project or available cloud session | Yes, within the authorized project/session | Yes, with execution tools and dependencies | Project `.claude/skills` supported; local manager preview/apply is a separate CLI step | **Not required** for a configured Desktop GUI session; installing dependencies/setup may still require commands |
| [Claude](#claude), chat / Projects | Start a chat or Project, upload selected materials | Produces text/artifacts; no automatic access to your local repository | Code execution only when enabled and applicable, not your local project tests by default | Custom skills may be uploaded as a **ZIP through Customize > Skills** when enabled; not the Toolkit managed install | **Not required** for chat or supported UI skill upload; preparing a ZIP may require a separate local step |

These are **documentation-level capabilities**, reviewed **2026-10-20**, not live acceptance results. Feature access depends on plan, account, platform, region, workspace settings and explicit grants. Never treat a missing control as user error. Source links are below each client. No paid API or subscription is required merely to read these guides; some client execution modes have separate plan/access requirements which must be checked in the actual account.

### OpenAI Codex

**Best for:** making real code changes in a GitHub repository or a local project, when coding tools are available.

1. Open [Codex Cloud](https://learn.chatgpt.com/docs/cloud) on web/desktop; connect an authorized GitHub repository if prompted. Create and publish a cloud environment **only after reviewing its proposed setup and access**. An existing published environment is enough. On mobile you can select an existing environment; first-time setup is documented for web/desktop.
2. Select that environment, describe one of the tasks below and set the constraint: *inspect first, do not deploy, charge or publish without approval*. Review the diff and the test output before allowing a commit or PR.
3. **If Toolkit skills are needed**, arrange for the selected skills to exist under the relevant repository's `.agents/skills/<skill-name>/SKILL.md`. Do not assume that opening the Toolkit README installs skills in a different repository. Use the [managed CLI](BEGINNER_START.md#optional-local-managed-install) in a supported local coding environment, or have an authorized coding agent propose file changes for review; these are distinct from merely reading the documentation.
4. When blocked without a repository/environment: ask for an MVP specification and a file list, **not** a fictional edited project. Stop if access, environment preparation or test tools are missing.

**Terminal:** optional for a configured Codex Cloud UI route; not optional for personally running the current Toolkit's local `adt.py`. Codex Desktop can operate on selected local folders but requires an installed supported app and local permissions. Account, cloud availability and quotas are controlled by OpenAI; do not promise free execution.

**Official references (checked 2026-10-20):** [Codex Cloud setup](https://learn.chatgpt.com/docs/cloud), [Codex local skill discovery](https://learn.chatgpt.com/docs/build-skills), [ChatGPT/Codex modes](https://help.openai.com/en/articles/20001275). **Unverified here:** actual skill discovery, activation and benefit in a running Codex session.

### ChatGPT

**Best for:** first discussing an idea, studying uploaded material, planning a small app or reviewing code with tools that your selected mode actually provides.

1. Open [ChatGPT](https://chatgpt.com/). Start Chat (text-first) or, if available, Work. Create a Project if you want to keep related chats and uploaded files together; attach only nonsecret materials you may share.
2. Paste one of the requests below. Ask the assistant to report **which tools it actually has**. Regular Chat can discuss and prepare code or downloadable artifacts, but this alone does not change or test your actual repository.
3. If you have an eligible Work mode and have granted access to a repository, connected app or desktop-local folder, request authorized changes there. Work on web/mobile does **not** automatically read files on your computer. Review proposed write actions and tests as evidence.
4. **Toolkit skills:** instructions shared in chat can inform a conversation; neither uploading the README nor having Codex skills installed locally proves ChatGPT Chat has discovered or activated them. ChatGPT workspace Skills and plugins have their **own installation/permission controls**; do not equate them with a Toolkit local copy.

**Fallback:** without Work, repo tools or file-writing access, produce a short specification or files for manual use and label tests `NOT_RUN`. No terminal is needed for this fallback.

**Official references (checked 2026-10-20):** [Using ChatGPT](https://learn.chatgpt.com/docs/use-chatgpt), [Work and Codex](https://help.openai.com/en/articles/20001275), [separate skill distribution paths](https://learn.chatgpt.com/docs/enterprise/skills), [GitHub access limitations](https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt-drease). **Unverified:** direct automatic installation/activation of this Toolkit's local skills in ordinary Chat.

### Claude Code

**Best for:** working with existing project code through an authorized coding agent.

1. In [Claude Desktop Code](https://code.claude.com/docs/en/desktop), open the Code tab, choose a local folder/session or a cloud environment offered to your account, and review project trust and permissions. You need an installed Desktop app for its local GUI, but typing into a terminal is not the sole launch path.
2. Describe one task, ask for inspection and a small diff before changes, then review command/test output. Local dependencies and project setup may still require installation or command execution even when the **human** interacts only through the GUI.
3. Toolkit's managed `--layout claude` installs under `.claude/skills/<skill-name>/SKILL.md`. The client documents project-local skills, but a copied folder is only filesystem evidence until you observe discovery and use. A Claude account skill synced from claude.ai is another mechanism; cloud sessions do not inherit unrelated personal local folders.
4. **Fallback:** without Desktop, a project, installation permissions or executable tools, prepare a change proposal or use an authorized coding environment later.

**Official references (checked 2026-10-20):** [Claude Code Desktop](https://code.claude.com/docs/en/desktop), [skills and scope](https://code.claude.com/docs/en/skills). **Unverified:** live discovery or invocation of installed Toolkit skills on this repository; no AI-agent trial was run.

### Claude

**Best for:** brainstorming, reviewing uploaded documents and code, preparing a feature specification or optional use of supported cloud-created artifacts.

1. Open [Claude](https://claude.ai/) chat or a Project and add a minimal description or permitted files. Projects can hold knowledge and instructions; this does not grant access to an unshared local repository.
2. Paste one of the requests below. Ask for a plan or a prepared artifact and for an explicit account of what was **not** modified or executed.
3. **Optional Skills UI:** if your account exposes `Customize > Skills` and code execution/file creation is enabled, Anthropic documents uploading a **ZIP containing a correctly structured skill folder with SKILL.md**. Review the source content and ZIP before upload. This is **not** running Toolkit's managed install and cannot be assumed for every setup. Upload only a minimal, distributable skill you understand, not the entire Toolkit or protected/private sources; check organization restrictions.
4. If skill upload is unavailable, use a short excerpt or the relevant nonsecret guide as conversation context. If you need changes in an actual repository and Claude chat has no authorized write tool, move the task to a properly configured coding environment.

**Official references (checked 2026-10-20):** [Claude Projects](https://support.claude.com/en/articles/9517075-what-are-projects), [using custom skills](https://support.claude.com/en/articles/12512180-use-skills-in-claude), [skill ZIP structure](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills). **Unverified:** that an arbitrary Toolkit skill ZIP was accepted, discovered or invoked in a real Claude account.

