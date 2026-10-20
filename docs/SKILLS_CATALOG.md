# Skills, roles & profiles

[Русская версия](ru/SKILLS_CATALOG.md)

A maintained reference based on `MANIFEST.json` and the actual `SKILL.md` files in this distribution. The current quantities are checked against the manifest by the offline quality gate. Descriptions summarize source metadata; availability depends on the selected client and installation profile.

## Core skills

These 23 skills live under `.agents/skills/`.

| Skill | When to use it |
| :--- | :--- |
| [`adaptive-delivery`](../.agents/skills/adaptive-delivery/SKILL.md) | Legacy v3 scope-size routing guide kept for backward compatibility. For new feature implementation prefer feature-delivery rather than activating both workflows. |
| [`agent-framework-fit`](../.agents/skills/agent-framework-fit/SKILL.md) | Evaluate whether an agent orchestration framework is justified before proposing LangGraph, CrewAI, DeerFlow or a complete agent runtime. Use for multi-agent architecture… |
| [`architecture-decisions`](../.agents/skills/architecture-decisions/SKILL.md) | Compare design alternatives for a cross-cutting or high-impact change without unnecessary infrastructure. Use before changing major component boundaries. |
| [`browser-workflow-evidence`](../.agents/skills/browser-workflow-evidence/SKILL.md) | Run browser-based tasks with verifiable outcomes and transparent limitations. Use for UI automation, browser agents and externally hosted flows. |
| [`clear-voice`](../.agents/skills/clear-voice/SKILL.md) | Пиши, проверяй и редактируй естественные тексты на русском языке (и при необходимости на английском), сохраняя проверяемые факты, авторский голос, условия и формат. Испол… |
| [`code-review`](../.agents/skills/code-review/SKILL.md) | Review a proposed code diff for correctness, regressions, compatibility, security and maintainability. Use for independent change review. |
| [`codebase-knowledge-map`](../.agents/skills/codebase-knowledge-map/SKILL.md) | Map large repositories, dependency flows and component boundaries when ordinary code search is insufficient. Use for change impact analysis and architecture discovery. |
| [`design-system-consistency`](../.agents/skills/design-system-consistency/SKILL.md) | Audit or implement interfaces without breaking an existing design system. Use for dashboards, mobile web, PWA, screens and design-to-code tasks. |
| [`documentation-maintenance`](../.agents/skills/documentation-maintenance/SKILL.md) | Create or update accurate project documentation and usage instructions. Use when behavior, configuration, public contracts or runbooks change. |
| [`editorial-naturalness`](../.agents/skills/editorial-naturalness/SKILL.md) | Edit user-facing product copy and professional Russian or English text for clarity without changing facts. Use for documentation, UI copy and announcements. |
| [`external-skill-review`](../.agents/skills/external-skill-review/SKILL.md) | Review third-party agent skills and tool bundles before adoption. Use for skill imports, installers, hooks, MCP scripts and repository-sourced instructions. |
| [`feature-delivery`](../.agents/skills/feature-delivery/SKILL.md) | Use for implementing a new feature or significant behavior change. Pick quick, normal or deep workflow based on risk, track acceptance criteria and prove completion witho… |
| [`implementation`](../.agents/skills/implementation/SKILL.md) | Implement a bounded source-code change while preserving project conventions and verifying changed behavior. Use for actual software implementation tasks. |
| [`minimal-safe-change`](../.agents/skills/minimal-safe-change/SKILL.md) | Prefer the smallest maintainable solution while preserving tests, security and compatibility. Use for implementation, refactoring, debugging or code review. |
| [`motion-quality`](../.agents/skills/motion-quality/SKILL.md) | Review and improve animation purpose, timing, accessibility and performance. Use when adding, auditing or optimizing web or mobile motion. |
| [`provider-reality-check`](../.agents/skills/provider-reality-check/SKILL.md) | Evaluate current LLM provider free tiers and API compatibility using official sources and reproducible checks. Use for API routing, budget estimates and free-provider sel… |
| [`qa-strategy`](../.agents/skills/qa-strategy/SKILL.md) | Choose risk-based unit, integration, contract, UI and end-to-end validation. Use for changes requiring test design or verification evidence. |
| [`release-safety`](../.agents/skills/release-safety/SKILL.md) | Prepare and verify a release or production deployment based on the real project pipeline and granted authorization. Use for release readiness, merge or deployment work. |
| [`research-verification`](../.agents/skills/research-verification/SKILL.md) | Research an unknown technical or product question, checking primary sources, freshness, uncertainty and competing options. Use when decisions depend on external facts. |
| [`screenshot-fidelity`](../.agents/skills/screenshot-fidelity/SKILL.md) | Compare UI implementations against screenshots and design references. Use for visual parity, screenshot-to-code, regressions and responsive layout checks. |
| [`security-boundaries`](../.agents/skills/security-boundaries/SKILL.md) | Review concrete trust boundaries, credentials, sensitive data and harmful failure modes. Use when a change introduces or crosses a security boundary. |
| [`skill-portability`](../.agents/skills/skill-portability/SKILL.md) | Use when creating, evaluating, importing or migrating an Agent Skills SKILL.md folder. Validate metadata, links, client compatibility, provenance and activation boundarie… |
| [`task-scoping`](../.agents/skills/task-scoping/SKILL.md) | Define the scope, constraints, acceptance criteria and dependencies of a change. Use before implementing a task with incomplete or competing requirements. |

