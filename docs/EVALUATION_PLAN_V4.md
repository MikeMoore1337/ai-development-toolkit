# Evaluation plan for practical usefulness

Do not assert improvement merely because more skills or tests exist.

## Paired trials

On the same pinned repository SHA, run representative tasks with identical model, task text, permissions, tools and budget, first with v3 and then v4; reverse run order where possible. Include simple UI fix, API defect, complex feature, context recovery, skill import and deployment-gated change.

Record:
- Acceptance criteria reached and independently evidenced
- Relevant regressions or introduced defects
- Actual user approvals or blockers
- Total model usage / elapsed execution time from agent telemetry if accessible; else unknown
- Unnecessary file changes and duplicated documents
- Skill activation evidence (not just presence on disk)
- Correct distinction between local test, CI, production

Treat conclusions as provisional without repeated comparable runs. A valid skill package does not itself guarantee better agent performance.

## Product-specific smoke tests

- Codex: project skill folder actually discovered, one `feature-delivery` trigger, one no-trigger case.
- Hermes: correct profile/home skill directory and independent actual-load confirmation; Make Feature under personal license only.
- Claude Code: validate client-supported skill root and metadata compatibility.
- GitHub: verify AGENTS.md and CI still enforce project-specific release permissions.
