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
- The runner is disposable; it must not be interpreted as a security sandbox for arbitrary agents. No agent runtime is invoked.

## Checks

1. A stable pinned `paperclipai` package boots with embedded PostgreSQL.
2. `GET /api/health` responds with non-error JSON.
3. A temporary, zero-budget company is created.
4. The Toolkit's unchanged `.agents/skills/minimal-safe-change` can be imported into Paperclip's company skill library and found by slug.
5. The test emits `PAPERCLIP_CONTROL_PLANE_SMOKE_NOT_AGENT_EVAL`, `real_agent_trials=0`, `model_calls_requested_by_test=0`.

This workflow intentionally **does not verify** correct runtime materialization, agent activation, GitHub source synchronisation, review/approval enforcement or improvement over ordinary Codex usage. Real model/agent experiments remain prohibited under the Toolkit's zero-spend hold documented in `docs/REAL_AGENT_PILOT.md`.

## Interpretation

Passing means only that this specific control-plane setup and local skill import worked on the GitHub runner. A failed install/import must remain a visible failure; do not bypass or mark skipped. The experiment is isolated in an unmerged draft PR until the evidence is reviewed. Do not retain it in required long-term CI without a separate benefit assessment.
