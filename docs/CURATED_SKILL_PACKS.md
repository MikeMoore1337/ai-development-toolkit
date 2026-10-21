# Curated Skill Packs

[Русская версия](ru/CURATED_SKILL_PACKS.md)

These packs reuse MANIFEST.json profiles and existing skill folders. No new
package manager, skill runtime, dependencies or automatic installation is introduced.

## Choose a task

| Task | Primary profile | Skills | Optional additions, never installed automatically |
| --- | --- | ---: | --- |
| Backend services, REST APIs | `backend` | 7 | `data-access`, `database-migrations`, `background-processing`, `authentication-authorization` |
| Frontend components / UI | `frontend` | 7 | `state-management`, `forms-validation`, `frontend-performance` |
| Fullstack feature integration | `fullstack` | 6 | `cross-layer-debugging`, `contract-testing`, `e2e-testing` |
| Python API autotests | `qa-python` | 7 | `qa-ci` profile for CI failures |
| Playwright UI tests | `qa-ui` | 5 | Separate `qa-ci` when relevant |
| Contract and integration tests | `qa-contract` | 4 | Add more only by task |
| CI investigation | `qa-ci` | 4 | None |
| Release QA | `qa-release` | 4 | None |
| Accessibility QA: keyboard, focus, forms, contrast and WCAG | `accessibility-qa` | 4 | Offline examples; optional real browser and AT checks |
| Incident investigation, telemetry quality, SLI/SLO and recovery | `observability-sre` | 5 | Offline synthetic oracles, owner gate for infrastructure |
| Library upgrades, lockfile and rollback | `dependency-maintenance` | 5 | Evidence-first; no automatic updates |
| CI/CD, containers, infrastructure and deployment planning | `devops-infrastructure` | 4 | Offline synthetic checks only; no cloud or Docker required |
| Threat modeling, security architecture and DevSecOps | `security-engineering` | 4 | Offline synthetic tests; no external scans |
| Bounded load, performance budgets and regressions | `performance-load-testing` | 3 | Synthetic local tests only; no external traffic |
| Stateful reliability, retry, duplicates and recovery | `reliability-testing` | 4 | Invariants, bounded synthetic fault tests; no production chaos |
| AI evaluation, RAG or prompt/tool-use regression | `ai-engineering-qa` | 5 | Reuse QA contracts and security guidance; no real model call |
| Agent design and architecture | `agent-architecture` | 4 | `security-boundaries`, `external-skill-review` |
| Idea validation, MVP scope and PRD | `product-discovery` | 3 | Formal QA requirements analysis only when needed |
| Business rules, use cases and system requirements | `business-system-analysis` | 4 | Add `api-design` only for actual interface contracts |
| UX/UI flows, wireframes and handoff | `ux-design` | 4 | `screenshot-fidelity` / `motion-quality` for actual visual or motion tasks |
| Delivery plan, dependencies and risk review | `project-delivery-management` | 4 | Add a feature controller separately only when implementing |
| Technical research | `research` | 2 | `codebase-knowledge-map` for large repositories |
| LLM API provider research | `provider-research` | 2 | No paid API required |

## Business & System Analysis

Optional business/system profile: one new skill plus task-scoping, requirement-analysis and requirements-traceability. It keeps source R/AC identifiers, represents unknowns explicitly, and hands off to UX/UI, Backend, Frontend and QA. [Guide](BUSINESS_SYSTEM_ANALYSIS.md). No second controller or full QA Pack.

## UX/UI Design

Optional `ux-design` composes one process skill with existing design-system and component architecture guidance. It preserves R/AC/UC links, describes reachable screens and prepares a verifiable handoff, not implemented code. [Guide](UX_UI_DESIGN.md).

## AI Engineering & QA

The optional `ai-engineering-qa` profile adds one AI-specific skill and reuses `research-verification`, `security-boundaries`, `test-analysis-design`, and `contract-testing`. It provides deterministic offline checks and does not claim real model effectiveness, RAG semantics or autonomous execution. [Guide](AI_ENGINEERING_QA.md).

## Accessibility QA

Optional `accessibility-qa` combines one specialist skill with existing QA test-design, optional Playwright and quality-gate guidance. [Guide](ACCESSIBILITY_QA.md). Offline checks never claim WCAG conformance.

## Observability & SRE

The optional `observability-sre` profile adds one evidence-led skill and reuses triage, release-safety, security and reliability. [Guide](OBSERVABILITY_SRE.md). No mandatory monitoring stack, live access or new controller.

## DevOps & Infrastructure

The optional `devops-infrastructure` profile combines one specialized skill with existing release, security-boundary and architecture guidance. It prepares CI/CD and IaC plans without running deployments. [Guide](DEVOPS_INFRASTRUCTURE.md).

## Security Engineering

