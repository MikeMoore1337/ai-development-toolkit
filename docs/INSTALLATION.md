# Installing skills safely

Client layouts, pinned source evidence and offline verification: [CLIENT_COMPATIBILITY.md](CLIENT_COMPATIBILITY.md).

1. Prepare the target repository and note its existing `AGENTS.md` / `CLAUDE.md`. The toolkit never overwrites them.
2. Preview a profile:

   ```bash
   python scripts/install.py --target /path/to/repo --profile qa-core
   ```

3. Review all `DRY-RUN` lines, then apply explicitly with `--apply`. No hidden downloads or local execution of bundled skill code occurs.
4. Read the actual installed `SKILL.md` and verify that your agent client discovers it. Paths vary by version and configuration.
5. Run relevant project checks. Installing an instruction is not proof of its benefit.

Example `--layout claude` installs to `.claude/skills`; `--skills-dir PATH` sets the destination directly (trusted local paths only). Unknown names and duplicate destination skill names fail before applying. QA roles are documentation; they do not auto-create agents.

**When moving to a public repository:** run validation and publication checks; review `extensions/qa/SOURCE_MAPPING.md`, licenses and all credential-like strings.


## Optional read-only profile recommendation

The toolkit can suggest a profile from an explicit task and limited, well-known
project configuration file names. It **does not** inspect private source text,
contact any service, install a skill or decide release permissions.

```bash
python scripts/recommend_profile.py --target /path/to/repo --task qa
python scripts/recommend_profile.py --target /path/to/repo --task feature
```

Supported tasks: `feature`, `ui`, `qa`, `ci`, `release`, `docs`,
`agent`. For QA, a Python configuration selects `qa-python`; Python plus
JavaScript selects `qa-fullstack`; JavaScript plus Playwright selects
`qa-ui`. Unknown stacks fall back to `qa-core`.

The output includes a rationale and `read_only: true`. Every recommendation
is **heuristic** and must be reviewed against local project rules. Use the
existing installer for preview and explicit `--apply` after deciding.

## Skill Manager v2 (opt-in)

The existing `install.py` remains supported for simple one-time copies. The
new `skill_manager.py` maintains an **ownership lockfile** and local history
only for skills installed with the manager. It never adopts or overwrites an
unmanaged skill or edits `AGENTS.md` / `CLAUDE.md`.

```powershell
$project = "D:\Work\example-project"

# All modifying operations PREVIEW changes by default:
py -3 scripts/skill_manager.py install --target $project --profile qa-python
py -3 scripts/skill_manager.py install --target $project --profile qa-python --apply
py -3 scripts/skill_manager.py status --target $project
py -3 scripts/skill_manager.py update --target $project
py -3 scripts/skill_manager.py update --target $project --apply
py -3 scripts/skill_manager.py uninstall --target $project --skills api-testing
py -3 scripts/skill_manager.py uninstall --target $project --skills api-testing --apply
# Restore the most recent managed transaction:
py -3 scripts/skill_manager.py rollback --target $project
py -3 scripts/skill_manager.py rollback --target $project --apply
# If a process was interrupted, inspect and recover:
py -3 scripts/skill_manager.py recover --target $project
py -3 scripts/skill_manager.py recover --target $project --apply
```

The manager stores the first client's schema-v1 lock in `.adt/skills-lock.json`.
For a second client it uses the independently owned
`.adt/skills-lock-codex.json` or `.adt/skills-lock-claude.json`. Shared
`.adt/manager.lock` and transaction snapshots in `.adt/history/` remain
**inside the target project**.
Backups may include copies of installed skill files: exclude `.adt/` from
commits where appropriate. The manager does not edit `.gitignore` automatically.

**Safety:** lockfile-only ownership, content drift checks, read-only previews,
exclusive process locking, staged replacement, interruption recovery, no
hidden network downloads. Locally modified owned skills block mutation.

Existing skills installed with the original `install.py` are not adopted.
Back up and manually migrate them only after reviewing their contents, then
install through the manager into free destinations. Do not delete user changes
just to make a manager command pass.

### File-level previews

Every modifying preview now reports `file_diffs` with added, modified and
deleted relative file names and before/after SHA256 values. These are local
byte comparisons; they do not reveal file contents or bypass the ownership
lock. Review this list before supplying `--apply`. A clean, unchanged update
reports an empty change set. When a file contains local modifications outside
the recorded lockfile digest, the operation stops rather than overwriting it.

### Discover profiles and copy managed skills between clients

```bash
python scripts/skill_manager.py catalog
python scripts/skill_manager.py catalog --profile qa-python
python scripts/skill_manager.py migrate --target /path/to/repo --from-layout codex --layout claude
python scripts/skill_manager.py migrate --target /path/to/repo --from-layout codex --layout claude --apply
python scripts/skill_manager.py status --target /path/to/repo --layout claude
```

Migrate **copies**, never removes, the clean, Manager-owned source skills,
with exact SHA256 match to the current Toolkit source. It refuses collisions,
drift, legacy/unmanaged folders and different source bytes. `status`,
`update`, `uninstall` and `rollback` use `--layout` to select the
independent client; `recover` handles pending transactions across both.

See [full Windows/Linux migration scenarios and limitations](CLIENT_MIGRATION.md).
File installation alone is not proof of client discovery, model activation or
effectiveness. For arbitrary custom `--skills-dir` locations continue to use
legacy `install.py`; Skill Manager does not claim ownership of them.
