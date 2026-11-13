# Original Issue-Orchestrator - pinned Toolkit pilot (#570)

**State: SOURCE TEMPLATE ONLY / PHYSICAL WSL2 PILOT OBSERVED / FULL UNATTENDED E2E NOT_VERIFIED. This Toolkit template itself is not an activated engine.**

> **Текущий результат (13.11.2026).** Оригинальный Issue-Orchestrator v0.10.0 запускался в WSL2 с Codex CLI через вход ChatGPT. Одна очередь (WIP=1) последовательно выполнила тестовые Issues #7 и #8: PR #15 и #17 слиты, post-merge CI прошёл. PR #17 опубликовал оператор после исправления локальной ошибки `stale info`, а не оригинальный движок. Восстановительная правка #7 дополнительно слита через PR #18. В локальной базе всё ещё удерживается `divergent_validated_heads` для #7: требуется утверждённый `release_validated_work` и проверка после перезапуска. **Полное автономное E2E, окончательная реконсиляция и внедрение в рабочие репозитории НЕ подтверждены.**



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
| Codex CLI with ChatGPT authorization | ORIGINAL PROVIDER SUPPORTED; owner reported `codex login status` -> `Logged in using ChatGPT` on Windows. WSL2 ChatGPT login and scoped native sandbox were reported PASS by the owner; permanent host separation and fully unattended publication remain NOT_VERIFIED |
| Independent OS credential isolation on owner's Windows host | NOT_VERIFIED; per-agent sandbox is not proof of GitHub secret isolation |
| Autonomous unattended E2E with two new pilot issues | PARTIAL: #7 and #8 completed with operator-assisted publication; unattended E2E NOT_VERIFIED |
| Merging | HUMAN by default; preserved, with no auto-deploy |

## Files and fixed pilot boundary

This is a generic Toolkit-owned source template: `example/issue-orchestrator-pilot` is deliberately a placeholder, **not** a real target or an authorization. The actual pilot repository and its exact GitHub issue links live outside portable Toolkit, under the separately permitted test repository.

- `pilot-0.10.0.yaml` - upstream-formatted configuration candidate, **not installed** in the target repository or loaded automatically.
- `pilot-scope.json` - source-only example of the intended fixed scope for a separately approved pilot, with placeholder repository `example/issue-orchestrator-pilot`, branch `main`, Issues `#7` and `#8`, label `adt-io570-pilot-20261109`.
- GitHub Issues Issue #7 and Issue #8 were newly created for this pilot. The second has upstream-native `Depends-on: #7`.

Do not treat `filtering.max_to_start: 2` as an immutable allowlist: it limits launches, not which issues qualify. A third issue labelled with the pilot label could become eligible. **Do not start the original engine unless that gap is closed by an upstream-supported mechanism or specifically accepted after a verified hard safety gate.** Check both labels and exact IDs against GitHub immediately before any eventual activation.

## Provider compatibility and execution gate

At upstream `d4a79824ccd806089cf3f70ec632d39b8ee255ea`:

1. `src/issue_orchestrator/execution/agent_runner_providers/__init__.py` registers `claude-code`, `codex` and `deepseek`.
2. `.../codex.py` uses `executable = "codex"` and probes `codex login status`. Its commands launch Codex CLI.
3. The public plugin entry point `issue_orchestrator.ai_provider_keys` supplies API-key metadata, not a pluggable Python SDK execution backend.
4. `agents[].command` is a documented override, but provider-less custom commands reject `sandbox: true`; simply launching an SDK script does not preserve the provider readiness, authentication, sandbox, interactive review and credential gates.

The Python `openai-codex` SDK is not needed for this integration: use the original CLI provider. The owner has confirmed that Windows `codex login status` prints `Logged in using ChatGPT`. This proves the **Windows CLI login mode reported by the owner**, not that the Linux/WSL executor has the same authentication, available quota, or isolated GitHub credentials. Real model turns were observed by the owner in the separate WSL2 pilot; this portable Toolkit source template never launches models.

**Disposition: `SOURCE_TEMPLATE / WSL2_PILOT_PARTIAL / FULL_E2E_NOT_VERIFIED`.** Codex CLI is now explicitly permitted when authenticated via ChatGPT. Do NOT use API-key billing, extra paid providers, Claude CLI, create a VM/new Windows user, expose publisher credentials or enable the legacy Toolkit supervisor. Do not start the original engine until host security and pilot issue-scope gates have passed.

Next: verify the pinned original CLI in the intended execution environment (prefer existing WSL2 Linux for the upstream POSIX terminal runner); run `codex --version`, `codex login status`, and the original engine's `doctor` after installation review. Windows sign-in does **not** automatically authenticate a separate WSL/Linux profile. Reject unknown or API-key billing. Test that the coding process cannot access GitHub publishing credentials and that the exact pilot issue scope remains guarded at claim time. Existing GUI/SDK success is not E2E evidence.

## Separate generic Toolkit template activation - NOT performed

1. Inspect the pinned upstream tree, LICENSE, NOTICE, lockfile, dependencies and actual target host. No auto-download or global installation. Confirm the exact Git HEAD `d4a79824ccd806089cf3f70ec632d39b8ee255ea`.
2. The owner has permitted ChatGPT-authenticated Codex CLI for this pilot; independently verify the *host's* CLI login, subscription mode, credential isolation, approved repo and immutable Issue membership before activating. The permission is not a paid API grant or a blanket run authorization.
3. Use the separate pilot repository's updated `AGENTS.md` and upstream agent/reviewer prompts; review the upstream `setup` and guardrail hooks before applying them. The Toolkit legacy controller must stay inactive. Review every proposed change before applying it.
4. Verify that `main` and the exclusive scope label still refer to only Issues #7 and #8. Scope must be fail-closed before runtime and remain guarded against late membership changes.
5. After the above gates, follow supported upstream `issue-orchestrator setup`, `setup-guardrails`, `init`, `doctor`, `start`, `pause`, `resume`, `status` and `restart` interfaces as appropriate, using the version-pinned configuration. None was executed in this chat.
6. Observe one real coding session at a time; independent reviewer, bounded rework, PR, exact-head CI, human merge, GitHub Issue closure, post-merge CI, automatic move to #8 and restart/reconciliation. Do not claim success from an empty runnable queue.

The source-only Toolkit tests validate the declared configuration and fail-closed statuses, **not** upstream `doctor`, live GitHub label invariants, security isolation, agent execution or the required E2E.

## Related legacy modules

`scripts/issue_orchestrator.py`, `scripts/issue_supervisor.py` and `scripts/issue_supervisor_sdk.py` are legacy/source-only reference material from previous experiments. They are not activated, removed, imported or wired to this upstream integration. Do not run two queue controllers.

Sources: pinned [configuration](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/configuration.md), [quickstart](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/quickstart.md), [stability](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/stability.md), [FAQ dependencies](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/faq.md), and [GitHub permissions](https://github.com/issue-orchestrator/issue-orchestrator/blob/d4a79824ccd806089cf3f70ec632d39b8ee255ea/docs/user/github-permissions.md).
