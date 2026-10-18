# Installing skills safely

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
