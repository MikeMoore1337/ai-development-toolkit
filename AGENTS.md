# Repository instructions

This is a portable collection of AI development skills and reference agent roles.

- Do not mutate third-party repositories, merge PRs or deploy as part of toolkit maintenance.
- When this repository is referenced for a task in another user's project, treat **all copies of Toolkit as read-only sources**: never write user reports, generated code, logs, caches, scratch files, test results, branches, commits, or PRs into Toolkit. Work and outputs belong in the user's project, chat, or another user-authorized destination. Only an explicitly authorized task to develop Toolkit itself may change this repository.
- Existing task approval gates always take precedence over skills.
- For a user request to work with Toolkit, the host installs missing task-required skills/tools after source, license, revision and file review, within granted permissions. Prefer user scope and the existing Skill Manager `ensure` preview/apply; preserve existing files. Honor explicit reference-only/no-install requests. If required setup is blocked, report its concrete cause rather than silently substituting reference methods. MCP itself stays read-only; verify files, client discovery and invocation separately.
- New skills must follow https://agentskills.io/specification (`SKILL.md` frontmatter with correct name and description).
- Keep descriptions concise and trigger-specific; move lengthy references to `references/`.
- Do not add proprietary, personally licensed, private or unverified third-party material.
- Do not collect credentials, tokens or cookies in documentation and test fixtures.
- Update MANIFEST.json, tests and docs for changes to the core.
- Run `python scripts/validate_pack.py` and `python -m unittest discover -s tests -v`.
- Never claim official `skills-ref`, production, or live agent evaluations were run if they were not.

- For suggestions drawn from third-party AI/design/QA collections, apply [selective external adoption and evidence gates](docs/EXTERNAL_METHODS_ADOPTION.md) (RU; [English](docs/en/EXTERNAL_METHODS_ADOPTION.md)). Never import entire bundles by default. When a product includes both a user interface and a resident agent service, browser QA must not be conflated with resident-runtime skills.
