# Evidence, safe worktrees and session diagnosis

This is a portable **reference for existing skills**, not a new controller, CLI, auto-hook, telemetry collector or an authorization to run agents. Original methods were independently adapted from [obra/superpowers](https://github.com/obra/superpowers/tree/main/skills) (MIT); no upstream skills are installed or copied. Project AGENTS, client capabilities, human approvals, privacy and release gates take precedence.

## Failure triage (read-only first)

1. State the expected behavior, actual error or symptom, source revision, environment and a minimal reproducible path. If reproduction is destructive, unsafe or inaccessible, record `REPRODUCTION_NOT_VERIFIED`.
2. Check existing logs/tests, recent changes, and each component boundary. For multicomponent failures distinguish UI, transport, API, persistence and external dependency. Never echo credentials or private payloads.
3. Label candidate causes `HYPOTHESIS`. Mark `ROOT_CAUSE_CONFIRMED` only after corroborating an error path or controlled reproduction.
4. Propose the smallest compatible correction; first test the affected behavior, then run required project-defined regressions. No universal test-first or paid-model requirement.

## Isolation decision (do not silently mutate the workspace)

1. Detect whether the current project is already in a host-managed or linked Git worktree. In Git, compare `git rev-parse --git-dir` with `git rev-parse --git-common-dir` and check `git rev-parse --show-superproject-working-tree`: a submodule is **not** evidence of a worktree.
2. If already isolated, **reuse it**. Do not create nested or additional worktrees.
3. Otherwise, prefer native client worktree/sandbox controls. If the target repository has a lease/controller, use its interface instead of manually managing the tree. Confirm permissions, task identity and worktree ownership before any action.
4. Only if no native/controller mechanism exists and the task owner authorized isolation may a manual `git worktree add` be considered. Check branch existence, clean base, filesystem paths and `.gitignore`/ `git check-ignore` for a project-local destination. Do not create, prune or delete an unknown path.
5. Establish baseline test results (or record why not executable). Never install dependencies automatically because a generic skill lists an install command. Do not assume OS, package manager or base branch.
6. Keep exact-head checks, merge authorization, cleanup and post-release smoke within the project's existing process.

## Proof before claims

| Claim | Sufficient evidence | Insufficient evidence |
|---|---|---|
| Bug fixed | Reproduction passes at current revision, regression observed | Fix committed, assumption |
| Tests pass | Exact commands, exit status, scope, current SHA | Earlier green run, second-hand success |
| Independently reviewed | Identified actual reviewer/context and concrete findings | A synthetic label or the implementer's self-claim |
| Merged | GitHub's observed merge outcome + commit | PR opened, review approved |
| Deployed | Deployment to the named environment + SHA and smoke where required | PR/head CI green |
| AI client executed | Actual delegation receipt and observed results | Planned or hypothetical agent |

Use `NOT_VERIFIED`, `NOT_EXECUTED`, `NOT_MEASURED` or `BLOCKED` where evidence is missing.

## Optional session-efficiency diagnosis

A diagnostic is generated **only on request or a relevant performance defect**. It must not start logging, install hooks, read other sessions without authorization or change the model. Collect a minimal, redacted summary **in the target project's authorized environment**, never in the shared Toolkit repository:

- Task, client and version when known, scope/expected actions, start/end timestamps if observed.
- Exact evidence for repeated tool calls, duplicate file reads, failed retries or repeated plans; separate normal polling from waste.
- Measured prompt/completion/cached-token counters **only when supplied by the client**; don't infer them from elapsed time or pricing.
- Root-cause hypothesis, possible correction, regression guard and rollback. If there is no trace, mark `NOT_MEASURED`, not zero.
- Never include raw prompts, session transcripts, secrets, credentials, identifying paths or user project data in public fixtures/issues.

Positive case: an already-isolated session reports and reuses the existing worktree, then verifies test outcomes at the actual head. Negative case: sandbox unavailable, no native tool or unapproved Git action -> report boundary without mutation. Collision case: a project-managed controller forbids manual worktrees -> controller wins, even if a generic reference suggests creation.
