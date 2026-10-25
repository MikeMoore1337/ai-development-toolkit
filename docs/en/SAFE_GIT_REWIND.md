# Selective Git rewind - safe alternative to Claude Code Rewind

Toolkit [Issue #372](https://github.com/MikeMoore1337/ai-development-toolkit/issues/372). This is an **explicit, local, commit-based** fallback with no Claude hooks, agent daemon, API keys, paid inference, chat capture or implicit writes. It is **not** per-action Claude Code history, a complete Rewind implementation, or a fork.

## Upstream adoption decision

Reviewed `holasoymalva/claude-code-rewind@d421d069384ab3349d7e798d72b3794628559b86`:

- README advertises MIT and automatic capture; no root `LICENSE` exists in the inspected repository, while `pyproject.toml` only declares MIT as metadata. A complete redistribution license was not verified.
- `claude_rewind/hooks/` contains only `__init__.py`; automatic hook registration is not demonstrated by the inspected source tree.
- `claude_rewind/core/rollback_engine.py` combines snapshot-derived paths with `self.project_root / file_path` before writes/deletions without an immediately visible mandatory root-confinement check. Traversal/symlink adversarial tests are required before trusting the original writer.
- Advertised performance improvements have not been independently verified.

**Decision:** direct upstream runtime adoption is `NO_GO`. Reuse Git rather than adding a second version-history database.

## Usage

Requires Python 3.12+ and Git. From the Toolkit checkout, targeting an isolated test checkout:

```sh
python scripts/safe_git_rewind.py --repo /path/to/project timeline --count 10
python scripts/safe_git_rewind.py --repo /path/to/project preview --commit <full-40-char-sha> --file src/example.py
```

The preview reports the exact current HEAD, blob identities and diff without writing. Explicitly confirm a **single tracked regular file** only after reviewing the preview:

```sh
python scripts/safe_git_rewind.py --repo /path/to/project apply --commit <full-40-char-sha> --file src/example.py --expect-head <current-head-sha> --confirm
```

The adapter rejects partial revisions, stale HEAD, staged or unstaged modifications to the selected file, missing/untracked files, symlinks/junctions, noncanonical paths, `.git` and paths outside the checkout. Apply modifies worktree only, not index/history; previous content remains in Git at HEAD. A checked manual undo is `git restore --source=HEAD --worktree -- src/example.py`.

Limits: only Git commits, not individual agent actions. No untracked/deleted/conflicting file restoration, no silent conflict resolution, and no protection against another process writing **between** the last preflight and `git restore`. Use only on a controlled checkout, not production. No original Rewind install or personal Codex/Claude client execution was performed.

Offline tests: `python -m unittest discover -s tests -p test_safe_git_rewind.py -v`. No paid model/CLI calls or network dependencies. Adapter source release requires successful PR and post-merge CI.
