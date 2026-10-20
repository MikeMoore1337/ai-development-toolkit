---
name: project-delivery-management
description: "Turn a PRD or project requirements into a traceable delivery plan with tasks, dependencies, priorities, risks and evidence-backed status. Use for project planning and progress reports, not implementing one bug or deploying a release."
metadata:
  pack: "management"
  version: "1.0.0"
---

# Project & Delivery Management

**Positive triggers:** "Break this PRD into tasks"; "Plan implementation order"; "Find blocking dependencies"; "Review project delivery readiness"; "Write a project status report".

**Negative triggers:** "Fix this Python bug"; "Build a React component"; "Write a unit test"; "Design a screen"; "Publish the release". Choose `feature-delivery` (or separately `make-feature`) for feature execution, QA skills for testing, and `release-safety` for releases. This skill is **not** a workflow controller and does not orchestrate agents.

## Inputs and authority

Take an existing PRD, repository task list or natural-language goal. Reuse source identifiers `R-ID`, `AC-ID`, priorities, dependencies, exclusions, constraints and open decisions. Use the existing Product Discovery contract (`extensions/product/skills/product-discovery/references/PRD_CONTRACT.json`) if supplied; never demand a new PRD. A hypothesis remains `UNTESTED` until validated and is not automatically an approved task. Label facts `USER_PROVIDED`, `SOURCE_BACKED`, `OBSERVED`, assumptions `ASSUMPTION`, and gaps `UNKNOWN`. Ask only blocking questions; keep independent tasks moving.

**GitHub is source of truth** when used. Inspect live Issue/PR, branch HEAD and checks before stating current status; otherwise report the snapshot date and `NOT_VERIFIED`. For projects without GitHub, return a chat plan or an explicitly authorized document. Do not create Issues, edit trackers, deploy, merge or close Issues without the necessary authorization. Owner permissions and project instructions prevail.

## Procedure

1. **Reuse first.** Use `task-scoping` for scope and AC, `architecture-decisions` for significant technical choices, `feature-delivery` for concrete implementation, QA `quality-gate-assessment` for testing, and `release-safety` for publishing gates. Never duplicate their execution workflow.
2. **Preserve traceability.** Map each source requirement to one or more bounded deliverables/tasks, carry original `R-ID` and `AC-ID` unchanged, list expected outcome, verification, priority, owner if known, necessary approvals and unresolved decisions. No fabricated owners, timelines, velocity, RICE, ROI or scope decisions. Record missing effort as `UNKNOWN`.
3. **Separate dependencies.** `BLOCKS` means a prerequisite task; `RELATED` is informational; `REQUIRES_DECISION` and `REQUIRES_APPROVAL` identify outstanding human decisions; `OPTIONAL` is not a blocker. Detect self-dependencies and cycles before sequencing; when blocked, report which work can proceed independently.
4. **Sequence ready work.** Prefer one task at a time: verify prerequisites, execute with the project's feature workflow, verify evidence, update actual status and choose the next ready item. Parallel work is optional and never claimed launched without evidence.
5. **Track risk and change.** Use a compact risk register; label unknown probability `UNKNOWN` rather than inventing a score. Record changes to baseline requirements, dependencies and AC; never retrospectively weaken an AC just to mark a task done. Minor clarifications that do not alter scope can stay inline.
6. **Report actual status.** `PLANNED`, `IN_PROGRESS`, `BLOCKED`, `VERIFIED`, `MERGED`, `RELEASED` refer to distinct milestones. `DRAFT`, `READY_FOR_REVIEW`, `CANCELLED`, `NOT_APPLICABLE` are optional. `VERIFIED` needs applicable checks; `MERGED` needs target-branch evidence (closed is insufficient); `RELEASED` needs publication/deployment evidence (green CI is insufficient). Reopen or recheck when new defects emerge. Do not silently promote status.
7. **Handoff.** Pass the existing IDs and unresolved questions Product → Delivery → Analyst → Designer → Engineer → QA → Delivery. A handoff does **not** mean acceptance. See [workflow](references/WORKFLOW.md) and [handoff](references/HANDOFF.md).

## Output contract and recovery

For beginners: a short explanation, ordered tasks, blockers, unknowns, what counts as done, and **one next action**. For experts: source/assumptions, scope baseline, task-to-R/AC traceability, typed dependency graph, priority rationale, risk register, change impact, actual evidence and owner/approval gates. Use [contract](references/DELIVERY_CONTRACT.json) and [synthetic example](references/EXAMPLES.md), scaled to scope. A tiny defect does not need a management plan.

On missing requirements: return `DRAFT_WITH_GAPS`; on a dependency cycle: report the exact cycle and halt dependent tasks; on unavailable GitHub: show `SNAPSHOT_NOT_CURRENT`; on missing CI or permission: `NOT_VERIFIED` or `BLOCKED`, never success. If checks fail or evidence is disproved, move from `VERIFIED` to review, not silently to released. [Manual negative checks](references/MANUAL_ACCEPTANCE.md) cover recovery.

**Storage boundary:** When Toolkit is referenced for another project, all Toolkit copies are **read-only**. Return plans, logs and reports **in chat by default**. Save files only to an explicitly authorized destination; do not write anything into Toolkit, or create unrequested files in the user's project. No external API, background service, Issue tracker or runtime is required. The optional `scripts/validate_delivery_plan.py` validates a provided local JSON plan **without writing**; its static checks cannot authenticate GitHub evidence or real model activation.
