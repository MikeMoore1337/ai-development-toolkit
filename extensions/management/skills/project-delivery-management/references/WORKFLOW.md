# Delivery planning and status procedure

## Reuse-first matrix

| Capability | Existing source | Gap | Decision |
| --- | --- | --- | --- |
| Task scoping | `task-scoping` | Single-task only | REUSE |
| Feature execution | `feature-delivery` / `make-feature` | Already covers implementation | REUSE |
| Task decomposition | PRD in `product-discovery` | No cross-task sequencing | NEW guidance |
| Dependencies | `task-scoping` | No typed links or cycle check | REFINE in management |
| Risk register | `architecture-decisions`, QA | No project-wide lightweight view | NEW guidance |
| Status reporting | `feature-delivery` | No cross-task report with independent evidence | NEW guidance |
| Scope changes | `task-scoping`, QA impact | No PRD/AC baseline comparison | REFINE |
| Release readiness | QA `quality-gate-assessment`, `release-safety` | Already owns quality/release gates | REUSE |

Project Delivery Management decides **what is ready and what is blocked**; it never executes features or grants merge/release permissions.

## Minimal plan

Keep source PRD IDs and AC unchanged. For each task use a stable ID, source R/AC links, outcome, scope, dependency types, priority rationale, owner or UNKNOWN, verification method, status, concrete blockers and approvals. Do not make unsupported estimates. Keep accepted baseline separate from requests to change it. Display non-blocking tasks first; sequential execution is the default, not mandatory parallelism.

**Dependencies:** `BLOCKS` references a prerequisite `task_id`. `RELATED` and `OPTIONAL` are non-blocking. `REQUIRES_DECISION` and `REQUIRES_APPROVAL` require `reference` and explicit `resolved`; unresolved gates block execution. Check for self-cycles and multi-node cycles before scheduling. Resolve cycles by rewriting the plan **only with confirmed business intent**.

**Priority:** user value, actual blocker chains, safety risks, confirmed cost of delay, requirement readiness, technical limitations and available review capacity. Without data, mark time/ROI/velocity `UNKNOWN`. A dependent high-priority task does not outrank its uncompleted prerequisite.

## Status vs evidence

| Status | Minimum honest observation |
| --- | --- |
| `DRAFT` / `PLANNED` | Proposal exists, no work claimed |
| `IN_PROGRESS` | Work actually started |
| `BLOCKED` | Named blocker with required action |
| `READY_FOR_REVIEW` | Result offered for review, not verified |
| `VERIFIED` | Applicable acceptance tests reviewed and evidence exists |
| `MERGED` | Target branch contains change; closed PR alone is not sufficient |
| `RELEASED` | Real publication/deployment independently evidenced |
| `CANCELLED` / `NOT_APPLICABLE` | Decision and reason recorded |

State regression is permitted (IN_PROGRESS → BLOCKED → IN_PROGRESS, VERIFIED → READY_FOR_REVIEW after a critical defect). A document may finish at VERIFIED without a merge or deploy. The optional offline validator only verifies **shape and presence** of evidence fields; never substitutes for actual source checks.

## Change impact and risk

Record change ID and kind (new requirement, clarification, bug fix, priority change, cancellation, deferral, AC revision), affected R/AC and tasks, dependency and test impact, risks, required approval and updated baseline. New scope needs explicit inclusion; purely editorial clarification can be recorded inline. Never rewrite old AC to disguise failure. For each risk: ID, cause, consequence, severity, probability (or UNKNOWN), detection, mitigation, contingency, owner if known and open/resolved status. Escalate serious unresolved risks to blockers.

## Recovery and source of truth

Use GitHub Issues and PRs when already adopted. Inspect Issue state, PR draft/open/closed/merged, exact HEAD SHA and CI, and actual environment before advancing statuses. If GitHub is not accessible, report the date of last known snapshot, never claim live sync. For private projects without GitHub return a chat plan; do not create a second tracker. Reuse source R/AC numbers to hand off unchanged business rules to #55 and user flows to #56. Do not make up analysis decisions or design contracts.

Optional command for a plan saved **outside Toolkit**: `python scripts/validate_delivery_plan.py /authorized/path/plan.json`. No output file is produced. The tool is not required to use the skill, and cannot validate whether links represent genuine outcomes.
