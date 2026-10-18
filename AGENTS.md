# Repository instructions

This is a portable collection of AI development skills and reference agent roles.

- Do not mutate third-party repositories, merge PRs or deploy as part of toolkit maintenance.
- Existing task approval gates always take precedence over skills.
- New skills must follow https://agentskills.io/specification (`SKILL.md` frontmatter with correct name and description).
- Keep descriptions concise and trigger-specific; move lengthy references to `references/`.
- Do not add proprietary, personally licensed, private or unverified third-party material.
- Do not collect credentials, tokens or cookies in documentation and test fixtures.
- Update MANIFEST.json, tests and docs for changes to the core.
- Run `python scripts/validate_pack.py` and `python -m unittest discover -s tests -v`.
- Never claim official `skills-ref`, production, or live agent evaluations were run if they were not.
