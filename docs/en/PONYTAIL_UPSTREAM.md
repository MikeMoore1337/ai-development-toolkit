# Original Ponytail 5.3.2 - opt-in skills

[Русский](../PONYTAIL_UPSTREAM.md) | [Issue #422](https://github.com/MikeMoore1337/ai-development-toolkit/issues/422) | [Official upstream](https://github.com/DietrichGebert/ponytail)

## Provenance and delivery

The six files in `optional-original-skills/{ponytail,ponytail-review,ponytail-audit,ponytail-debt,ponytail-gain,ponytail-help}/SKILL.md` are byte-for-byte **unchanged** files from `DietrichGebert/ponytail`, tag `v5.3.2`, commit `16352ac229eb08a9598dcae48fe9f2b342567d86` (already pinned in `MANIFEST.json`). The unchanged upstream MIT license is `optional-original-skills/PONYTAIL_LICENSE`. `tests/test_public_distribution.py` verifies the original Git blob SHA of all six skill files.

This copy is **not auto-installed**, is not part of any default Toolkit profile, and does not bundle or execute the official plugin lifecycle hooks. It is an official upstream **skill-only fallback**, not proof of client installation or activation.

## Windows owner route (no Codex CLI)

1. Inspect `%USERPROFILE%\.agents\skills\` for existing same-name skills. Never overwrite another source or a pre-existing install.
2. In Windows Explorer copy only the **six Ponytail skill directories** from `optional-original-skills/` into `%USERPROFILE%\.agents\skills\`. Keep the upstream SKILL.md files unchanged.
3. Restart Codex Desktop; manually check whether `ponytail`, `ponytail-review` and `ponytail-audit` are visible/invokable. Until observed, report **HOST_NOT_VERIFIED**.
4. To roll back remove only the six directories copied by step 2, not other installations.

For the **full** plugin (not the skill-only fallback), follow upstream [INSTALL.md](https://github.com/DietrichGebert/ponytail/blob/v5.3.2/INSTALL.md), which documents Codex marketplace commands and lifecycle hooks. This change did **not** execute Codex CLI, Claude CLI, plugin installation, hooks, paid APIs or live model calls. Skill-only copying does not provide automatic session injection or guaranteed mode persistence.

## Authority and isolation

- User/project instructions, `AGENTS.md`, security, tests, permissions and delivery gates override any optional external skill.
- Toolkit's existing `minimal-safe-change` remains intact; do not auto-activate both overlapping skills. Ponytail must be an explicit user choice.
- Never automatically select `ultra`, invoke `ponytail-review`/`ponytail-audit`, add paid dependencies or new review loops.
- Other users can choose upstream-supported clients and install routes; the owner's no-CLI/no-extra-cost policy is not a universal Toolkit restriction.
- Source and CI verification are not native-client L4-L6 evidence.
