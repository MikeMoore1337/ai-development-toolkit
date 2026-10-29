# Original Harness² (optional upstream installation)

This installs the **unmodified** [google-research/harness2](https://github.com/google-research/harness2) source at `1cfe254e8d25b15f37048c3730134686abe60335` (upstream package `0.1.0`, Apache-2.0). The Toolkit does **not** contain or rewrite Harness²'s Propose–Probe–Compose engine, evaluators, runners, prompts, skills or agent substrate.

## Install and verify

Use **Linux**, or **Ubuntu in WSL2** on Windows, with `python3.12`, Git, internet access for GitHub/PyPI, and an unprivileged account. The upstream does not support Toolkit's Windows Python 3.14 as its benchmark runtime.

```bash
# Explicit opt-in: this downloads and installs original third-party Python code.
bash integrations/harness2/install.sh install
bash integrations/harness2/install.sh status
```

This installs in `~/.local/share/ai-development-toolkit/harness2-1cfe254e8d25b15f37048c3730134686abe60335/`. The checkout is pinned; no project files, AGENTS.md, Toolkit MCP, Codex Desktop configuration, or global Python packages are altered.

The installer **does not** run `harness2-demo`, models, benchmarks, Codex CLI or Claude CLI. It does not download optional benchmark datasets. The installation alone is not evidence of agent execution or model quality.

## Run official upstream commands, not a Toolkit clone of the engine

After successful installation, execute the **original upstream** entry points from its source checkout (example commands for the supported LAB benchmark):

```bash
source="$HOME/.local/share/ai-development-toolkit/harness2-1cfe254e8d25b15f37048c3730134686abe60335/source"
bin="$HOME/.local/share/ai-development-toolkit/harness2-1cfe254e8d25b15f37048c3730134686abe60335/.venv/bin"
cd "$source"
"$bin/harness2-setup" lab --dry-run
# After reviewing benchmark downloads, authentication and provider costs:
# "$bin/harness2-setup" lab
# "$bin/harness2-check" --bench lab
# "$bin/harness2" --bench lab --k 1 --mode parallel --only-domains antitrust-competition --max-tasks 1
# "$bin/harness2-judge" --bench lab --k 1 --mode parallel
# "$bin/harness2-report" --bench lab --k 1 --mode parallel
```

The commented commands are **not authorized by installation**. Upstream supports JobBench, LAB and WorkBuddy-Bench only, with its own OpenCode/Codex substrates. Its Codex executor uses CLI and **disables its sandbox**; it is **not** Codex Desktop integration. Model-backed runs may charge API fees; no owner run is permitted while the owner's zero-additional-cost and no-Codex/Claude-CLI restrictions apply. Other Toolkit users can separately authorize and execute native upstream workflows in a properly isolated environment under their own policies. No model access, sandbox isolation or billable usage is verified by this integration.

To inspect or remove the pinned installation:

```bash
bash integrations/harness2/install.sh status
bash integrations/harness2/install.sh remove --confirm
```

Removal deletes only the exact marked installation directory after checkout/SHA/origin verification. It never deletes upstream output stored outside that directory. On an interrupted install, inspect the partial directory yourself before cleaning up; do not rerun installer with elevated privileges.

## Readiness and validation

`status` validates marker, original Git origin, pinned revision, CLI executable and installed Python package. This is a **local installation check**, not a real model benchmark or proof of Codex Desktop activation. For running live benchmarks, follow the [official setup](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/SETUP.md), [benchmarks](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/BENCHMARKS.md) and [experiment safety guidance](https://github.com/google-research/harness2/blob/1cfe254e8d25b15f37048c3730134686abe60335/docs/EXPERIMENTS.md) without bypassing any user policy. Upstream setup downloads its dependencies and some datasets with separate licences. Treat the pinned Git commit as source identity, not a cryptographic publisher signature.

This integration is an **external optional developer tool**, not a new Toolkit skill, evaluation engine or registered Personal MCP tool.

## Complete opt-in native CLI (no model execution)

The installed original CLI is available through a thin Toolkit entry point, which **does not reimplement** any upstream runner, task evaluator or judge. Commands execute in the pinned source directory, not in the Toolkit or an application checkout:

```bash
bash integrations/harness2/cli.sh status
bash integrations/harness2/cli.sh setup-preview lab
# Only after checking upstream dependencies, licences and available disk/network:
# bash integrations/harness2/cli.sh setup lab --confirm-network-downloads
bash integrations/harness2/cli.sh check lab
bash integrations/harness2/cli.sh run-preview lab
bash integrations/harness2/cli.sh artifacts
# After a separately authorized genuine judged upstream run exists:
# bash integrations/harness2/cli.sh report lab
```

`setup-preview` and `run-preview` invoke the official `--dry-run` flags.
The explicit `setup` action downloads and executes upstream benchmark dependencies;
it does **not** invoke a model but can have supply-chain, licence, disk and network
implications. `check` is upstream's own readiness check; **failure is expected**
until the benchmark tools, data and authorized model credentials are installed.
`report` will also correctly fail if there are no original `judged.json` rows.
`artifacts` lists only original judged file names, not raw logs.

**The bridge never permits `harness2` model runs or `harness2-judge`.** Those
native upstream entry points remain installed for **other users** who explicitly
authorize model spending and configure a separate, properly isolated machine.
The owner's zero-spend and no-Codex/Claude-CLI constraints still prohibit them.
Codex Desktop cannot be substituted for the upstream Codex CLI substrate.

The independent no-model CI smoke workflow checks a real upstream editable
installation in an ephemeral Linux runner with no model credentials, official
CLI help, official setup preview and fail-closed checks. It is **not** proof of
a configured benchmark, a model result or a Windows WSL2 installation.


**Artifact-root compatibility:** `artifacts` uses upstream's actual `HARNESS2_RUNS_DIR` (default `source/runs`) rather than a fixed location. Its read-only listing stays inside the current user's home and lists only `judged.json` filenames, never file contents. Out-of-home paths are rejected.