## Frontend engineering extension

Optional, technology-neutral skills under `extensions/frontend/skills/`.

| Skill | When to use it |
| :--- | :--- |
| [`component-architecture`](../extensions/frontend/skills/component-architecture/SKILL.md) | Design component boundaries without selecting a framework. |
| [`state-management`](../extensions/frontend/skills/state-management/SKILL.md) | Track state source of truth and concurrency. |
| [`frontend-api-integration`](../extensions/frontend/skills/frontend-api-integration/SKILL.md) | Map actual API contracts to UI states. |
| [`forms-validation`](../extensions/frontend/skills/forms-validation/SKILL.md) | Build form state and validation feedback. |
| [`frontend-performance`](../extensions/frontend/skills/frontend-performance/SKILL.md) | Measure and improve real frontend bottlenecks. |

## Backend engineering extension

Optional, technology-neutral skills under `extensions/backend/skills/`.

| Skill | When to use it |
| :--- | :--- |
| [`service-architecture`](../extensions/backend/skills/service-architecture/SKILL.md) | Define bounded services and dependencies. |
| [`api-design`](../extensions/backend/skills/api-design/SKILL.md) | Specify compatible producer-side API contracts. |
| [`data-access`](../extensions/backend/skills/data-access/SKILL.md) | Protect persistence integrity and query behavior. |
| [`database-migrations`](../extensions/backend/skills/database-migrations/SKILL.md) | Plan schema evolution and recovery. |
| [`background-processing`](../extensions/backend/skills/background-processing/SKILL.md) | Define worker delivery and retry semantics. |
| [`authentication-authorization`](../extensions/backend/skills/authentication-authorization/SKILL.md) | Enforce trusted resource permissions. |

## Fullstack engineering extension

Optional, technology-neutral skills under `extensions/fullstack/skills/`.

| Skill | When to use it |
| :--- | :--- |
| [`fullstack-integration`](../extensions/fullstack/skills/fullstack-integration/SKILL.md) | Coordinate contracts and cross-layer rollout. |
| [`cross-layer-debugging`](../extensions/fullstack/skills/cross-layer-debugging/SKILL.md) | Trace faults through interface and backend. |
| [`end-to-end-feature-design`](../extensions/fullstack/skills/end-to-end-feature-design/SKILL.md) | Design a vertical feature slice with testable acceptance. |

## Product Discovery extension

Optional, stack-independent guidance for shaping product value before implementation.

| Skill | When to use |
| :--- | :--- |
| [`product-discovery`](../extensions/product/skills/product-discovery/SKILL.md) | Test the product problem and hypotheses; define MVP inclusions/exclusions, a traceable PRD and meaningful metrics before development. |

