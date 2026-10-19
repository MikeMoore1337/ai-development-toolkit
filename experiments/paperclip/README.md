# Paperclip isolated integration pilot

## Purpose and constraints

This experiment checks a **control-plane** smoke on an ephemeral GitHub-hosted Ubuntu runner, not model quality or autonomous agent performance. It does not install a service on the owner machine or a VPS, and never touches YFC, Hermes, private vaults or production data.

- Pinned upstream version: `paperclipai@2026.1012.0` (not `latest`, canary or `master`).
- Supported Node runtime: `24.11.0`.
- Paperclip binds to loopback `127.0.0.1:3100`, keeps data under `RUNNER_TEMP`, and does not install a system service.
- No API keys, GitHub credentials, model providers, agents, heartbeats, PR merge or deployment.
- The company monthly budget is **zero**. No cost/usage data is assumed or fabricated.
- `actions/checkout` does not persist credentials. Workflow permissions are `contents: read` only.
- Logs from the Paperclip bootstrap are not published because onboarding can generate local secrets.
- Import reads only the public Toolkit skill at the GitHub URL; no GitHub login or write token is given to Paperclip.
- The runner is disposable; it must not be interpreted as a security sandbox for arbitrary agents. No agent runtime is invoked.

## Checks

1. A stable pinned `paperclipai` package boots with embedded PostgreSQL.
2. `GET /api/health` responds with non-error JSON.
3. Two temporary zero-budget companies are created (separate to avoid duplicate skill slugs).
4. The official managed-skill creation API preserves the exact bytes of the Toolkit's unchanged `.agents/skills/minimal-safe-change/SKILL.md`. The server's stored file must match source content exactly.
5. **Independently**, the public GitHub skill URL is imported through Paperclip's GitHub-source API. Failures remain a hard CI failure with a minimal, sanitized error diagnostic; managed skill creation **never** counts as a substitute for GitHub import.
6. The test emits `PAPERCLIP_CONTROL_PLANE_SMOKE_NOT_AGENT_EVAL`, `real_agent_trials=0`, `model_calls_requested_by_test=0`.

This workflow intentionally **does not verify** correct runtime materialization, agent activation, GitHub source synchronisation, review/approval enforcement or improvement over ordinary Codex usage. Real model/agent experiments remain prohibited under the Toolkit's zero-spend hold documented in `docs/REAL_AGENT_PILOT.md`.

## Interpretation

Passing means only that this specific control-plane setup, exact managed skill creation and public GitHub source import worked on the GitHub runner. Initial live run: direct import from the workflow checkout was rejected with HTTP 403, consistently with Paperclip's documented local skill workspace boundary. We intentionally preserve that boundary and test the supported public GitHub import route instead. A failed install/import must remain a visible failure; do not bypass or mark skipped. The experiment is isolated in an unmerged draft PR until the evidence is reviewed. Do not retain it in required long-term CI without a separate benefit assessment.

## CI execution mode and observed boundaries

The Draft PR uses an experimental-branch-only `push` trigger plus the existing restricted pull-request trigger, so the exact checksum-update HEAD can run without merging. Required toolkit CI continues independently. Branch-triggered workflow runs cannot be inferred from the pull-request-only commit-run listing tool; inspect the actual Actions page/run before claiming success.

The GitHub import previously returned HTTP 422, reason not captured by the earlier run. Current smoke records only the sanitized HTTP code/reason and continues to independently test managed skill creation, but exits nonzero if GitHub import remains unavailable. It creates no agents and no model connections. Neither scenario proves runtime skill activation.
