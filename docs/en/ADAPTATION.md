# Adapting Toolkit to a new project

[Русский оригинал](../ADAPTATION.md) | [English installation guide](../INSTALLATION.md) | [Language policy](../LANGUAGE_POLICY.md)

Here, *universal* means the underlying methods are portable; **it does not mean that every rule applies to every project automatically**.

1. Find the actual project's `AGENTS.md`, `README.md`, CI configuration, package manager and test configuration. Fill out `profiles/project-profile.example.json` with verified project-specific facts.
2. Start with the smallest relevant Core set (`task-scoping`, `implementation`, `qa-strategy`, `code-review`, `research-verification`). Add others only when the task needs them.
3. Where needed, import a particular specialized skill from the **original** archive only after separately reviewing language, license, links, runtime and dependencies.
4. Never blindly copy project-specific `AGENTS product app.md` or `AGENTS knowledge base.md`, a hardcoded `origin/master`, a Python runtime version, or fixed CI job names.
5. For managed installation use `scripts/skill_manager.py` (preview by default; `--apply` after review); for a one-time copy use `scripts/install.py`. Neither changes project `AGENTS.md` or other people's skills.
6. Execute `python scripts/validate_pack.py`, relevant scenario checks, and an independent test of an actual task in the target repository.

| Project | Suggested starting skills | Do not assume |
| --- | --- | --- |
| Python backend | task-scoping, implementation, qa-strategy | Python version, pytest, FastAPI, GitHub |
| Frontend/mobile | implementation, qa-strategy, code-review | React, Telegram, browser tests |
| CLI/library | implementation, code-review, documentation-maintenance | Production deploy, HTTP, UI |
| Data/ML | research-verification, architecture-decisions, qa-strategy | Personal-data storage, LLM API, GPU |
| Documentation/content | research-verification, documentation-maintenance | Branches, releases, or even source code |

Project-specific roles, skills and external tools must be installed separately. Other agent environments require verification of their `.agents/skills` discovery mechanism and their actual instructions.

## Reviewing third-party tools before installation

Before adding an external skill, MCP server or local utility, apply [`external-skill-review`](../../.agents/skills/external-skill-review/SKILL.md).

Look first for an existing equivalent in source code, existing skills, official client tools and current project tasks. If a gap is not proven, keep the tool optional and **do not install it**.

For claims about token savings or faster execution, compare real tasks and measured results rather than advertising percentages. For browser tools, separately review user profile isolation, authentication and write permissions. For MCP and automations, review privileges, network requests and consequences. Researching a tool **does not authorize** installation, access to private data, publishing, merging or production deployment.

## Supporting Codex and Claude Code in one repository

For managed installations, prefer `scripts/skill_manager.py`: select a profile (`catalog --profile qa-python`), inspect the dry-run, explicitly provide `--apply`, and check separately with `status --layout codex` or `status --layout claude`. The `migrate` command **copies** verified, manager-owned skills between these two layouts and leaves the originals intact. User-owned or legacy skills are neither automatically transferred nor adopted.

For exact Windows/Linux commands, lockfile format and recovery, see [client migration](../CLIENT_MIGRATION.md). The presence of an installed file **does not prove that a particular AI client actually used the skill**.