[Beginner and expert Product Discovery guide](PRODUCT_DISCOVERY.md).

## QA Engineering Pack

The QA extension is optional and not automatically installed with the Core.

| Skill | When to use it |
| :--- | :--- |
| [`api-testing`](../extensions/qa/skills/api-testing/SKILL.md) | Design API tests around contracts, state changes and failure semantics. Use for HTTP endpoints, status handling and API versioning. |
| [`change-impact-analysis`](../extensions/qa/skills/change-impact-analysis/SKILL.md) | Map a change to affected contracts, callers, state and regression tests. Use before modifying shared code, contracts, migrations or agent tools. |
| [`collaborative-development`](../extensions/qa/skills/collaborative-development/SKILL.md) | Coordinate parallel human and AI changes to tests and automation without conflicting ownership. Use when tasks share fixtures, branches or test infrastructure. |
| [`contract-testing`](../extensions/qa/skills/contract-testing/SKILL.md) | Protect service interfaces and message schemas from incompatibility. Use when API/event payloads, versions or providers change. |
| [`coverage-analysis`](../extensions/qa/skills/coverage-analysis/SKILL.md) | Assess test coverage of requirements and risks instead of relying only on line percentage. Use for release gaps and strategy reviews. |
| [`database-validation`](../extensions/qa/skills/database-validation/SKILL.md) | Validate persistence semantics and migrations without coupling to one database product. Use for schema or data integrity changes. |
| [`defect-management`](../extensions/qa/skills/defect-management/SKILL.md) | Turn reproduced product failures into actionable, evidence-backed defect reports. Use when deciding whether to create or update a bug. |
| [`e2e-testing`](../extensions/qa/skills/e2e-testing/SKILL.md) | Select high-value end-to-end scenarios and collect visible evidence. Use for critical user journeys spanning UI and backend. |
| [`failure-triage`](../extensions/qa/skills/failure-triage/SKILL.md) | Investigate failed CI jobs or tests and classify failure origin using evidence. Use when tests fail, infra is unstable or release status is ambiguous. |
| [`flaky-analysis`](../extensions/qa/skills/flaky-analysis/SKILL.md) | Determine why a test is nondeterministic and remove the mechanism. Use for intermittent failures, retries and timing-sensitive checks. |
| [`graphify-adapter`](../extensions/qa/skills/graphify-adapter/SKILL.md) | Optionally use a code graph to investigate callers, dependencies and change impact. Use only when an approved graph tool is available. |
| [`integration-testing`](../extensions/qa/skills/integration-testing/SKILL.md) | Verify behavior across real component boundaries including queues, databases and external APIs. Use for multi-service or asynchronous changes. |
| [`playwright-testing`](../extensions/qa/skills/playwright-testing/SKILL.md) | Use Playwright to build stable UI assertions, network waits and traces. Use only in Playwright-enabled web projects. |
| [`pytest-test-design`](../extensions/qa/skills/pytest-test-design/SKILL.md) | Structure deterministic Python tests with pytest fixtures and parametrization. Use only when pytest is present. |
| [`qa-clear-voice`](../extensions/qa/skills/qa-clear-voice/SKILL.md) | Improve clarity and factual precision of Russian QA reports, incident notes and test documentation. Use when rewriting QA evidence for human readers. |
| [`qa-code-review`](../extensions/qa/skills/qa-code-review/SKILL.md) | Review the quality of QA automation code, test fixtures and framework boundaries. Use for PRs changing test implementations or CI helpers. |
| [`qa-safe-change`](../extensions/qa/skills/qa-safe-change/SKILL.md) | Plan a safe, minimal QA automation change from request through verifiable handoff. Use when modifying shared test infrastructure or many test modules. |
| [`quality-gate-assessment`](../extensions/qa/skills/quality-gate-assessment/SKILL.md) | Assess merge or release readiness from acceptance criteria and actual verification evidence. Use before approving risky changes or deployments. |
| [`requirement-analysis`](../extensions/qa/skills/requirement-analysis/SKILL.md) | Translate product requests into testable outcomes and identify gaps. Use when specifications are ambiguous, incomplete, or high-risk. |
| [`requirements-traceability`](../extensions/qa/skills/requirements-traceability/SKILL.md) | Connect requirements to test cases, executions and evidence. Use when auditability or cross-team handoff is needed. |
| [`security-review`](../extensions/qa/skills/security-review/SKILL.md) | Review security of test repositories, CI pipelines and automation helpers. Use before integrating agents, external tools or new test credentials. |
| [`security-testing`](../extensions/qa/skills/security-testing/SKILL.md) | Derive negative security tests for permissions and trust boundaries. Use when access rules, session behavior, user data or agent actions change. |
| [`test-analysis-design`](../extensions/qa/skills/test-analysis-design/SKILL.md) | Design meaningful tests using partitions, boundaries, state transitions and explicit oracles. Use before automating new behavior or evaluating missed cases. |
| [`test-data-management`](../extensions/qa/skills/test-data-management/SKILL.md) | Plan isolated reproducible test data and cleanup. Use when automated tests create state or run concurrently. |
| [`test-management`](../extensions/qa/skills/test-management/SKILL.md) | Plan mappings between automated tests and test management systems without requiring any particular vendor. Use for linking requirements to test IDs and reports. |
| [`test-review`](../extensions/qa/skills/test-review/SKILL.md) | Independently assess whether tests can detect regressions and avoid false passes. Use on new or modified tests, especially before merging a risky change. |
| [`test-strategy`](../extensions/qa/skills/test-strategy/SKILL.md) | Choose a risk-based mix of unit, contract, API, integration, E2E and exploratory tests. Use when planning or revising project test architecture. |

