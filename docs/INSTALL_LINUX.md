# Install AI Development Toolkit - Linux

[Русский](ru/INSTALL_LINUX.md) · [All platforms](INSTALLATION.md) · [Update guide](UPDATING.md)

## No-terminal route

If you only need guidance in ChatGPT, Claude or an IDE agent, installation is optional: [start here](BEGINNER_START.md). A repository link alone does not activate skills.

## Prerequisites

Requires Git, Python 3.12+, GitHub read access and an **existing** project directory. Install/configure the AI client separately.

Check Python 3.12+ and Git. Availability of `python` and the `python3.12` distro package varies. Do not run privileged package installation without authorization.

## Install into an existing project

**Before running the commands:** replace the example `project=...` path with an **existing** project directory. Toolkit will not create it. Every `python3.12` command below is an example: if you have Python 3.13/3.14, replace **every** invocation, including the version check, with the actual executable, such as `python3.14`.

From the Toolkit directory. Inspect project AGENTS.md / CLAUDE.md and unmanaged skills first:

~~~bash
python3.12 --version
command -v python3.12
git --version
git clone https://github.com/MikeMoore1337/ai-development-toolkit.git
cd ai-development-toolkit
project="$HOME/projects/existing-project"
python3.12 scripts/adt.py profile list
python3.12 scripts/adt.py doctor --target "$project"
python3.12 scripts/skill_manager.py install --target "$project" --layout codex --profile general
~~~

**Stop after the preview.** Check the destination, file list and conflicts before running the following apply and status commands separately:

~~~bash
python3.12 scripts/skill_manager.py install --target "$project" --layout codex --profile general --apply
python3.12 scripts/skill_manager.py status --target "$project" --layout codex
~~~

For Claude Code choose `--layout claude` rather than `--layout codex`. The manager refuses to overwrite unmanaged skills and does not edit AGENTS.md/CLAUDE.md.

## Update and verification

Updating Toolkit sources, managed copies, recovery, ChatGPT plugin and MCP follow **different procedures**. [Step-by-step updates](UPDATING.md) · [Codex / Claude Code migration](CLIENT_MIGRATION.md).

Successful `status` verifies files only. Live Codex/Claude Code skill activation and application QA need separate evidence. A macOS CI runner is not a personal Mac.
