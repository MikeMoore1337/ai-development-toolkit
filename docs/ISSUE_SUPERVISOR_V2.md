# Issue Orchestrator v2 - host supervisor (#570)

**Status: SOURCE-ONLY / BLOCKED_HOST_ISOLATION.** Do not enable as an autonomous daemon. The current code is not production-ready.

## Responsibility boundaries

- Existing scripts/issue_orchestrator.py is the only GitHub Issue/PR queue authority (WIP=1).
- scripts/issue_supervisor.py is an opt-in host control prototype with private atomic state and single-process locking; it does not grant publish or merge authority based on an agent message.
- scripts/issue_supervisor_sdk.py is an optional adapter to the official openai-codex Python SDK. Toolkit never auto-installs or invokes it on checkout.
- Official SDK releases depend on a matching openai-codex-cli-bin package. This is part of the SDK implementation, not an instruction to run Codex CLI manually. Explicit host approval and current subscription/usage verification are mandatory.

## Current mandatory safety refusal

The SDK adapter **unconditionally refuses** live execution with OS_SEPARATED_WORKER_NOT_ATTESTED. A subprocess started as the GitHub-owning Windows user may access Credential Manager or GitHub authentication files even if GH_TOKEN is removed from its environment. Prompt-only instructions do not enforce credential isolation. Dedicated restricted host identity and independent proof of secret separation must be delivered before worker dispatch.

## Implemented source-level checks

1. Strict policy bound to repository, target branch, immutable Issue allowlist (max 30) and capped attempts/turns; initial mode PAUSED.
2. Private state written atomically outside the checkout; a single-writer kernel file lock released on crash; refusal to overwrite existing state.
3. GitHub owner and exact remote HEAD checks, clean target checkout, fast-forward only, deterministic issue worktrees with verified common Git directory.
4. Persist turn attempts before SDK dispatch and fail closed into RECONCILIATION_REQUIRED after ambiguous completion.
5. A PR with completed checks still cannot be merged: independent exact-SHA reviewer and privileged publisher are NOT_IMPLEMENTED.
6. Explicit STOP sentinel prevents the next step from claiming work; a full process-lifetime kill switch is NOT_IMPLEMENTED.
7. The read-only `audit` CLI re-observes selected Issues, verified merged PR HEAD, exact merge SHA and post-merge GitHub Actions. It only reports `QUEUE_ALL_VERIFIED` when every scope member is independently checked; empty `available` and max-issues exhaustion never prove completion.
8. Sensitive output is not written into the audit, and no real model or API calls are made during offline tests.

## One-request activation contract

The owner wants exactly one explicit, repository/branch/Issue-scoped instruction, after which a trusted host should advance automatically through `plan -> start -> worktree -> tests -> independent review -> PR -> exact-head CI -> permitted merge -> post-merge verification -> plan`. The owner must not type "continue" after each Issue; this does not confer permission over an entire unselected backlog.

Example of the intended **single owner instruction**, not an enabled command:

> Run the authorized Toolkit Issue Orchestrator for OWNER/REPO, target branch dev, and only Issues #12, #34 and #56. Process the eligible issues one at a time without asking me to repeat "continue"; validate tests, independent SHA-bound review, PR checks, merge authorization and post-merge evidence before moving to the next. Show UI previews only when owner approval is required. Report separately verified, blocked, waiting and held issues, and stop on unverified costs or security permissions.

The trusted Windows host must bind the specific repository, branch and immutable allowlist to this instruction before any unattended execution. A generic single-Issue request must never authorize an entire backlog.

Until the host runtime, privileged publisher and autonomous restart are independently proven, the new supervisor **will not start models**. The `run` command refuses `PERSISTENT_SUPERVISOR_NOT_IMPLEMENTED`, and SDK worker calls refuse `OS_SEPARATED_WORKER_NOT_ATTESTED`. Do not bypass these gates.

Read-only audit of an initialized scoped queue:

    py -3.14 scripts/issue_supervisor.py audit --repo OWNER/REPO

Results distinguish `QUEUE_ALL_VERIFIED`, `QUEUE_HAS_ELIGIBLE`, `QUEUE_RUNNING` and `QUEUE_NO_ELIGIBLE_WITH_BLOCKERS`, with separate lists for closed-verified, available, waiting approval, blocked and excluded Issues.

## Open acceptance gates - keep Issue #570 OPEN

- Actual Windows host identity split and locked-down worktree runtime, with no publisher credentials visible to the coding process.
- Durable opt-in OS service/scheduled task, authenticated process identity, heartbeat, bounded restart, pause/resume/stop, and child-process kill.
- Before claim/merge/completion, idempotent GitHub/PR/branch/labels/review/head/CI reconciliation; no duplicate PR or forced push.
- Owner-configured quick/full validation bound to one exact commit, independent reviewer verdict on same SHA, max no-progress rework and retry budgets.
- PR watcher limited to queue-owned PRs, stable ID deduplication, stale/resolved review handling.
- SHA-bound UI approval notification and revocation, while independent tasks may continue.
- Synthetic negative scenarios for restart, stale worker, dirty/ambiguous worktrees, head races, stale CI, malicious Issue text, quota expiry, kill switch.
- Actual host-supervisor E2E on NEW isolated synthetic Issue with one real PR, one active worker, CI, independent review, authorized merge and post-merge receipt.

## Tests (no SDK or model required)

Run on a clean local Toolkit checkout:

    py -3.14 -m unittest discover -s tests -p test_issue_supervisor.py -v
    py -3.14 -m unittest discover -s tests -p test_issue_orchestrator.py -v

## External evidence and selective adoption

- issue-orchestrator/issue-orchestrator source revision d4a79824ccd806089cf3f70ec632d39b8ee255ea (Apache-2.0): patterns only, no copied source or unstable internal API.
- Official openai/codex Python SDK: https://github.com/openai/codex/tree/main/sdk/python (Apache-2.0), not bundled.
- MCP Market skills and OpenClaw gh-issues are review-workflow ideas, not installed executables or authorities.
- The previously verified 3-Issue Codex Desktop pilot proves session-driven execution only; it does not prove the v2 resident supervisor.
