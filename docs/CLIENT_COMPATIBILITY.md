# AI client compatibility: offline contracts

Reviewed: **2026-10-19**. Machine-readable evidence: [compatibility/clients.json](../compatibility/clients.json), schema v1. The checks cover **contracts and filesystem structure**, not a real AI-client execution. Installed versions, trust decisions and configuration may change behavior.

## Levels and boundaries

| Level | Evidence | Status in this issue |
| --- | --- | --- |
| L1 | Agent Skills specification and SKILL.md validation | Internal validator + pinned official skills-ref in CI |
| L2 | Safe copy and filesystem layout | Existing Skill Manager v2 plus new synthetic client/project fixtures |
| L3 | Official source / documentation contract | Source references below reviewed on date above |
| L4 | Actual client discovered installed skill | **NOT_TESTED** |
| L5 | Client/model read and used skill | **NOT_TESTED**; Issue #11 |
| L6 | Benefit vs no-skill baseline | **NOT_TESTED**; Issue #11 |

A level marked VERIFIED only verifies **that level**, not overall client compatibility. PARTIAL, NOT_TESTED, UNSUPPORTED and UNKNOWN have different meanings. A successful copy does not prove discovery or effectiveness.

## Client matrix

| Client | Project-local layout | Global / external | L1 | L2 | L3 | L4-L6 |
| --- | --- | --- | --- | --- | --- | --- |
| Codex | .agents/skills | $HOME/.agents/skills, /etc/codex/skills and repo ancestors | VERIFIED | VERIFIED | VERIFIED (docs) | NOT_TESTED |
| Claude Code | .claude/skills | ~/.claude/skills and client-managed plugins | VERIFIED | VERIFIED | VERIFIED (docs) | NOT_TESTED |
| Hermes Agent | .agents/skills or .hermes/skills, under a Git repository | ~/.hermes/skills, configured external_dirs and create_dir | VERIFIED | PARTIAL | VERIFIED (pinned docs) | NOT_TESTED |

**Official sources and versions (reviewed 2026-10-19):**

- [Agent Skills specification](https://agentskills.io/specification): mandatory name and description, optional license, compatibility, metadata, allowed-tools, and optional resource directories. The Toolkit enforces the portable subset.
- [OpenAI Codex build-skills guide](https://learn.chatgpt.com/docs/build-skills), live documentation reviewed 2026-10-19: repository ancestor .agents/skills directories, user and admin paths, optional client-only agents/openai.yaml. Codex can follow symlinked skill folders and may display duplicate names. **Toolkit intentionally forbids linked paths** for safe managed copies.
- [Claude Code skills documentation](https://code.claude.com/docs/en/skills), live documentation reviewed 2026-10-19: .claude/skills, global paths, per-skill activation controls. Claude Code-specific frontmatter (for example context or disable-model-invocation) is not part of the portable Agent Skills schema. Toolkit does not silently add these fields; it also never edits CLAUDE.md.
- [NousResearch/hermes-agent Skills System, exact SHA 2e83e2a935ee04f606aab58e498d34ca58d84c07](https://github.com/NousResearch/hermes-agent/blob/2e83e2a935ee04f606aab58e498d34ca58d84c07/website/docs/user-guide/features/skills.md), inspected read-only. Project-local skills require a trusted Git project, undergo scanning/quarantine, and take priority over local/profile and external skills. Hermes skill_manage can modify writable external skill directories. No Hermes code was executed/imported and no VPS was used.

Client discovery/activation depends on client policy, user configuration, Git project trust (Hermes) and security scanning; L4-L6 are deliberately unmeasured. The registry distinguishes standard metadata from client-specific extensions. A documentation contract is not a guarantee of a future client release.

## Offline usage

Registry check (CI runs this on Windows and Linux):

    python scripts/verify_client_compatibility.py

Check installed skills in an **existing disposable project** without modifying it:

    python scripts/verify_client_compatibility.py --project /tmp/demo --client codex --skills qa-strategy
    python scripts/verify_client_compatibility.py --project /tmp/demo --client claude-code --skills qa-strategy
    python scripts/verify_client_compatibility.py --project /tmp/demo --client hermes --layout .agents/skills --skills qa-strategy

These verify explicit layouts, required SKILL.md, frontmatter via existing Toolkit code, existing referenced Markdown files, link confinement, symlink/junction rejection, and nested-file safety. They do not install skills, parse every possible Markdown construct, analyze script contents, download sources, contact AI APIs or discover skills using a live client. Scripts in a skill are never executed.

The integration suite uses the **existing** Skill Manager v2 to install the qa-python profile into disposable projects, migrate Codex to Claude Code, verify byte-for-byte copied skill tree hashes, and preserve AGENTS.md and CLAUDE.md. Ownership isolation, idempotence, rollback, collision and recovery are already covered more broadly in [CLIENT_MIGRATION.md](CLIENT_MIGRATION.md) and existing manager tests. No second manager was built.

## Hermes-specific boundaries

Only the project-level .agents/skills / .hermes/skills tree can be checked offline. No dedicated Hermes installer, Skill Manager support, global-scoped management or migration is provided: registry statuses are UNSUPPORTED. The Codex project layout overlapping with Hermes is not enough to prove Hermes discovery. Real Hermes requires project trust; writable external skills are not protected merely by their location. Use OS-level read-only permissions for shared files when necessary. No adapter is warranted without a demonstrated incompatible contract.

## CI and revalidation

The existing hosted Linux/Windows CI invokes the offline registry gate along with quality, ownership tests, provenance and SHA256 validation. The pinned upstream skills-ref reference check remains separate. No new dependency, external runner, network-dependent source fetch or model request is introduced.

When client documentation changes, review official sources again, update the review date and pinned source revision as necessary, and adapt checks and tests. L4-L6 evidence remains subject to the separately gated real-agent Issue #11.
