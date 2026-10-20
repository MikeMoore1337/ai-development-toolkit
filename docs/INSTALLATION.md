# Installing skills safely

## Beginner CLI (Skill Manager v2)

Use the same managed install engine through a smaller entrypoint. Python 3.12+ and an **existing** target project are required. The CLI never downloads or installs an AI client. Run these commands from the Toolkit checkout:

~~~bash
python scripts/adt.py profile list
python scripts/adt.py doctor --target /path/to/repo
python scripts/adt.py profile plan --target /path/to/repo --task qa
python scripts/adt.py init --target /path/to/repo --profile general
python scripts/adt.py init --target /path/to/repo --profile general --apply
python scripts/adt.py status --target /path/to/repo
~~~

On Windows, replace `python` with `py -3` and use a Windows project path. Select `--layout claude` for a Claude Code skills folder; this does **not** confirm that Claude Code is installed or detects skills. All commands except `init --apply` are read-only. Inspect the per-file plan **before** granting `--apply`. A missing project is never created automatically. `doctor` reports damaged state, drift, linked paths, transactions and unmanaged skills without attempting repair; filesystem permissions and client activation can remain NOT_VERIFIED. For a recoverable interruption, preview `python scripts/skill_manager.py recover --target /path/to/repo`; apply recovery only after explicit review. For managed updates and rollback, continue using `skill_manager.py`. A repeat `init` skips already managed clean skills; unrelated unmanaged folders remain untouched. Existing `AGENTS.md` and `CLAUDE.md` are not rewritten.

For technical documentation use `--task docs` (profile `docs-technical`, source verification), for wording only use `--task docs-edit` (`editorial`); `--task docs-verify` requests factual cross-checks. QA selection is heuristic: Python/JavaScript files do not establish that pytest or Playwright are installed. Wide `qa-all` includes 27 QA skills and should normally be replaced with a focused profile; the number of files does not measure model tokens.

[Русская версия](ru/INSTALLATION.md) | [Русский первый запуск](ru/GETTING_STARTED.md)

Client layouts, pinned source evidence and offline verification: [CLIENT_COMPATIBILITY.md](CLIENT_COMPATIBILITY.md).

**New project? Start with Skill Manager v2.** You need Python 3.12+, a clone of this Toolkit and an existing target project. The Toolkit does not install an AI client. Choose a profile with `python scripts/skill_manager.py catalog`, then:

```bash
python scripts/skill_manager.py install --target /path/to/repo --profile qa-core
python scripts/skill_manager.py install --target /path/to/repo --profile qa-core --apply
python scripts/skill_manager.py status --target /path/to/repo
```

The first command previews file-level changes; only `--apply` writes. Review the target project's existing `AGENTS.md`, `CLAUDE.md` and skill folders first; these files are never automatically rewritten. For Claude Code, use `--layout claude` consistently. Manager ownership and backups apply only to its own installations.

**One-time copy without managed updates:** `python scripts/install.py --target /path/to/repo --profile qa-core`, then repeat with `--apply`. This legacy installer is still supported, refuses to overwrite existing skills and allows custom trusted `--skills-dir PATH` destinations. It does **not** create manager ownership or rollback history. Do not assume the Manager can adopt a legacy installation.

**Verify:** use `status` for Manager-owned skills, inspect the copied `SKILL.md`, then separately check whether your installed, configured AI client actually discovers and activates the skill. Copying files, source-format compliance and real client activation are different claims. QA reference roles are documentation, not auto-created agents.

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
`agent`, `backend`, `frontend`, `research`, `provider`. For QA, a Python configuration selects `qa-python`; Python plus
JavaScript selects `qa-fullstack`; JavaScript plus Playwright selects
`qa-ui`. Unknown stacks fall back to `qa-core`.

The output includes a rationale, `read_only: true`, and separate `optional_skills`
and `optional_profiles` suggestions (never installed). For the five curated
areas and size/overlap metrics, see [Curated Skill Packs](CURATED_SKILL_PACKS.md).
Run `python scripts/profile_metrics.py` for file-byte measurements (not model tokens).

The output includes a rationale and `read_only: true`. Every recommendation
is **heuristic** and must be reviewed against local project rules. Use the
recommended Skill Manager for preview and explicit `--apply` after deciding.

## Skill Manager v2 (recommended for managed installs)

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
