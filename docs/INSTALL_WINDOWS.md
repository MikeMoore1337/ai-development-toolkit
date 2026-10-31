# Install AI Development Toolkit - Windows

[Русский](ru/INSTALL_WINDOWS.md) · [All platforms](INSTALLATION.md) · [Update guide](UPDATING.md)

## No-terminal route

If you only need guidance in ChatGPT, Claude or an IDE agent, installation is optional: [start here](BEGINNER_START.md). A repository link alone does not activate skills.

## Prerequisites

First [choose your client and interface](INSTALLATION.md). The commands below prepare native skill files: `--layout codex` works for Codex Desktop/CLI and documented clients sharing `.agents/skills`; `--layout claude` works for Claude Code Desktop/CLI. They do not install an AI application, MCP or a hosted chat plugin. Cline/Kiro use the separate custom-folder route in that guide.

Requires Git, Python 3.12+, GitHub read access and an **existing** project directory. Install/configure the AI client separately.

Install Python 3.12+ and Git through an approved method. `py -3.12` requires Python 3.12; replace the version for a separately installed 3.13/3.14. Toolkit itself needs no administrator privileges.

## Install into an existing project

**Before running the commands:** set `$project` to the path of an **existing** project directory; the shown path is an example, not a folder Toolkit creates. Every `py -3.12` command assumes Python 3.12 is installed. If you have 3.13 or 3.14 instead, replace **all** occurrences with `py -3.13` or `py -3.14`. Use `py -0p` to list installed versions.

From the Toolkit directory. Inspect project AGENTS.md / CLAUDE.md and unmanaged skills first:

~~~powershell
py -3.12 --version
git --version
git clone https://github.com/MikeMoore1337/ai-development-toolkit.git
Set-Location ai-development-toolkit
$project = Join-Path $HOME "Projects\existing-project"
py -3.12 scripts/adt.py profile list
py -3.12 scripts/adt.py doctor --target $project
py -3.12 scripts/skill_manager.py install --target $project --layout codex --profile general
~~~

**Stop after the preview.** Check the destination, file list and conflicts before running the following apply and status commands separately:

~~~powershell
py -3.12 scripts/skill_manager.py install --target $project --layout codex --profile general --apply
py -3.12 scripts/skill_manager.py status --target $project --layout codex
~~~

For Claude Code choose `--layout claude` rather than `--layout codex`. The manager refuses to overwrite unmanaged skills and does not edit AGENTS.md/CLAUDE.md.

## Update and verification

Updating Toolkit sources, managed copies, recovery, ChatGPT plugin and MCP follow **different procedures**. [Step-by-step updates](UPDATING.md) · [Codex / Claude Code migration](CLIENT_MIGRATION.md).

Successful `status` verifies files only. Live Codex/Claude Code skill activation and application QA need separate evidence. A macOS CI runner is not a personal Mac.
