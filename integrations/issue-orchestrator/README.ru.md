# Original Issue-Orchestrator - pinned Toolkit pilot (#570)

**State: SOURCE-ONLY / BLOCKED_PROVIDER_COMPATIBILITY. This is NOT an activated integration.**

This directory holds a minimal, declarative evaluation of upstream [issue-orchestrator/issue-orchestrator](https://github.com/issue-orchestrator/issue-orchestrator). It does not implement a second queue, supervisor, reviewer, worktree manager, agent provider or auto-merge.

| Upstream | Pinned baseline |
|---|---|
| Repository | issue-orchestrator/issue-orchestrator |
| Commit | `d4a79824ccd806089cf3f70ec632d39b8ee255ea` |
| Version | `0.10.0` (early beta) |
| License | Apache-2.0; preserve LICENSE/NOTICE and trademark attribution |
| Interface | Supported CLI and YAML configuration; MCP is experimental |

## Verified design fit at the pinned SHA

| Requirement | Upstream assessment |
|---|---|
| GitHub issue discovery, dependencies, scheduler | BUILT IN |
| Worktrees, PR publishing, reconciliation and recovery | BUILT IN |
| Quick/publish validations, independent reviewer role and bounded rework | BUILT IN; configure |
| Pause/resume/restart, dashboard, timeline | BUILT IN |
| WIP=1 | CONFIG: `execution.concurrency.max_concurrent_sessions: 1`; disable reserved tech-lead slots |
| Exact pilot scope (two immutable Issue IDs) | GAP: `filtering.label` is supported; `filtering.issue` takes only one number. Label membership can change after preflight. The JSON scope below is an audit declaration, NOT an enforced runtime allowlist. |
| Codex Python SDK with ChatGPT authentication | BLOCKED: built-in `codex` provider invokes `codex` CLI, not the Python SDK |
| Independent OS credential isolation on owner's Windows host | NOT_VERIFIED; per-agent sandbox is not proof of GitHub secret isolation |
| Autonomous unattended E2E with two new pilot issues | NOT_VERIFIED |
| Merging | HUMAN by default; preserved, with no auto-deploy |

## Files and fixed pilot boundary

- `pilot-0.10.0.yaml` - upstream-formatted configuration candidate, **not installed** in the target repository or loaded automatically.
- `pilot-scope.json` - immutable declaration of approved target `MikeMoore1337/adt-orchestrator-pilot`, branch `main`, Issues `#7` and `#8`, label `adt-io570-pilot-20261109`.
- GitHub Issues [#7](https://github.com/MikeMoore1337/adt-orchestrator-pilot/issues/7) and [#8](https://github.com/MikeMoore1337/adt-orchestrator-pilot/issues/8) were newly created for this pilot. The second has upstream-native `Depends-on: #7`.

Do not treat `filtering.max_to_start: 2` as an immutable allowlist: it limits launches, not which issues qualify. A third issue labelled with the pilot label could become eligible. **Do not start the original engine unless that gap is closed by an upstream-supported mechanism or specifically accepted after a verified hard safety gate.** Check both labels and exact IDs against GitHub immediately before any eventual activation.

## Critical provider blocker

At upstream `d4a79824ccd806089cf3f70ec632d39b8ee255ea`:

1. `src/issue_orchestrator/execution/agent_runner_providers/__init__.py` registers `claude-code`, `codex` and `deepseek`.
2. `.../codex.py` uses `executable = "codex"` and probes `codex login status`. Its commands launch Codex CLI.
3. The public plugin entry point `issue_orchestrator.ai_provider_keys` supplies API-key metadata, not a pluggable Python SDK execution backend.
4. `agents[].command` is a documented override, but provider-less custom commands reject `sandbox: true`; simply launching an SDK script does not preserve the provider readiness, authentication, sandbox, interactive review and credential gates.

The owner's installed `openai-codex==0.167.0` SDK reportedly returned `AUTH_TYPE=chatgpt` on Windows. This is owner-reported authentication evidence, **not** SDK compatibility with upstream, subscription cost verification or an isolated coding agent. No model has been launched here.

**Disposition: `BLOCKED_PROVIDER_COMPATIBILITY`.** Do NOT invoke Codex CLI or Claude CLI, install paid providers, silently switch to an API key, create a VM/new Windows user, or enable the legacy Toolkit supervisor.

Acceptable next decisions are limited to (a) upstream maintaining a documented, security-reviewed SDK provider interface, (b) separately and explicitly authorizing Codex CLI after runtime, auth, security and subscription checks, or (c) verifying another upstream-supported, policy-compliant coding provider. No alternative has yet been authorized.

## Later activation procedure - NOT performed

1. Inspect the pinned upstream tree, LICENSE, NOTICE, lockfile, dependencies and actual target host. No auto-download or global installation. Confirm the exact Git HEAD `d4a79824ccd806089cf3f70ec632d39b8ee255ea`.
2. Resolve provider compatibility and credential isolation first; record an explicit owner authorization. The source-only candidate is NOT permission to use Codex CLI.
3. Reconcile the pilot `AGENTS.md` (currently documents the legacy Toolkit controller) and supply the upstream-managed agent prompts and guardrails via the upstream `setup` workflow. Review every proposed change before applying it.
4. Verify that `main` and the exclusive scope label still refer to only Issues #7 and #8. Scope must be fail-closed before runtime and remain guarded against late membership changes.
5. After the above gates, follow supported upstream `issue-orchestrator setup`, `setup-guardrails`, `init`, `doctor`, `start`, `pause`, `resume`, `status` and `restart` interfaces as appropriate, using the version-pinned configuration. None was executed in this chat.
6. Observe one real coding session at a time; independent reviewer, bounded rework, PR, exact-head CI, human merge, GitHub Issue closure, post-merge CI, automatic move to #8 and restart/reconciliation. Do not claim success from an empty runnable queue.

The source-only Toolkit tests validate the declared configuration and fail-closed statuses, **not** upstream `doctor`, live GitHub label invariants, security isolation, agent execution or the required E2E.

## Related legacy modules

`scripts/issue_orchestrator.py`, `scripts/issue_supervisor.py` and `scripts/issue_supervisor_sdk.py` are legacy/source-only reference material from previous experiments. They are not activated, removed, imported or wired to this upstream integration. Do not run two queue controllers.

Sources: pinned [configuration](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/configuration.md), [quickstart](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/quickstart.md), [stability](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/stability.md), [FAQ dependencies](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/faq.md), and [GitHub permissions](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/github-permissions.md).
