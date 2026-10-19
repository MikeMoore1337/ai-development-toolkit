# Curated Skill Packs

These packs reuse MANIFEST.json profiles and existing skill folders. No new
package manager, skill runtime, dependencies or automatic installation is introduced.

## Choose a task

| Task | Primary profile | Skills | Optional additions, never installed automatically |
| --- | --- | ---: | --- |
| Backend services, REST APIs | `backend` | 5 | `contract-testing`, `database-validation`, `release-safety` |
| Frontend components / UI | `frontend` | 5 | `screenshot-fidelity`, `motion-quality`, `playwright-testing` |
| Python API autotests | `qa-python` | 7 | `qa-ci` profile for CI failures |
| Playwright UI tests | `qa-ui` | 5 | Separate `qa-ci` when relevant |
| Contract and integration tests | `qa-contract` | 4 | Add more only by task |
| CI investigation | `qa-ci` | 4 | None |
| Release QA | `qa-release` | 4 | None |
| Agent design and architecture | `agent-architecture` | 4 | `security-boundaries`, `external-skill-review` |
| Technical research | `research` | 2 | `codebase-knowledge-map` for large repositories |
| LLM API provider research | `provider-research` | 2 | No paid API required |

## Backend Development

**Primary:** `backend` = `task-scoping`, `architecture-decisions`, `implementation`,
`qa-strategy`, `code-review`. Suitable for architecture, source modifications,
refactoring and tests for API/services. Optional contract and database validation
are needed only when those boundaries exist. Do not assume Python, FastAPI,
Django, SQLAlchemy or PostgreSQL. For QA-only work choose a QA profile instead.

## Frontend Development

**Primary:** `frontend` = `task-scoping`, `design-system-consistency`,
`implementation`, `qa-strategy`, `code-review`. For existing design-system UI
components and frontend review without assuming React, Next.js or Tailwind.
For a narrow task prefer existing `ui-fix` or `ui-motion` instead.
Add `screenshot-fidelity` only with reference evidence, `motion-quality` only
for animation, and `playwright-testing` only with a usable Playwright stack.
Not for backend work or inventing a new design system.

## QA Engineering

Reuse existing `qa-core`, `qa-python`, `qa-fullstack`, `qa-ui`, `qa-ci`,
`qa-contract`, `qa-release`, `qa-security`, `qa-management` and `qa-collaboration`.
Use one focused profile per task. Avoid `qa-all` in ordinary projects.
QA sources remain subject to existing provenance/owner-snapshot constraints.
Don't assume every project has Playwright or pytest.

## Agent Engineering

Reuse `agent-architecture` = `architecture-decisions`, `agent-framework-fit`,
`codebase-knowledge-map`, `qa-strategy`. Add `security-boundaries` for trust
boundaries and `external-skill-review` before third-party imports. Use
`provider-research` separately for LLM APIs. No Hermes runtime or agent
framework is installed or mandated. Not a live security/agent behavior test.

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
