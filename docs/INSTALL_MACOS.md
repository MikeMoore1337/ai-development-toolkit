# Install AI Development Toolkit - macOS

[Русский](ru/INSTALL_MACOS.md) · [All platforms](INSTALLATION.md) · [Update guide](UPDATING.md)

## No-terminal route

If you only need guidance in ChatGPT, Claude or an IDE agent, installation is optional: [start here](BEGINNER_START.md). A repository link alone does not activate skills.

## Prerequisites

Requires Git, Python 3.12+, GitHub read access and an **existing** project directory. Install/configure the AI client separately.

Apple Silicon and Intel use identical Toolkit commands. `python` and Apple-provided `python3` may not meet the 3.12+ requirement. Use an approved python.org installer or existing Homebrew. Install Git separately via an approved channel or Apple Command Line Tools when needed.

## Install into an existing project

From the Toolkit directory. Inspect project AGENTS.md / CLAUDE.md and unmanaged skills first:

~~~bash
python3.12 --version
command -v python3.12
git --version
uname -m
git clone https://github.com/MikeMoore1337/ai-development-toolkit.git
cd ai-development-toolkit
project="$HOME/Projects/existing-project"
python3.12 scripts/adt.py profile list
python3.12 scripts/adt.py doctor --target "$project"
python3.12 scripts/skill_manager.py install --target "$project" --layout codex --profile general
# Only after reviewing the preview:
python3.12 scripts/skill_manager.py install --target "$project" --layout codex --profile general --apply
python3.12 scripts/skill_manager.py status --target "$project" --layout codex
~~~

For Claude Code choose `--layout claude` rather than `--layout codex`. The manager refuses to overwrite unmanaged skills and does not edit AGENTS.md/CLAUDE.md.

## Update and verification

Updating Toolkit sources, managed copies, recovery, ChatGPT plugin and MCP follow **different procedures**. [Step-by-step updates](UPDATING.md) · [Codex / Claude Code migration](CLIENT_MIGRATION.md).

Successful `status` verifies files only. Live Codex/Claude Code skill activation and application QA need separate evidence. A macOS CI runner is not a personal Mac.
