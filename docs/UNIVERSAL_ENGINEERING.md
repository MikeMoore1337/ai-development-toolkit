# Universal engineering skills

The core skills remain general-purpose. These three new packs add focused
engineering guidance without introducing dependencies, runtimes, repository
modifications or automatic installation.

| Pack | Source directory | Focus | Skills |
| --- | --- | --- | ---: |
| Frontend | `extensions/frontend/skills/` | UI components, state, integration, forms, performance | 5 |
| Backend | `extensions/backend/skills/` | Service contracts, persistence, jobs, access boundaries | 6 |
| Fullstack | `extensions/fullstack/skills/` | Layer handoffs, diagnosis, vertical design | 3 |
| QA (existing) | `extensions/qa/skills/` | Independent verification and test strategy | 27 |

## Task activation and non-overlap

- `component-architecture` owns component contracts, not visual style; use
  `design-system-consistency` for the latter.
- `frontend-api-integration` owns the UI consumer seam;
  `api-design` owns producer contract design;
  `contract-testing` is QA test implementation for that contract.
- `state-management` owns client state; `data-access` owns persistence.
- `end-to-end-feature-design` maps a vertical feature slice but is not an
  orchestrator; use just one of `feature-delivery` and `make-feature` when
  a workflow controller is actually needed.
- `cross-layer-debugging` diagnoses a concrete failure;
  QA `failure-triage` classifies failing tests and CI.
- `authentication-authorization` defines backend enforcement while
  `security-review` and `security-testing` provide independent QA scrutiny.
- `database-migrations` never authorizes production migrations or irreversible
  data changes. Project approval gates override every skill.

These are task-specific skills, not agents or complete framework tutorials.
They do not require Python, JavaScript, TypeScript, React, Spring, Django,
a particular database, paid APIs, or a deployed service.

## Example selection

| Task | Profile | Focused optional addition |
| --- | --- | --- |
| Implement an existing service endpoint | `backend` | `authentication-authorization` for access changes |
| Add a form to a web UI | `frontend` | `forms-validation` |
| Debug a network-to-database mismatch | `fullstack` | `cross-layer-debugging` |
| Change persisted schema | `backend` | `database-migrations` |
| Add async job | `backend` | `background-processing` |
| Design or run regression tests | `qa-core` or focused QA profile | Existing QA pack |

## Use without modifying a project

```bash
python scripts/recommend_profile.py --target /path/to/project --task fullstack
python scripts/skill_manager.py catalog --profile frontend
python scripts/skill_manager.py install --target /path/to/project --profile backend
python scripts/skill_manager.py install --target /path/to/project --profile backend --apply
python scripts/install.py --target /path/to/project --skills database-migrations
```

Installers use a preview by default and preserve project-level `AGENTS.md`
and `CLAUDE.md`. Reinstalling overlapping managed skills is not implicit
profile composition; use the manager's explicit ownership and diff workflow.

## Acceptance and limitations

Static checks validate names, manifest coverage, file links, source hashes,
pack coexistence and installation behavior. They do **not** prove runtime
correctness, agent activation, code quality or cross-framework effectiveness.
Evaluate those claims in real projects or controlled independent client trials
and preserve the observed results.
