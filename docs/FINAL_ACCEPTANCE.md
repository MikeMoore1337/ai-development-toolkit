# Final offline acceptance (Issue #70)

[Русский](ru/FINAL_ACCEPTANCE.md) | [End-to-end workflow](END_TO_END_WORKFLOW.md) | [Client capabilities](CLIENT_CAPABILITIES.md) | [Skill Evals](SKILL_EVALS.md)

**Scope:** read-only synthetic acceptance of the six roadmap stages (S1-S6), with explicit boundaries between source files, checked contracts, independent users and actual AI-client invocations. Passing GitHub Actions does **not** establish real model effectiveness, human usability, deployment or Skill activation.

## Beginner and expert routes

**Novice:** "I am not a programmer. I want a free local expense tracker: add expenses, see the entries and display a selected month's total." Only these three capabilities are MVP. No mandatory terminal, framework selection, registration, cloud connection or paid service. In a file-capable client, preview changes before authorized writes. In a normal ChatGPT/Claude chat, a Toolkit URL and an attached project ZIP provide reference guidance, **not** a verified installed or invoked Skill. Missing execution privileges must be reported rather than faked.

**Expert:** "Add a CSV batch importer to an existing application without breaking its API, authorization or idempotency; include failure handling, QA evidence, safe release and support handoff." Preserve R-ID/AC-ID and original scope across API/data/security architecture, implementation, unit/integration/contract/negative tests, exact-SHA release and operational support. The synthetic case has no user interface: UI may be NOT_APPLICABLE with an explicit reason, but security may not be skipped.

## Reuse-first matrix

| Direction | Existing sources and oracles | Decision |
| --- | --- | --- |
| S1 quality / provenance | validate_pack, validate_quality, skill_routing_eval, validate_provenance, pinned skills-ref | REUSE |
| S2 beginner, installation, recovery | #52, beginner fixtures/tests and docs/ru/ACCEPTANCE.md | REUSE; independent human NOT_TESTED |
| S3 product, PRD, analysis and UX | Product/analysis/UX docs and #67 | REUSE |
| S4 engineering, QA, security | Existing reliability, performance, accessibility and AI validators | REUSE; select by risk |
| S5 releases, incidents and support | release-safety, observability, dependency/data/maintenance checks | REUSE |
| S6 workflow and client/tool contracts | #67 / #68 / #69 oracles and existing agent eval files | REUSE |
| Cross-stage trace and consolidated evidence | No six-stage final oracle | NEW read-only validator and fixtures |
| Live model experiments | #11 hidden-oracle harness, reviewer and execution freeze | BLOCKED |

No new Skill, controller, model runner, installer, CI framework, database, external connection or paid integration.

## Portable Final Acceptance Contract

The sole synthetic source is [contract.json](../fixtures/final-acceptance/contract.json): acceptance and roadmap identities, stage inventory, novice/expert original goals, R-ID, AC-ID, stage deliverables, planned tests, evidence refs, source revisions, handoff, permissions, receipts, excluded features, cost/measurement fields and limitations. [broken_cases.json](../fixtures/final-acceptance/broken_cases.json) is an intentionally broken in-memory mutation suite. [validate_final_acceptance.py](../scripts/validate_final_acceptance.py) is read-only and reuses the existing Issue #67 E2E audit. [Unit tests](../tests/test_final_acceptance.py) compare expected error codes and repeat each mutation for determinism.

- SOURCE_PRESENCE checks only that a safe, repository-local source exists. PASS for **source presence** is not a claim that the Skill or model actually worked; domain-specific validators and CI are independent evidence.
- INDEPENDENT_HUMAN remains NOT_TESTED without an actual independent novice and recorded observations.
- LIVE_MODEL stays BLOCKED under the Issue #11 zero-spend and owner gates. Real comparative effectiveness stays NOT_MEASURED.
- PASS, FAIL, NOT_TESTED, BLOCKED, NOT_APPLICABLE and INCONCLUSIVE must not be aggregated as a single DONE.
- SOURCE_ONLY, CONTRACT_VALIDATED, SYNTHETIC_TESTED, EXECUTED, INDEPENDENT_REVIEWED, OWNER_REPORTED, NOT_TESTED and BLOCKED are separate evidence levels. Recorded execution requires concrete evidence at the correct source revision.
- IMPLEMENTED, QA_VERIFIED, MERGED, RELEASED, DEPLOYED and USER_VERIFIED require separate receipts. A release or merge is not deployment; copying a Skill is not activation.

Each executed result must report acceptance ID, exact Toolkit HEAD, roadmap/stage/issue, R/AC, method, expected and actual observation, evidence and its level, environment, verification time, reviewer/independence, limitations, blocker and disposition. The synthetic fixture revision labels fictional input, while the validator resolves the real Git checkout SHA at execution time. No head SHA is invented in data files.

## Offline commands

From the repository root with Python 3.12 or newer:

    python scripts/validate_final_acceptance.py
    python -m unittest tests.test_final_acceptance -v
    python scripts/validate_end_to_end_workflow.py
    python scripts/verify_client_compatibility.py
    python scripts/validate_tool_integrations.py
    python scripts/skill_routing_eval.py --strict
    python -m unittest discover -s tests -v

This oracle makes **no network or provider calls**, writes **no files**, runs no models and changes no real projects. Both journeys are contractual simulations: their product implementation, QA, activation and deployment remain unperformed. The existing CI separately checks metadata, release provenance, SHA256, official pinned skills-ref, Ruff, actionlint, package safety and source-archive integrity. On a suspected Windows go-cli flake, record the exact failed run as well as a rerun, without skips or weakened oracles.

