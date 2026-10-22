# Client skill installation and migration (offline)

[Русская версия](ru/CLIENT_MIGRATION.md)

This guide covers **file installation**, not guaranteed client activation or skill effectiveness. Commands run from the Toolkit checkout. All targets below are existing, trusted **disposable demo directories**; substitute a project path only after reviewing its own rules and user-owned skills.

## Support matrix

| Client | Project-local skill directory | Toolkit route | Verified claim |
| --- | --- | --- | --- |
| Codex | `.agents/skills/<name>/SKILL.md` | Skill Manager `--layout codex` | Filesystem structure; no live client test |
| Claude Code | `.claude/skills/<name>/SKILL.md` | Skill Manager `--layout claude` | Filesystem structure; no live client test |
| Custom client | Explicit trusted `--skills-dir` | Legacy `install.py` only | Copy only; **no discovery guarantee or manager ownership** |
| Hermes Agent | Documented project-local `.agents/skills/` or `.hermes/skills/` | Existing Codex layout may be relevant | Documentation-level compatibility only; **no Hermes execution or installation tested** |

References: [Codex usage](https://developers.openai.com/blog/skills-agents-sdk), [Claude Code skills](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [Hermes skills](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/skills.md). Always confirm the exact installed client version and project trust/activation policies before relying on discovery. Hermes may modify writable external skills via its skill manager: do not assume that sharing a directory makes it read-only.

## What is supported

| Scenario | Support / limitation |
| --- | --- |
| New Python project (`qa-python`) | Manager install preview / apply / status / update |
| New UI project (`ui-fix`) | Same, with either supported layout |
| Codex to Claude Code, or reverse | Manager **`migrate`** copies all *managed and clean* skills only, preserving source |
| Both clients in one repository | Separate ownership per layout, independent status/update/uninstall/rollback |
| Copy from one arbitrary custom directory to another | Not managed; use legacy installer for fresh unmanaged destinations after review |
| Legacy `install.py` to Manager v2 | **No automatic adoption**; must back up/review and manually clear conflicts |
| Arbitrary unowned user skills | **No automatic migration or adoption** |
| Different installed bytes vs current Toolkit source | **Migration refused** to prevent silent version changes |
| Live client discovery and real model use | **Not tested**; file checks cannot demonstrate this |

The first Manager installation keeps `.adt/skills-lock.json` **schema v1**, irrespective of which layout was installed first. If another layout is installed, its separate v1 lock is `.adt/skills-lock-codex.json` or `.adt/skills-lock-claude.json`. The original lock is never silently repurposed. Both use the existing `.adt/manager.lock` and `.adt/history/` with recovery and rollback by last transaction for each layout. Do not hand-edit or delete lockfiles. Preserve `.adt/` backups outside published source control as appropriate.

For OS-specific prerequisites see [Linux](INSTALL_LINUX.md), [macOS](INSTALL_MACOS.md), [Windows](INSTALL_WINDOWS.md), and [updates](UPDATING.md). The `python` examples below require a separately verified Python 3.12+ interpreter; adjust to `python3.12` on Linux/macOS if necessary.

## Linux/macOS (bash)

```bash
mkdir -p /tmp/adt-cli-python-demo /tmp/adt-cli-ui-demo
python scripts/skill_manager.py catalog
python scripts/skill_manager.py catalog --profile qa-python
python scripts/recommend_profile.py --target /tmp/adt-cli-python-demo --task qa
python scripts/skill_manager.py install --target /tmp/adt-cli-python-demo --layout codex --profile qa-python
python scripts/skill_manager.py install --target /tmp/adt-cli-python-demo --layout codex --profile qa-python --apply
python scripts/skill_manager.py status --target /tmp/adt-cli-python-demo --layout codex

# Copy the exact installed Toolkit-managed skill set to Claude Code.
python scripts/skill_manager.py migrate --target /tmp/adt-cli-python-demo --from-layout codex --layout claude
python scripts/skill_manager.py migrate --target /tmp/adt-cli-python-demo --from-layout codex --layout claude --apply
python scripts/skill_manager.py status --target /tmp/adt-cli-python-demo --layout claude

# Independent update, safe removal and last-transaction undo.
python scripts/skill_manager.py update --target /tmp/adt-cli-python-demo --layout claude
python scripts/skill_manager.py update --target /tmp/adt-cli-python-demo --layout claude --apply
python scripts/skill_manager.py uninstall --target /tmp/adt-cli-python-demo --layout claude --skills api-testing
python scripts/skill_manager.py uninstall --target /tmp/adt-cli-python-demo --layout claude --skills api-testing --apply
python scripts/skill_manager.py rollback --target /tmp/adt-cli-python-demo --layout claude
python scripts/skill_manager.py rollback --target /tmp/adt-cli-python-demo --layout claude --apply

# Separate frontend project, Claude Code only:
python scripts/skill_manager.py install --target /tmp/adt-cli-ui-demo --layout claude --profile ui-fix
python scripts/skill_manager.py install --target /tmp/adt-cli-ui-demo --layout claude --profile ui-fix --apply
```

## Windows PowerShell

```powershell
$project = Join-Path $env:TEMP "adt-cli-python-demo"
New-Item -ItemType Directory -Force -Path $project | Out-Null
py -3 scripts/skill_manager.py catalog --profile qa-python
py -3 scripts/skill_manager.py install --target $project --layout codex --profile qa-python
py -3 scripts/skill_manager.py install --target $project --layout codex --profile qa-python --apply
py -3 scripts/skill_manager.py migrate --target $project --from-layout codex --layout claude
py -3 scripts/skill_manager.py migrate --target $project --from-layout codex --layout claude --apply
py -3 scripts/skill_manager.py status --target $project --layout codex
py -3 scripts/skill_manager.py status --target $project --layout claude
py -3 scripts/skill_manager.py update --target $project --layout claude
py -3 scripts/skill_manager.py recover --target $project
# Run this only if an interrupted transaction is reported:
py -3 scripts/skill_manager.py recover --target $project --apply
```

Reverse migration uses `--from-layout claude --layout codex`; the source is never automatically removed. Migration to an already occupied destination fails intentionally. For custom clients, use `python scripts/install.py --target PATH --skills SKILL --skills-dir ABSOLUTE_DIRECTORY` (dry-run first, then `--apply`). This is a simple non-owned copy and cannot be managed by `migrate`.

## Previews, collisions and failure recovery

- **Never apply without inspecting the preview**: `changes` lists skill directories and `file_diffs` shows modified paths and SHA256 values, not private file contents.
- Any existing/unmanaged or linked destination, path junction, modified owned source or corrupted lockfile is a hard refusal. `AGENTS.md` and `CLAUDE.md` are not changed.
- `status` reports each layout independently. `update` and `uninstall` are dry-run by default. `rollback` reverts the most recent transaction **for the specified layout**; other client state is untouched.
- On interruption, inspect `recover --target PATH` and then explicitly run `recover --target PATH --apply`. Recovery looks at pending transactions for *both layouts* and may refuse ambiguous local modifications requiring manual inspection.
- Do not use a real client or its skill-management commands to conduct these filesystem tests. Existing skills added by `install.py` are **not** treated as Manager-owned. Back them up and compare manually; the Manager refuses conflicting paths.
- A successful copy does not mean the model detected, loaded, used, or benefitted from a skill. Actual client tests are separately gated (Issue #11).
