# Paperclip isolated integration pilot

## Purpose and constraints

This experiment checks a **control-plane** smoke on an ephemeral GitHub-hosted Ubuntu runner, not model quality or autonomous agent performance. It does not install a service on the owner machine or a VPS, and never touches YFC, Hermes, private vaults or production data.

- Pinned upstream version: `paperclipai@2026.1012.0` (not `latest`, canary or `master`).
- Supported Node runtime: `24.11.0`.
- Paperclip onboarding explicitly uses `--bind loopback`; health is queried only over `127.0.0.1:3100`. Instance data stays in `RUNNER_TEMP`; no system service is installed.
- No API keys, GitHub credentials, model providers, agents, heartbeats, PR merge or deployment.
- Both companies' monthly budgets are **zero** and independently read back from the API. Both companies have `requireBoardApprovalForNewAgents=true`, set via PATCH and then verified with GET. No cost/usage data is assumed or fabricated.
- `actions/checkout` does not persist credentials. Workflow permissions are `contents: read` only.
- Logs from the Paperclip bootstrap are not published because onboarding can generate local secrets.
- Import reads only the public Toolkit skill at the GitHub URL; no GitHub login or write token is given to Paperclip.
- The runner is disposable; it must not be interpreted as a security sandbox for arbitrary agents. No agent runtime is invoked.

## Checks

1. A stable pinned `paperclipai` package boots with embedded PostgreSQL.
2. `GET /api/health` responds with non-error JSON.
3. Two temporary zero-budget companies are created (separate to avoid duplicate skill slugs). Both are PATCHed to require board approval for new agents and both settings are read back.
4. The official managed-skill creation API preserves the exact bytes of the Toolkit's unchanged `.agents/skills/minimal-safe-change/SKILL.md`. The server's stored file must match source content exactly.
5. **Independently**, the public GitHub repository is imported through Paperclip's documented skill selector parser (`npx skills add <pinned GitHub repository URL> --skill minimal-safe-change`, used only as a string input, never executed as a shell command). The reference is pinned to immutable commit `73688b472ff3cce8091914b3d1845c414d930c7a`. The stronger gate verifies exactly one imported skill, `sourceType=github`, the matching `sourceRef` SHA and exact read-back equality of the imported `SKILL.md`. Failures remain a hard CI failure with a minimal, sanitized error diagnostic; managed skill creation **never** counts as a substitute for GitHub import.
6. A separate zero-provider offline job validates Toolkit provenance inventory, release preflight, checksums, metadata and unit tests.
7. The test emits `PAPERCLIP_CONTROL_PLANE_SMOKE_NOT_AGENT_EVAL`, `real_agent_trials=0`, `model_calls_requested_by_test=0`.

This workflow intentionally **does not verify** correct runtime materialization, agent activation, GitHub source synchronisation, review/approval enforcement or improvement over ordinary Codex usage. Real model/agent experiments remain prohibited under the Toolkit's zero-spend hold documented in `docs/REAL_AGENT_PILOT.md`.

## Interpretation

Passing means only that this specific control-plane setup, exact managed skill creation and public GitHub source import worked on the GitHub runner. Initial live run: direct import from the workflow checkout was rejected with HTTP 403, consistently with Paperclip's documented local skill workspace boundary. We intentionally preserve that boundary and test the supported public GitHub import route instead. A failed install/import must remain a visible failure; do not bypass or mark skipped. The experiment is isolated in an unmerged draft PR until the evidence is reviewed. Do not retain it in required long-term CI without a separate benefit assessment.

## CI execution mode and observed boundaries

The Draft PR uses an experimental-branch-only `push` trigger plus the existing restricted pull-request trigger, so the exact checksum-update HEAD can run without merging. Required toolkit CI continues independently. Branch-triggered workflow runs cannot be inferred from the pull-request-only commit-run listing tool; inspect the actual Actions page/run before claiming success.

The GitHub import previously returned HTTP 422, reason not captured by the earlier run. Current smoke records only the sanitized HTTP code/reason and continues to independently test managed skill creation, but exits nonzero if GitHub import remains unavailable. It creates no agents and no model connections. Neither scenario proves runtime skill activation.

## Investigation evidence (2026-10-20)

