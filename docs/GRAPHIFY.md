# Optional upstream Graphify (local code navigation)

Graphify is an **optional external developer tool**, not part of Toolkit runtime,
its installer, the Personal MCP server or any QA profile's required dependencies.
This guide uses the **unmodified upstream** [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify)
(official package `graphifyy`, license Apache-2.0). The source repository's
default branch is `v8`; the release evaluated for this guide is
[`v0.9.97`](https://github.com/Graphify-Labs/graphify/releases/tag/v0.9.97)
(2026-10-27). Recheck the release and advisories before changing the pin.

## Install in an isolated tool environment (opt in)

Install `uv` or `pipx` using your platform's supported package manager. Do not
install Graphify into an application's Python environment:

```sh
uv tool install 'graphifyy==0.9.97'
graphify --version
```

Or: `pipx install 'graphifyy==0.9.97'`.
This first **download/install** needs network access and permission to install
an external CLI; it is never triggered automatically by Toolkit. Version output
and successful execution must be checked on the **actual target machine**.
Python >=3.10 is the upstream minimum; Windows/Python 3.14 and Codex Desktop
need a real smoke test before claiming compatibility.

## Run the unmodified CLI

From the desired repository root, with an explicit and reviewed scan scope:

```sh
graphify extract . --code-only --no-cluster
graphify explain "adt.py"
graphify path "adt.py" "skill_manager.py"
graphify query "what code depends on scripts/adt.py?"
```

The `--code-only` option indexes source using the local tree-sitter AST
without requiring a model, API key or semantic extraction. `--no-cluster`
keeps raw extracted edges; Graphify is never a substitute for source/tests.

**The Toolkit checkout has a native root [`.graphifyignore`](../.graphifyignore)**
with 69 reviewed patterns from [#423](https://github.com/MikeMoore1337/ai-development-toolkit/issues/423)
for `third_party`/vendor, dependencies, caches/build, `.env*`, credentials,
private paths and four local review JSON files. The original Graphify 0.9.97
reads it automatically alongside `.gitignore` on **the first scan of a
fresh checkout**, without any wrapper or extra `--exclude` flags.

The original CLI also **persists explicit `--exclude` flags for later
runs of that same graph** in its generated build config; this is not a
replacement for an ignore file on a fresh checkout. After changing the
corpus rules, run `graphify extract . --code-only --no-cluster --force`
when a complete AST refresh is required.

The approved ignore set deliberately excludes
`scripts/native_eval_capsules.js` because it imports vendor code. This
module will **not** appear in the graph: inspect its source and tests
directly for change-impact analysis. Some graph nodes can have an empty
`source_file`; zero banned path matches do not constitute a complete
secrets audit.

Run only in the intended repository root, never your home directory or a
parent of several repositories. Do not use `--no-gitignore` for ordinary
scans. `graphify-out/` is disposable output excluded from Git; review it
for sensitive data and never publish the graph. Toolkit's ignore rules
apply to **Toolkit only**, not automatically to downstream user projects.
The example `query` may be broad or truncated by its token budget.
Check actual code and tests before acting on `EXTRACTED`/`INFERRED` edges.

## Optional project-scoped Codex skill

Only after the project owner approves and you have checked what the installer
would change, use the **upstream**, not a locally reimplemented skill:

```sh
graphify install --platform codex --project
```

If the original Graphify skill is already available in the current Codex
Desktop session through a user-scoped installation, **reuse it**. Do not
install a second copy. The optional project-scoped command above copies
the original skill under `.codex/skills/graphify/` with packaged references.
Check `git diff`, existing `AGENTS.md`, hooks and owner approval **before**
project changes; never overwrite a user-owned skill.

Do not run the distinct `graphify codex install` path here: it may
modify `AGENTS.md` and Codex hooks. Codex uses `$graphify` rather than
`/graphify`. Do not require Codex CLI. Installation instructions alone
do not prove successful skill discovery or execution.
Toolkit's existing `graphify-adapter` remains the portable, conditional QA
adapter: it does not install or automatically invoke Graphify.

Do **not** enable strict source-read hooks, watch mode, MCP serving, cloud,
cross-repository indexing, semantic extraction, third-party model providers
or background tasks as a consequence of installing Toolkit. Each requires a
separate scope and approval. Existing `AGENTS.md`, Issue gates and source
of truth are authoritative; normal source search is always an allowed
fallback when Graphify is unavailable or stale.

## Update and rollback

```sh
uv tool upgrade graphifyy                 # only after reviewing the release
uv tool install --reinstall 'graphifyy==0.9.97'
uv tool uninstall graphifyy
```

For `pipx`, use its corresponding `upgrade`/`uninstall` commands.
Remove generated `graphify-out/` and any project-scoped skill installation
**only after inspecting the diff**; preserve unrelated local files. No
runtime, CI or production deployment is needed for this optional tool.

**Evidence status (2026-10-29):** [#423](https://github.com/MikeMoore1337/ai-development-toolkit/issues/423)
records an actual Windows/Codex Desktop original-skill and CLI acceptance,
a code-only AST graph and bounded path/category checks. The native
`.graphifyignore` hardening was tracked separately in
[#474](https://github.com/MikeMoore1337/ai-development-toolkit/issues/474).
These observations apply to the tested checkout and scope only; they do
not prove universal client compatibility, full secret absence or token
savings. No background installation or paid providers are enabled.
