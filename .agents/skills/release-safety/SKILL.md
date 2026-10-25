---
name: release-safety
description: Prepare and verify a release or production deployment based on the real project pipeline and granted authorization. Use for release readiness, merge or deployment work.
---


# Release safety
1. Discover current release mechanism and base branch from the repository. Never hardcode branch names or CI providers.
2. Establish exact commit/revision, required checks, migration order, rollout requirements and ownership.
3. Review backwards compatibility, data backups when necessary, feature flags and rollback or forward-fix.
4. Define verifiable smoke checks for changed critical paths and observe health beyond successful pipeline completion.
5. A clean local test or user approval of a screenshot does not itself prove a deployment happened.
6. Obtain and respect the authorization actually granted; don't infer rights from a generic skill.
7. Record PR/commit/deployment evidence and distinguish what was attempted, verified and blocked.
8. Before reporting `RELEASED`, verify the exact PR head and required checks, the GitHub merge outcome and merge commit, then the relevant deployment and post-release smoke for that deployed SHA when available. An open PR, approved screenshots, or head CI alone means `NOT_RELEASED`; missing deployment evidence means `DEPLOYMENT_NOT_VERIFIED`.
9. When the target repository uses managed worktrees/leases, run only its supported finish procedure; never prune, delete, or move another controller's worktree on the basis of this skill. Inspect existing host-managed isolation first.
10. If a session's execution appears wasteful (retries, repeated calls, excessive duration), provide a privacy-preserving diagnostic summary supported by **observed** command counts and timestamps where available. Keep raw transcripts, prompts and tokens outside Toolkit; absent measurements are `NOT_MEASURED`. See `docs/en/SUPERPOWERS_EVIDENCE.md`.

**Output:** readiness, executed actions, exact versions, post-release evidence, outstanding risks.