Optional `security-engineering` profile combines one threat-modeling skill with `security-boundaries`, `security-review` and `security-testing`. It maps boundaries to risks, testable controls and residual risk. [Guide](SECURITY_DEVSECOPS.md). No scanner or live network calls.

## Performance & Load Testing

The optional `performance-load-testing` profile adds one specialist skill and reuses `test-strategy` and `failure-triage`. It checks bounded workload models, metrics, budgets, functional oracles and cross-version comparability. [Guide](PERFORMANCE_LOAD_TESTING.md). Local synthetic example only, no production traffic or paid services.

## Reliability Testing

The optional `reliability-testing` profile adds one specialist skill and reuses `background-processing`, `integration-testing` and `failure-triage`. Offline independent state oracles reject known broken implementations, without claiming real broker guarantees or exactly-once. [Guide](RELIABILITY_TESTING.md).

## Backend Development

**Primary:** `backend` includes existing implementation and review guidance,
plus `service-architecture` and `api-design`. Add `data-access`,
`database-migrations`, `background-processing` and
`authentication-authorization` only when the change touches those boundaries.
These skills do not assume Python, Go, Java, .NET, any framework or database.
For QA-only work choose an existing QA profile.

## Frontend Development

**Primary:** `frontend` includes existing UI design, implementation and review
guidance, plus `component-architecture` and `frontend-api-integration`.
Add `state-management`, `forms-validation` or `frontend-performance`
only for those concerns. No React, Vue, Angular, Svelte, TypeScript or CSS
framework is mandated. For narrow visual work prefer `ui-fix` or
`ui-motion`; use screenshot and motion checks when there is relevant evidence.

## Fullstack Development

**Primary:** `fullstack` includes `end-to-end-feature-design` and
`fullstack-integration` alongside general planning, coding and review.
Add `cross-layer-debugging` for failures crossing layers, plus specific
Frontend, Backend or QA skills only where the task needs them. This is a
cross-layer contract profile, **not** a replacement for a feature-delivery
controller. Choose only one of `feature-delivery` or `make-feature` when
a separate orchestrated feature workflow is desired.

[Universal engineering skill inventory](UNIVERSAL_ENGINEERING.md) explains
activation boundaries, stack-neutrality and acceptance examples.

## QA Engineering

Reuse existing `qa-core`, `qa-python`, `qa-fullstack`, `qa-ui`, `qa-ci`,
`qa-contract`, `qa-release`, `qa-security`, `qa-management` and `qa-collaboration`.
Use one focused profile per task. Avoid `qa-all` in ordinary projects.
QA sources remain subject to existing provenance/owner-snapshot constraints.
Don't assume every project has Playwright or pytest.

### Optional advanced QA methods

Keep using existing `test-analysis-design`, `test-management` and `database-validation` skills. These techniques are **conditional guidance**, not new skills, profiles or dependencies.

| Situation | Useful technique | Independent check / limit |
| --- | --- | --- |
| Large input domain with clear invariants | **Property-based testing** | Generate varied inputs and assert a specified invariant (e.g. parse/serialize round-trip); ensure the invariant comes from the contract, not the implementation. No Hypothesis dependency is assumed. |
| Exact expected output is hard to enumerate | **Metamorphic testing** | Apply a transformation with a known relation: reordering independent records should not change an aggregate; first confirm independence is a business rule. |
| Stateful workflow with many allowed/forbidden sequences | **Model-based testing** | Build a small reference state machine; compare system transitions, including retries, denied actions and recovery. Avoid a duplicate model derived blindly from the same product code. |
| Critical deterministic logic has tests but may still be weak | **Mutation testing** | Change one rule in a disposable copy; a meaningful existing assertion should fail. Use sparingly, never mutate production or set a universal mutation-score threshold. |

For managed automated tests, **identity follows the tested behavior**: preserve a stable external ID for rename/move with the same oracle; after a split only the successor covering the original behavior may retain that ID; on merge, reconcile retired IDs against the external tracker without deleting history or creating duplicates. Jira, Test IT and test synchronizers remain optional and require explicit write authorization.

For database audits, distinguish **read-only metadata queries** from calling user-defined functions or procedures. `SELECT some_function()` may have side effects; a later `ROLLBACK` does not undo every sequence allocation or external effect. Examine permissions, environment, function bodies and downstream effects before execution. PostgreSQL-specific catalog queries belong only in PostgreSQL tasks. Prefer an authorized isolated test environment and independently observed state, never production credentials.

