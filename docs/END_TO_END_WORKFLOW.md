# End-to-end workflow: idea to support (Issue #67)

[Русская версия](ru/END_TO_END_WORKFLOW.md) | [Beginner](BEGINNER_WORKFLOW.md) | [Delivery](PROJECT_DELIVERY_MANAGEMENT.md) | [Release](RELEASE_PROCESS.md)

This is a portable **contract**, not a third controller, state service, installer or proof that an AI client executed anything. For a feature select exactly one controller: default to **feature-delivery** for ordinary code delivery (quick/normal/deep by risk); use **make-feature** only when expressly selected for its own bounded delegation and state management. Delegate specialist tasks, never ownership of the workflow. A role description is not an independent agent; without distinct execution context use INDEPENDENT_REVIEW=NOT_AVAILABLE.

## Reuse-first matrix

| Stage | Existing authority | Needed link / completion gate | Unknown stays unknown |
| --- | --- | --- | --- |
| Discovery | product-discovery | User/problem/MVP -> original goal; confirmed scope | Real demand |
| PRD | product-discovery | R-ID, AC-ID, main and error paths | Owner approval |
| Planning | project-delivery-management | Typed dependencies, blockers, permissions | Unapproved schedule |
| System | business-system-analysis | UC/SR retain parent R/AC; interfaces | Unknown NFR |
| UX/UI | ux-design-process | Flows/screens, visual approval gate, AC | UI if design only |
| Architecture | architecture-decisions | D-ID rationale, affected R/AC | Unchecked assumption |
| Implementation | feature-delivery OR make-feature | Changed files, baseline and AC linkage | Unwritten code |
| QA | qa-strategy / QA skills | Real observed test receipts for each AC | PASS without execution |
| Security | security-engineering | Risk-based check or justified N/A | Unreviewed risk |
| Release | release-safety | Exact SHA, required CI and distinct owner approval | Deployed state |
| Operations | observability-sre | Real signals/recovery only when deployed | Telemetry |
| Support | maintenance-support | Verified version/issue/customer message | Customer delivery |

Additional specialists: reliability-testing, performance-load-testing, accessibility-qa and DevOps only when risks demand them. UX/UI Design Orchestra is a subordinate design workflow, never another product controller. Existing Issues/PR, accepted documents or chat remain source of truth, not this example.

## Workflow / handoff / evidence contract

Workflow: workflow_id, original request, project_ref, source_revision, one controller, mode, current and required stages, skipped stages with reasons, original R/AC, decisions and dependencies, artifacts, evidence, permissions/owners if known, blockers, remaining scope and next action. For simple tasks one chat response is sufficient; only persist with explicit file authorization.

Handoff: id, from/to stage, related task, unchanged R-ID/AC-ID, source artifact + source revision, deliverable, decisions, constraints, open questions, evidence links, verification level, approval requirement and actual receiver acknowledgement. HANDOFF_PREPARED is not HANDOFF_ACCEPTED. DESIGN_APPROVED is not UI_IMPLEMENTED. IMPLEMENTATION_COMPLETE is not QA_PASS. QA_PASS is not RELEASED.

Evidence: stage, inputs, outputs, revision, requirements and decisions, verification level, test ID and observed result, missing evidence, approval, next stage. Levels: PROPOSED, SOURCE_BACKED, CONTRACT_VALIDATED, SYNTHETIC_TESTED, IMPLEMENTED, TESTED, INDEPENDENT_REVIEWED, MERGED, RELEASED, DEPLOYED, USER_VERIFIED, NOT_TESTED, BLOCKED. Never elevate a level without its actual receipt; a synthetic oracle only supports SYNTHETIC_TESTED.

Trace chain: goal -> original R-ID -> original AC-ID -> decision -> changed code -> executed test -> observation -> exact release/version -> support. Missing requirements, unexecuted tests, version mismatch, unauthorised scope additions and blockers must remain visible.

Dependencies: BLOCKS, RELATED, REQUIRES_DECISION, REQUIRES_APPROVAL, OPTIONAL. Check absent endpoints, cycles and missing mandatory predecessors. A blocked release does **not** stop unrelated planning or tests. Quick = small, reversible confirmed acceptance; normal = new connected feature; deep = permissions, payment, irreversible data, or major unknown. Depth follows risk, not diff size. No mandatory full-document stack for quick.

## Stop, resume and permissions

Check **actual tool capability** and separate authority before READ, CHANGE, EXECUTE or EXTERNAL. EXPLAIN and PREPARE do not modify a target. Never auto-install external skills, call paid APIs, bypass visual/rights approvals, write user outputs into Toolkit, or treat access as permission. Release/merge/deploy/publication/deletion/irreversible migration each use their applicable separate owner gate.

Resume index: workflow ID, previous state revision, current source/HEAD, last stage, next stage, accepted decisions, previous evidence, blockers, pending approvals, changes since pause, required revalidation, actual delegation counters and next action. If HEAD/requirements change, revalidate affected acceptance; never reuse old PASS. Missing artifacts or revoked permission stop dependent steps. Do not replay irreversible actions, duplicate issues/releases or reset budgets.

## Synthetic reproducible story

[Reference](../fixtures/end-to-end-workflow/reference.json): a fictional local household-task application with R1 add, R2 display, R3 complete and AC1-AC3. Product discovery, PRD and planning are described; analysis, UX and architecture remain proposals; implementation and tests were **not executed**. No real GitHub PR, user validation, release, production telemetry or support delivery is claimed. State resumes from planning/analysis, retaining blockers.

Run from an authorised Toolkit development checkout:

    python scripts/validate_end_to_end_workflow.py
    python -m unittest tests.test_end_to_end_workflow -v

The read-only Python standard-library oracle checks [42 intentionally broken mutations](../fixtures/end-to-end-workflow/broken_cases.json) against the same reference, including controller conflict, ID loss, dependency cycles, false QA/release/independence, scope creep, write boundary and stale HEAD. It checks structured claims, **not** whether the fictional implementation actually runs.

## Beginner, expert and chat-only paths

**Beginner:** "I want a simple local household-task list. Use AI Development Toolkit, choose the necessary methods yourself, do not require GitHub or terminal, and tell me precisely what worked and what did not." The client narrows scope, asks only blocking questions, performs authorised operations if truly capable, then gives one clear next action.

**Expert:** "Track original R/AC through relevant discovery, system/UX contracts, architecture, implementation, risk-based QA/security, release gates, and support; give exact receipts and a resumable index."

An IDE may inspect a local project without a project URL. An attached ZIP plus a Toolkit link is enough context to analyse an accessible archive, not proof of installed skills. In a chat without read/write/terminal tools, supply a plan or generated artifact and mark code changes, tests, runtime and deployment NOT_TESTED / CAPABILITY_UNAVAILABLE. Copying SKILL.md is not client activation. Real cross-client activation and measurement belong to Issue #68; optional tool permissions/integrations to #69. No paid dependency is required.
