# Skills, Roles & Profiles Quality Audit (Issue #26)

## Scope and trust boundaries

Base reviewed: `main` at `655dbd5b9c93e3829a6e9428c680205f8db723d4` (2026-10-19).
Declared inventory: **51 skills** (23 Core, 27 QA, 1 Make Feature), **16 reference roles**
(5 Core, 11 QA), **23 profiles**. These counts are audit snapshots, not validator constants.
The structural `skills-ref` gate and Skill Manager remain independent and unchanged.

Precedence: real target-project rules and owner approval always override reusable
instructions. A skill is guidance only: it cannot grant tool capabilities, secrets,
production deployment, merge rights, external API access or agent delegation.
Report verified evidence separately from planned tests and model assertions.

## Confirmed changes

| Severity | Location | Finding and response |
|---|---|---|
| INFO | `docs/INTEGRATION_MATRIX.md` | Backend row referred to deprecated `adaptive-delivery`; now recommends the current `feature-delivery`. |
| BLOCKER (regression class) | `scripts/validate_pack.py` | Existing link checker examined only SKILL.md, omitted anchor verification and full reference files. Added separate deterministic `scripts/validate_quality.py`; did not change existing public CLI. |
| BLOCKER (regression class) | `MANIFEST.json` profiles | Selection was inventory-checked but no machine-readable forbidden-workflow gate existed. Added explicit `docs/QUALITY_RULES.json` and independent profile validation. |

The latter two rows describe missing regression protections, not proof that an
existing profile was already invalid. Only positive reproductions in a concrete
file or fixture count as demonstrated compatibility defects.

## Explicit workflow compatibility

| Group | Responsibilities and choice |
|---|---|
| `feature-delivery`, `make-feature` | Choose **exactly one** top-level feature controller for a single task. Make Feature can have additional state/delegation conventions; neither overrides the target project. |
| `adaptive-delivery` | Legacy reference only; don't combine with either feature controller. Existing files retained for backwards compatibility. |
| `implementation`, `minimal-safe-change` | Compatible **helpers** to the chosen controller: implementation makes bounded changes, minimal-safe-change limits risk/scope. Not independent controllers. |
| `clear-voice`, `editorial-naturalness`, `qa-clear-voice` | Select clear-voice for broader editorial fidelity, editorial-naturalness for short generic edits, qa-clear-voice for QA evidence. Avoid redundant stylistic stacking; not a CI blocker. |
| `qa-strategy`, `test-strategy` | Core risk-based verification vs QA-pack architecture/test-layer strategy. Compatible where architecture and execution plans both matter. |
| `test-analysis-design`, `test-review`, `qa-code-review`, `quality-gate-assessment` | Test design, independent oracle review, maintainability of test code, and final release evidence respectively. They can coexist. |
| `security-boundaries`, `security-review`, `security-testing`, `external-skill-review` | Trust boundaries; CI/test automation threat review; negative security test design; third-party skill provenance and permissions. Select by actual target. |
| `agent-framework-fit`, `codebase-knowledge-map`, `skill-portability`, `provider-reality-check` | Orchestration decision, repository graph, skill package migration, and current provider evidence. Combine only for genuine cross-cutting decisions. |

Only documented **hard** conflicts belong in `QUALITY_RULES.json`.
Soft overlap or similar vocabulary is not evidence of an instruction conflict.

## Role boundaries and evidence handoff

`orchestrator` chooses one controller, owns scope/handoffs, and cannot grant
merge/deploy authority. `implementer` changes code. `reviewer` and
`qa-verifier` provide independent inspection only when distinct verification
really occurred. `researcher` resolves bounded unknowns. QA reference roles
specialize failure diagnosis, coverage, requirement analysis, test design,
test implementation, test review, CI investigation and release gate review.
They are *not* runnable background processes or a new agent hierarchy.
Across roles, handoff must identify paths, executed checks, evidence and unknowns.

## Example task -> suggested profile

This table documents **human selection**. `recommend_profile.py` remains a
conservative, read-only directory/marker heuristic; it does not understand
natural-language task intent or prove successful activation.

| Task | Suggested profile | Rationale |
|---|---|---|
| Python API implementation | `general` | Bounded software change; add API skills only for explicit tests |
| pytest tests | `qa-python` | Python test fixtures/oracles |
| Playwright UI tests | `qa-ui` | Browser-specific QA when Playwright confirmed |
| flaky CI | `qa-ci` | Failure triage and nondeterminism |
| backend refactor | `general` | Implementation and regression boundaries |
| new feature | `codex-feature` or `make-feature` | Exactly one controller chosen explicitly |
| screenshot UI fix | `ui-fix` | Visual fidelity and design system |
| release review | `qa-release` | Evidence and coverage |
| security audit | `qa-security` | Test-centered security; add `security-boundaries` for architectural trust review |
| documentation editing | `editorial` | Style/fidelity; use `documentation-maintenance` for technical correctness |
| AI provider selection | `provider-research` | Source-backed costs/availability |
| agent architecture | `agent-architecture` | Framework fit and source map |

A fixed-task recommender cannot distinguish Python API development from pytest
test writing or a security audit solely by detecting `pyproject.toml`.
Avoid presenting such recommendations as verified user intent.

## Offline checks and limitations

`python scripts/validate_quality.py` examines declared inventory, profiles,
the explicit exclusive-workflow rules and Markdown links under skills, roles,
references, project documentation and root guides. It recognizes relative and
percent-encoded paths, Markdown heading anchors (including duplicates), code
fences, inline code, Markdown reference definitions and external HTTP links.
Unsafe paths and missing local files are BLOCKERs. JSON output includes
`rule_id`, `severity`, `file`, `line` and `explanation`; result order is
stable. Invalid/missing quality-rule configuration is itself a BLOCKER.

Reproduce: `python scripts/validate_quality.py` and
`python -m unittest discover -s tests -p test_quality_gate.py -v`.
The existing Windows and Linux CI matrix runs the same gate. External URL
checks remain **outside mandatory CI**; 404/410, 401/403, 429, timeouts and
network restrictions cannot safely be treated as equivalent failures.

Not proved by this audit: actual Codex/Claude/Hermes skill activation,
independent agent review, improved generated code, full semantic consistency
of free-form text, current external link availability, upstream legal rights
or production deployment. Real agent trials remain in **Issue #11**.

Manual follow-up: re-check skill descriptions and task-selection behavior
after substantive changes, and spot-check external official URLs with bounded,
SSRF-safe tooling only when authorized. No paid service or VPS is needed.