These are decision aids: keep routine tests small and risk-driven. Compare **actual agent behavior and evidence**, not a keyword score, using [bilingual QA scenarios](SKILL_ROUTING_EVALS.md#manual-qa-behavior-checks-ruen-prompts).

## Agent Engineering

Reuse `agent-architecture` = `architecture-decisions`, `agent-framework-fit`,
`codebase-knowledge-map`, `qa-strategy`. Add `security-boundaries` for trust
boundaries and `external-skill-review` before third-party imports. Use
`provider-research` separately for LLM APIs. No Hermes runtime or agent
framework is installed or mandated. Not a live security/agent behavior test.

## Product Discovery

The optional `product-discovery` profile combines one new product skill with existing
`task-scoping` and `research-verification`. Its output is a proposed PRD and
falsifiable hypotheses, not implemented code or validated market demand.
[Beginner/expert guide](PRODUCT_DISCOVERY.md). No paid API or new installer.

## Research & Analysis

**Primary:** `research` = `task-scoping`, `research-verification`.
Use for verifiable general technical comparisons and evidence-based decisions.
Add `codebase-knowledge-map` for large repositories. Prefer the existing
`provider-research` for provider terms and availability checks. Neither
profile requires paid LLM/search API calls. No unverifiable freshness claims.

## Preview and install

```bash
python scripts/recommend_profile.py --target /path/to/project --task backend
python scripts/recommend_profile.py --target /path/to/project --task frontend
python scripts/recommend_profile.py --target /path/to/project --task fullstack
python scripts/recommend_profile.py --target /path/to/project --task research
python scripts/recommend_profile.py --target /path/to/project --task provider
python scripts/skill_manager.py catalog --profile backend
python scripts/skill_manager.py install --target /path/to/project --profile backend
python scripts/skill_manager.py install --target /path/to/project --profile backend --apply
python scripts/skill_manager.py install --target /path/to/project --profile frontend --layout claude
python scripts/skill_manager.py status --target /path/to/project
python scripts/skill_manager.py update --target /path/to/project
python scripts/skill_manager.py uninstall --target /path/to/project --skills code-review
python scripts/skill_manager.py rollback --target /path/to/project
python scripts/skill_manager.py recover --target /path/to/project
python scripts/profile_metrics.py --profile backend
python scripts/profile_metrics.py
```

All mutations require `--apply`; preview does not write. The manager tracks
owned installed skills using independent Codex (`.agents/skills`) and Claude
Code (`.claude/skills`) layouts and lockfiles. Reapplying a profile with
overlapping installed skills is intentionally rejected, not merged silently.
To change composition, preview `uninstall --skills ...` for no-longer-needed
owned skills and `install --skills ...` for genuinely new skills. `update`
updates owned contents only; it does not reconcile profiles. Never delete
or overwrite unmanaged or locally modified skills to work around collisions.
Backup and review first. See [INSTALLATION.md](INSTALLATION.md) and
[CLIENT_MIGRATION.md](CLIENT_MIGRATION.md) for rollback and recovery.
Existing `AGENTS.md` / `CLAUDE.md` are never modified. Custom layout
supports only the simple installer, not Skill Manager ownership.

## Exclusions, compatibility and measurements

Never activate `feature-delivery` with `make-feature`; never combine legacy
`adaptive-delivery` with either. See [QUALITY_RULES.json](QUALITY_RULES.json).
Editorial skills should be selected only for editorial tasks. Project-specific
constraints and approval gates take priority over universal profiles.

`scripts/profile_metrics.py` counts installed file bytes, root SKILL.md bytes,
reference files, profile intersections and skill count from local sources.
ToolKit-required automatic runtime dependencies are **zero**, but individual
skills may describe optional tools required by a specific task.
File bytes are not tokenizer measurements or real model context cost.

Provenance: only existing source skills are referenced, without changing
licensed snapshots. ID1337 permission is limited to exact previously pinned
source versions; neither legal review nor new distribution authorization
can be inferred. No live Codex, Claude or Hermes discovery is claimed.

## Project & Delivery Management

The optional `project-delivery-management` profile maps an existing PRD to work, dependencies, risks and observed status while reusing scoping/QA skills. No new tracker, workflow controller or automatic GitHub writes. [Guide](PROJECT_DELIVERY_MANAGEMENT.md).

### QA v2: examples and role handoffs

All 27 QA skills now ship with task-local `references/` (lazy-load only when the case calls for examples, failure oracles and handoff templates). The 11 QA roles have explicit input/output and exclusion contracts. Roles are **reference instructions**: the installer does not provision subagents. Pick the smallest task-specific profile; `qa-ui` uses Playwright only if the project actually uses it, and `qa-python` does not require pytest in other frameworks. For trivial work use one agent serially; delegate only if the client has genuinely distinct workers and file ownership does not conflict. Never call self-review independent. Reports stay in chat by default; no external API or paid runtime. See [QA Pack](../extensions/qa/README.md), [portability](QA_PORTABILITY.md), and [role contracts](../extensions/qa/roles/qa-architect.md).

## Dependency maintenance

The opt-in `dependency-maintenance` profile reuses existing skills. [Guide](DEPENDENCY_MAINTENANCE.md).