## Coverage and metric contract

The emitted S1-S6 table includes each mandatory row and separate PASS, FAIL, BLOCKED, NOT_TESTED, NOT_APPLICABLE and INCONCLUSIVE counts. A source-presence PASS does not raise the measured acceptance rate of a real application. Preserve every denominator including failures and blocked rows, with an explicit explanation for N/A; do not double-count criteria.

| Metric | Required evidence / missing value |
| --- | --- |
| Completeness and accepted AC | Count each original criterion once; only a verified result with matching evidence may be accepted |
| Unauthorized actions | Distinguish rejected synthetic actions, actual violations and unverified risks |
| False claims | Reject TESTED/DEPLOYED/INDEPENDENT_REVIEWED/SKILL_INVOKED without appropriate receipts |
| Regressions and unnecessary edits | Compare actual diff against R/AC and initial state; without observed diff use NOT_MEASURED |
| Usability steps and elapsed time | Observe human actions and timestamps; otherwise NOT_MEASURED |
| Additional model cost | Measure real billed usage; zero model calls in a synthetic suite is not a measured provider bill |
| Quality improvement over baseline | Matched model/version, permission and source SHA, multiple baseline/candidate trials, independent review; otherwise NOT_MEASURED |

Metrics are not a weighted single "quality score." Negative mutations reject lost stages/requirements/AC, broken handoff, wrong revision, false test PASS, fabricated independent sessions/time, unsupported tool/client/skill claims, unauthorized egress or writes, scope creep, hidden regression, comparison leakage, missing matched pairs, mixed model versions, invented zero cost and premature release. Structure checks cannot establish subjective comprehension.

## Independent beginner usability - manual protocol

**Status until conducted: NOT_TESTED.** Recruit a real novice uninvolved in the design and a separate observer. Use a disposable sample project and a pinned Toolkit SHA. Keep logs and file snapshots privately **outside** Toolkit; never store personal information, credentials or private user source here.

Exercises: (1) begin a small project from ordinary language, (2) use an existing IDE project with a single Toolkit URL and no project URL, (3) recover from a known error, (4) resume without a duplicate side effect, (5) identify what was designed, written, tested and deployed. For chat-only clients also test ZIP+URL and tool limitations. Record exact client version/mode/OS, user terminal interactions, extra questions, approvals, actual diff (including ignored files), errors and the next action. Goals such as at most 10 minutes, 2 blocking questions and 0 terminal commands are **project targets**, not observations.

Private result template:

    Anonymous session / independent observer IDs:
    UTC start and end timestamps / measured duration:
    Toolkit SHA / client name, version, mode, OS, capabilities:
    Initial disposable project snapshot / verbatim task:
    User actions / terminal use / blocking questions:
    Preview, authorized apply, status / real diff including untracked files:
    Actually read source / discovered Skill / invoked Skill / executed tests:
    Errors, recovery, repeat run, limitations, independent judgment:
    PASS | FAIL | NOT_TESTED | BLOCKED | INCONCLUSIVE

## Future paired Skill Eval - separately blocked

Reuse [Issue #11](https://github.com/MikeMoore1337/ai-development-toolkit/issues/11), [REAL_AGENT_PILOT.md](REAL_AGENT_PILOT.md) and [SKILL_EVALS.md](SKILL_EVALS.md). Do not edit the execution freeze in scripts/agent_eval_runner.py and do not call another CLI to bypass it.

Future permission requires a **new specific owner decision**, independent safety review, confirmed zero additional cost with no risk of automatic overage, isolated non-production environment and verified client versions and permissions. Hold task, SHA, model/version, granted tools, dataset and rubric constant; run multiple matched baseline without Skill and candidate with Skill trials, independent hidden oracle and human review. Separately prove actual Skill discovery/activation, measure failures, regression, unauthorized actions, unnecessary diff, duration and real cost. Never pool different models or hide failed attempts. Private traces remain outside Toolkit. Synthetic Go/Python/JavaScript offline smoke is not live Codex/Claude evaluation.

The owner previously reported successful ZIP + Toolkit URL use in ChatGPT, Claude, DeepSeek and Qwen (**OWNER_REPORTED_PASS**). Full technical traces, client versions, independent review, actual Skill invocation and baseline are **NOT_ATTACHED**. Do not promote this report to L4 discovery, L5 invocation or L6 effectiveness.

## Review and release handoff

READY_FOR_REVIEW denotes that the synthetic package may be reviewed; READY_FOR_OFFLINE_RELEASE additionally needs an exact-HEAD successful required CI and separate release safety gates. BLOCKED, NEEDS_WORK and INCOMPLETE_EVIDENCE remain valid. Never declare FULLY_VERIFIED while live evidence is missing.

The PR must state exact branch/base SHA, CI per OS/version for that HEAD, matrix, mutations, validated or missing evidence, known blockers and provenance checks. **Do not merge, publish, deploy, close #70 or close roadmap #42 without separate authorization.** Source-only readiness is not an empirical claim about AI model quality.

Related sources: [beginner workflow](BEGINNER_WORKFLOW.md), [quality rubric](QUALITY_RUBRIC.md), [release policy](RELEASE_PROCESS.md), [provenance](PROVENANCE_AUDIT.md), [tool permissions](TOOL_INTEGRATIONS.md), [client compatibility](CLIENT_COMPATIBILITY.md), [portability scenarios](PORTABILITY_EVAL_SCENARIOS.md).
