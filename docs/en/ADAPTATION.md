# Adapting the Toolkit to a new project

[Русский оригинал](../ADAPTATION.md) | [Language policy](../LANGUAGE_POLICY.md)

Here, **universal** means that the underlying methods are portable; it does not mean every rule is automatically applicable.

1. Inspect the actual project's `AGENTS.md`, `README.md`, CI, package manager and test configuration. Fill out `profiles/project-profile.example.json` with **verified project facts** in the target project.
2. Start with a minimal set of core skills: `task-scoping`, `implementation`, `qa-strategy`, `code-review`, `research-verification`. Add other skills only if the task needs them.
3. Add project-specific skills from the **original** package only after checking language, license, links, environment and prerequisites.
4. Do not blindly copy project-specific `AGENTS product app.md`, `AGENTS knowledge base.md`, `origin/master`, a fixed Python version or hardcoded CI job names.
5. Prefer managed installation with `scripts/skill_manager.py` (preview by default, explicit `--apply` after review). `scripts/install.py` is still available for one-time copying. Neither should replace `AGENTS.md` or user-owned skills.
6. Run `python scripts/validate_pack.py`, a selection of relevant scenarios and an independent check of a **real task in the target repository** when permitted.

| Project type | Starting point | Never assume |
| --- | --- | --- |
| Python backend | task-scoping, implementation, qa-strategy | Fixed Python version, pytest, FastAPI or GitHub |
| Frontend/mobile | implementation, qa-strategy, code-review | React, Telegram or browser tests |
| CLI/library | implementation, code-review, documentation-maintenance | Production deployment, HTTP or a UI |
| Data/ML | research-verification, architecture-decisions, qa-strategy | Handling personal data, LLM APIs or GPUs |
| Documentation/content | research-verification, documentation-maintenance | Git branches, releases or even application source code |

Project-specific roles, skills and external tools are installed separately. For other agent clients, first check whether they discover skills in `.agents/skills` and how they interpret instructions.

## Review external tools before adding them

Use [external-skill-review](../../.agents/skills/external-skill-review/SKILL.md) before adopting third-party skills, MCP servers or local tools. Look for an existing equivalent in code, established skills, official client tools and open project issues. If no verifiable gap exists, leave the tool **optional and uninstalled**.

Claims of time or token savings require comparable actual tasks and measurements, not marketing percentages. Browser tools require careful assessment of profiles, authorization and write access. MCP and automation integrations require scrutiny of permissions, external calls and irreversible actions. Researching an option is **not permission** to install it, access private data, publish, merge or deploy.

## Managing Codex and Claude Code in the same project

Use `scripts/skill_manager.py` for managed skills: `catalog --profile qa-python`, a no-write preview, explicit `--apply` and independent `status --layout codex` / `status --layout claude`. `migrate` copies identical **managed** skills between supported layouts without removing source files. User-created or legacy skills are not adopted or moved automatically.

For exact commands on Windows/Linux, lockfile details and recovery see [client migration](../CLIENT_MIGRATION.md). A copied skill file does **not** prove the target client discovered or used it.

## Tool permissions

The [optional tool integration contracts](../TOOL_INTEGRATIONS.md) (Issue #69) distinguish client capability, connection, exact operation/resource approval, network egress, zero-spend policy and execution evidence. Prefer native functions and a chat-only fallback. Never treat read-only approval as write, publish or deploy permission.
