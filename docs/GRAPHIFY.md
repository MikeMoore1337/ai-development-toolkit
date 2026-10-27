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
graphify extract . --code-only
graphify query "what calls the authentication handler?"
graphify explain "AuthenticationService"
graphify path "EntryPoint" "TargetService"
```

The `--code-only` option indexes source code using local tree-sitter AST
without requiring a model, API key or semantic extraction. It does not
promise that every dependency is resolved correctly. Before scanning, check
the upstream ignore behavior and your repository's `.gitignore`, and ensure
that secrets, `.env*`, generated directories, private notes and adjacent
repositories are not in scope. **Never** pass `--no-gitignore` for an ordinary
project scan. `graphify-out/` is derived disposable output: ignore it in
Git, inspect it for sensitive data, and delete it after use as appropriate.
Check current code and tests before acting on `EXTRACTED`/`INFERRED` edges.

## Optional project-scoped Codex skill

Only after the project owner approves and you have checked what the installer
would change, use the **upstream**, not a locally reimplemented skill:

```sh
graphify install --platform codex --project
```

Upstream may write `.agents/skills/graphify/` and supporting references.
Inspect `git diff`, existing `AGENTS.md`, skills, hooks and the repo's
approval/security rules before committing or enabling anything. Codex uses
`$graphify` rather than `/graphify`; **Codex Desktop operation is not
attested** merely by adding these instructions. Do not require Codex CLI.
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

**Evidence status (2026-10-27):** upstream source and CLI syntax were
inspected; no real Toolkit graph build or Codex Desktop activation was
observed in the session that authored this document. Do not mark live
installation or token savings as verified without reproducible evidence.