## Feature workflow extension

| Skill | When to use it |
| :--- | :--- |
| [`make-feature`](../extensions/make-feature/skills/make-feature/SKILL.md) | Сделай мне функцию: прорабатывает и реализует функцию из короткого запроса, сохраняет решения и проверяет результат. Подбирает глубину по неопределённости и риску; отдель… |

**Important:** Select one feature workflow controller for a task. Do not run `make-feature` and `feature-delivery` simultaneously.

## Agent roles

Roles are reference instructions, not separately running programs. Installers currently copy skills only.

| Collection | Role | Reference |
| :--- | :--- | :--- |
| Core | `implementer` | [Role](../.agents/roles/implementer.md) |
| Core | `orchestrator` | [Role](../.agents/roles/orchestrator.md) |
| Core | `qa-verifier` | [Role](../.agents/roles/qa-verifier.md) |
| Core | `researcher` | [Role](../.agents/roles/researcher.md) |
| Core | `reviewer` | [Role](../.agents/roles/reviewer.md) |
| QA | `ci-investigator` | [Role](../extensions/qa/roles/ci-investigator.md) |
| QA | `coverage-analyst` | [Role](../extensions/qa/roles/coverage-analyst.md) |
| QA | `flaky-analyst` | [Role](../extensions/qa/roles/flaky-analyst.md) |
| QA | `qa-architect` | [Role](../extensions/qa/roles/qa-architect.md) |
| QA | `quality-gatekeeper` | [Role](../extensions/qa/roles/quality-gatekeeper.md) |
| QA | `requirement-analyst` | [Role](../extensions/qa/roles/requirement-analyst.md) |
| QA | `security-reviewer` | [Role](../extensions/qa/roles/security-reviewer.md) |
| QA | `test-designer` | [Role](../extensions/qa/roles/test-designer.md) |
| QA | `test-implementer` | [Role](../extensions/qa/roles/test-implementer.md) |
| QA | `test-management-analyst` | [Role](../extensions/qa/roles/test-management-analyst.md) |
| QA | `test-reviewer` | [Role](../extensions/qa/roles/test-reviewer.md) |

## Profiles

See [Curated Skill Packs](CURATED_SKILL_PACKS.md) for task navigation, optional skills and safe transitions.

