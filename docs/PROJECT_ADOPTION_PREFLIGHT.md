# Project adoption preflight (read-only)

[Русская версия](ru/PROJECT_ADOPTION_PREFLIGHT.md) | [Existing adaptation procedure](en/ADAPTATION.md)

A new or existing project must remain the authority on its own business rules, `AGENTS.md`, `CLAUDE.md`, privacy boundaries, visual approvals, and release policy. The Toolkit may **propose** portable profiles; it must not silently rewrite the project, adopt user-owned skills, install from a network, or claim that the client invoked those skills.

## Inspect before installation

From a Toolkit checkout, with Python 3.12+:

```bash
python scripts/project_adoption_preflight.py --target /path/to/project --task qa --layout codex --archetype generic
python scripts/project_adoption_preflight.py --target /path/to/project --task ui --layout claude --archetype generic
```

Use the actual local project path on Windows, Linux or macOS. `--archetype` is **explicitly user-chosen** (`generic` is used in these examples; historical specialized modes remain in the implementation), never detected from private project content. The tool reuses the existing `adt.choose` and `adt.diagnose` functions: it only checks the *existence* of a bounded list of named configuration/policy markers and the existing Skill Manager's owned/unowned status. It never reads `AGENTS.md`, `CLAUDE.md`, application code or vault notes, and never writes into the project.

## Interpret the output

- `READY_FOR_HUMAN_REVIEW`: the local preflight found no immediate filesystem blocker. It is **not** merge, install, user-data access, skill activation or deploy permission.
- `REVIEW_REQUIRED`: user-owned skills or other warnings require human attention. Do not adopt or overwrite unmanaged files.
- `BLOCKED`: missing project, unsafe link, ownership collision, incompatible environment or corrupt manager state. Address the blocker manually.

`client_skill_discovery_L4`, `client_skill_use_L5` and `client_task_benefit_L6` all remain `NOT_TESTED`. A client layout is just a directory convention, not proof Codex or Claude Code exists on the device. ChatGPT plugin deployment is a different integration; it cannot be inferred from a local folder layout.

After examining the **real** policy and specific task, request a non-mutating installation preview with the existing tool:

```bash
python scripts/adt.py profile plan --target /path/to/project --task qa --layout codex
```

`--apply` is permitted only in the separately authorized `init` workflow after reviewing the proposed changes, sources, existing ownership and version. This preflight has **no** apply mode.

## Manual checks for any target project

Review its approved UI contract, data/privacy boundaries, background-agent permissions, change confirmation, release approvals and unmanaged skills **manually**. The `generic` preflight does not certify those policies.

The offline tests use disposable empty, existing, conflicting and linked-marker projects. They prove **source-only safety properties**, not real workflow success in any application or on any user's workstation. Real-client evidence belongs to [#141](https://github.com/MikeMoore1337/ai-development-toolkit/issues/141).
