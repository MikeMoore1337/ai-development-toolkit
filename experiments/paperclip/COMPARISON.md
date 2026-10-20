# Paperclip vs existing GitHub + Codex workflow — decision record

**Scope:** AI Development Toolkit; isolated board-only evaluation on `paperclipai@2026.1012.0` (Node 24.11.0). This document compares the *workflow/control-plane fit*, not the output quality of live agents.

**Status:** control-plane compatibility verified; no measured productivity or quality advantage. **Recommendation: NO GO for production adoption now; retain the current GitHub + Codex + Toolkit Skill Manager workflow.** The experimental Draft PR is not a request to merge the Paperclip CI workflow into `main`.

## Evidence levels

- **OBSERVED in CI:** Paperclip boots on a disposable GitHub-hosted runner; zero-budget companies and an approval-for-new-agents flag read back; exact `minimal-safe-change/SKILL.md` source imported from a pinned public GitHub commit; two synthetic unassigned issues form a parent-child hierarchy; a priority receipt, comment, two plan revisions and a stale-revision HTTP 409 are verified; one `human_only` plan confirmation remains pending; an independent Python process reads context back.
- **READ-ONLY GitHub baseline:** A public `GET` can retrieve this project's live Issue #80 and Draft PR #81. This demonstrates that GitHub remains the source of truth without mutating the repository, not that GitHub and Paperclip executed the same job.
- **SUPPORTED BY UPSTREAM IMPLEMENTATION/DOCS:** Paperclip exposes native issue CRUD, revisioned plan documents, structured interactions and adapter/agent features; running full services and models needs configuration.
- **NOT OBSERVED:** Codex execution, skill activation in an actual agent run, matching task outcomes, runtime model costs or quality, malicious agent authorization attempts, a real human approving in the UI, full server restart/recovery, automatic end-to-end GitHub Issues synchronisation, and reduced human workload.

## Same *workflow definition*, different available evidence

The comparison applies a common three-stage requirement to both products. This is **not** a claim of equivalent executed A/B trials.

| Stage | Current GitHub + Codex + Toolkit | Paperclip in disposable CI | Evidence |
| --- | --- | --- | --- |
| 1. Intake and decompose a regression investigation | GitHub Issue/PR are the existing authoritative work records; Codex execution remains owner-gated | Create a synthetic parent and child issue; verify relation, reprioritization and comment | Paperclip **observed**; GitHub authoritative Issue/PR **read only** |
| 2. Record a plan and ask for a decision | Record rationale/evidence in GitHub Issue/PR and use existing review/approval gates | Create two plan revisions; old revision yields HTTP 409; create `human_only` interaction without resolving it | Paperclip **observed**; no adversarial authorization or UI approval trial |
| 3. Resume context | Reopen existing GitHub Issue/PR and comments as the canonical source | Fresh Python process reads parent/child, comment, plan, revisions and pending interaction from Paperclip API | Paperclip **observed**, **server was not restarted**; not a time benchmark |

**Do not compare API response latency.** A loopback Paperclip service and remote GitHub APIs have completely different network paths. No comparable GitHub write workload, model outputs, operator minutes, number of manual hand-offs or defect counts were measured.

## Additional complexity and operational costs

| Dimension | GitHub + Codex as used today | Add Paperclip while retaining GitHub | Consequence |
| --- | --- | --- | --- |
| Authoritative issue/PR data | One established GitHub process | Paperclip adds a second issue namespace, plan store and approval state | **Duplicate task state** unless a verified reconciliation strategy is implemented |
| Long-running service | Existing GitHub SaaS and Codex environment | Node.js 24+, Paperclip service and embedded/configured PostgreSQL; upgrade/backup/availability responsibilities | Additional maintenance, failure and backup surface |
| Skills | Toolkit Skill Manager and repo-native `SKILL.md` | Paperclip can import an unchanged pinned `SKILL.md` | **Compatibility benefit** proven; runtime activation not tested |
| Reviews | Existing GitHub PR/review/CI gates remain binding | Structured pending `human_only` interaction observed | Paperclip cannot replace GitHub owner approvals without independently proven integration |
| Execution governance | Existing owner gates and zero-spend hold | Two synthetic companies stored budget=0 and board approval flag=true | Settings verified; **model spend enforcement and agent authorization not tested** |
| Migration/sync | No bridge needed | Mapping issue IDs, status, comments, links and human approvals would be needed | No verified safe bidirectional sync; never silently move the source of truth |
| Cost | Existing plan/CI quotas apply | No *model calls* in this experiment, but runner minutes, storage, service uptime and potential provider charges still matter | **No incremental model spend observed is not a proof of zero future cost** |

The dedicated experimental run [#39363617203](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/39363617203) executed two CI jobs, with **323 unit tests OK** and successful control-plane smoke. Its total wall-clock time of roughly two minutes is a **CI setup/test observation**, not a per-task productivity measurement or a direct comparison with GitHub.

## Measurable decision gates

Retain the current workflow by default. Reconsider Paperclip only when all of these can be validated without weakening owner restrictions:

1. An approved and independently audited **zero-incremental-charge** path exists for a real Codex/other agent comparison, including runtime isolation, provider entitlement, logging and stop conditions. The current `docs/REAL_AGENT_PILOT.md` ZERO-SPEND hold continues to prohibit agent execution even with command-line acknowledgements.
2. Use the same pinned synthetic QA tasks and independent acceptance oracle in both systems; measure successful outcomes, regressions, required human interventions, elapsed operator time, token/provider charges and recovery behavior. Record independent reviewer judgments. **No result is currently available.**
3. Define and verify a **single authoritative GitHub Issue/PR lifecycle** with explicit Paperclip-to-GitHub mappings, conflict handling and protection of owner approval/review gates. A second task system without sync is not an acceptable replacement.
4. Review Paperclip process isolation, local database durability/backups, secret permissions, upgrade burden and the enforcement (not merely display) of budgets and human-only approvals.
5. Demonstrate a meaningful workflow gain that outweighs permanent service/sync complexity; document the observed benefit, not a speculative percentage.

**Current decision: NO GO for permanent integration into AI Development Toolkit, YFC, Hermes or private Second Brain data.** Keep Issue #80 for the owner decision and PR #81 as an isolated, unmerged Draft until an explicit disposition. No deployment, VPS changes, agent execution, GitHub writes from CI or production access is authorized.

## Reproducible phase 3 check

`experiments/paperclip/comparison.py` uses **anonymous GET only** for GitHub Issue #80 / PR #81 and reads the same disposable Paperclip instance created in phase 2. It produces a clearly labelled `PAPERCLIP_VS_GITHUB_STRUCTURAL_READ_ONLY_NOT_AGENT_AB` record and checks that the source-of-truth Issue and unmerged Draft PR still exist.

It deliberately records `same_task_execution_compared=false`, `measured_productivity_improvement=false`, `real_agent_trials=0`. These truth labels are essential: CI must never misreport this as an agent performance benchmark.