A profile is simply a named selection of existing skills. Inspect before applying.

| Profile | Skills |
| :--- | :--- |
| `agent-architecture` | `architecture-decisions`, `agent-framework-fit`, `codebase-knowledge-map`, `qa-strategy` |
| `backend` | `task-scoping`, `architecture-decisions`, `service-architecture`, `api-design`, `implementation`, `qa-strategy`, `code-review` |
| `frontend` | `task-scoping`, `design-system-consistency`, `component-architecture`, `frontend-api-integration`, `implementation`, `qa-strategy`, `code-review` |
| `fullstack` | `task-scoping`, `end-to-end-feature-design`, `fullstack-integration`, `implementation`, `qa-strategy`, `code-review` |
| `product-discovery` | `product-discovery`, `task-scoping`, `research-verification` |
| `research` | `task-scoping`, `research-verification` |
| `browser-task` | `browser-workflow-evidence`, `qa-strategy` |
| `codex-feature` | `task-scoping`, `feature-delivery`, `minimal-safe-change`, `implementation`, `qa-strategy`, `code-review` |
| `docs-technical` | `documentation-maintenance`, `research-verification` |
| `editorial` | `clear-voice` |
| `editorial-qa` | `qa-clear-voice` |
| `feature-delivery` | `feature-delivery`, `minimal-safe-change`, `implementation`, `qa-strategy`, `release-safety` |
| `general` | `task-scoping`, `implementation`, `qa-strategy`, `code-review`, `minimal-safe-change` |
| `make-feature` | `make-feature` |
| `provider-research` | `research-verification`, `provider-reality-check` |
| `qa-all` | `api-testing`, `change-impact-analysis`, `collaborative-development`, `contract-testing`, `coverage-analysis`, `database-validation`, `defect-management`, `e2e-testing`, `failure-triage`, `flaky-analysis`, `graphify-adapter`, `integration-testing`, `playwright-testing`, `pytest-test-design`, `qa-clear-voice`, `qa-code-review`, `qa-safe-change`, `quality-gate-assessment`, `requirement-analysis`, `requirements-traceability`, `security-review`, `security-testing`, `test-analysis-design`, `test-data-management`, `test-management`, `test-review`, `test-strategy` |
| `qa-ci` | `failure-triage`, `flaky-analysis`, `test-data-management`, `test-review` |
| `qa-collaboration` | `collaborative-development`, `qa-safe-change`, `qa-code-review`, `test-review` |
| `qa-contract` | `contract-testing`, `integration-testing`, `api-testing`, `change-impact-analysis` |
| `qa-core` | `requirement-analysis`, `test-analysis-design`, `test-review`, `change-impact-analysis`, `quality-gate-assessment` |
| `qa-fullstack` | `requirement-analysis`, `test-analysis-design`, `test-review`, `change-impact-analysis`, `api-testing`, `contract-testing`, `integration-testing`, `e2e-testing`, `playwright-testing` |
| `qa-management` | `requirements-traceability`, `test-management`, `defect-management`, `quality-gate-assessment` |
| `qa-python` | `test-analysis-design`, `test-review`, `api-testing`, `pytest-test-design`, `database-validation`, `test-data-management`, `failure-triage` |
| `qa-release` | `change-impact-analysis`, `coverage-analysis`, `requirements-traceability`, `quality-gate-assessment` |
| `qa-security` | `security-testing`, `test-data-management`, `test-review`, `quality-gate-assessment` |
| `qa-ui` | `test-analysis-design`, `e2e-testing`, `playwright-testing`, `test-review`, `quality-gate-assessment` |
| `skill-import` | `skill-portability`, `external-skill-review`, `research-verification` |
| `ui-fix` | `task-scoping`, `design-system-consistency`, `screenshot-fidelity`, `qa-strategy` |
| `ui-motion` | `design-system-consistency`, `motion-quality`, `qa-strategy` |

See [installation](INSTALLATION.md) for dry-run, client layouts and compatibility.