- [Run 39325593342](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/39325593342): managed skill import/byte-for-byte file verification PASSED, public GitHub import returned `422 skill_source_github_read_failed`.
- [Run 39326644332](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/39326644332): anonymous direct GitHub API probes returned HTTP 200 for the repository metadata and `commits/main`, while the original folder GitHub import again failed with upstream HTTP 422.
- Source review identified a potential ref-resolution problem: Paperclip's GitHub folder importer initially tests candidate refs containing the appended folder path before the valid branch name. If GitHub returns 422 (rather than 404) for an invalid candidate ref, the import stops. This is a **hypothesis**, not proven root cause.
- Replaced the folder URL with the parser-supported `npx skills add ... --skill minimal-safe-change` string, pinned to a full immutable commit, to avoid candidate-ref probing. No installer command is executed by the smoke.
- Paperclip's `createCompanySchema` only accepts name, description, zero budget and responsible user; `requireBoardApprovalForNewAgents` defaults to `false` in the database and must be applied by supported `PATCH` and verified by `GET`. The updated smoke checks that explicitly.

## Confirmed acceptance result (2026-10-20)

The exact-head verification completed **PASS**:
[GitHub Actions #39327290358](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/39327290358),
commit `e7e77a69daaf306510c091b8d526e2ca5029d543`.

- `local-control-plane: success` — `github_import=PASS`, `managed_skill_exact_source=true`, `board_approval_required_verified=true`, `budget_monthly_cents_verified=0`, `real_agent_trials=0`, and `model_calls_requested_by_test=0`.
- `toolkit-source-integrity: success` — inventory and release provenance PASS (203 components, 65 skills), all SHA256 checks PASS, Toolkit metadata PASS and **323 unittest cases OK**.
- Anonymous GitHub API probes: HTTP 200 on repository metadata and `commits/main`.

**Decision:** The controlled zero-spend control-plane/skill-compatibility smoke is technically accepted. This is evidence of importing the skill and enforcing the stated test-company settings — **not** proof that autonomous planning, GitHub issue ownership, reviews, model spending controls, throughput or task effectiveness improve. Leave the PR in Draft, do not deploy Paperclip on Hermes/YFC/VPS, do not merge into main or clear the owner ZERO-SPEND hold for agents. Any later real-agent or end-to-end orchestration comparison needs independently approved scope, permissions and measured benefit.

## Follow-up stronger verification

After the baseline PASS in run `39327290358`, the experiment was strengthened to assert the imported GitHub skill has the exact pinned `sourceRef` and matches the original `SKILL.md` on read-back, rather than checking only its slug. These stronger checks require their own final exact-head CI result; the baseline PASS alone does not prove them.

## Phase 2: Board-only task/context verification

This non-agent exercise extends the accepted skill-import smoke to the **control plane**, using an additional disposable company in the same ephemeral runner.

1. The board creates a synthetic parent issue and child issue, both with **no agent assignee**, and updates the child priority using the server's change receipt.
2. The board appends a synthetic checkpoint comment, creates and updates a `plan` Markdown document, and verifies an update against an obsolete `baseRevisionId` is rejected with HTTP **409**.
3. The board creates a `request_confirmation` interaction, targeted at the latest plan revision, with `resolverPolicy=human_only` and `continuationPolicy=none`. **No acceptance or rejection is performed.** The card must remain `pending` and the effective policy must remain `human_only`.
4. A separate Python interpreter process reads the parent/child relation, comment, latest plan revision, revision history and pending human-only interaction via the local HTTP API.
5. Before and after, the board verifies there are **zero agents**, a zero monthly company budget, and `requireBoardApprovalForNewAgents=true`.

The private receipt storing only test IDs remains under `RUNNER_TEMP` and is not uploaded. No model providers, agents, credentials, heartbeats or issue checkout are created/invoked. The code deliberately performs **no mock board acceptance**, to avoid misrepresenting a simulated decision as real owner approval.

**Interpretation limits:** This tests the API's board-controlled issue storage, revision conflict handling and interaction state; it does **not** demonstrate enforcement against an authenticated agent (none exist), database recovery after server restart, end-to-end GitHub task synchronization, automatic agent coordination, actual human UI decision flow, speed advantage or model costs. The test is not authorization to activate autonomous work or deploy Paperclip.
