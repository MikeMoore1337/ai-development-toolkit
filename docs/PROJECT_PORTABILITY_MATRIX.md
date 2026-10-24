# Five-project QA and UX/UI portability matrix (Issue #300)

[Русская версия](ru/PROJECT_PORTABILITY_MATRIX.md) · [Read-only project preflight](PROJECT_ADOPTION_PREFLIGHT.md) · [QA change impact](QA_CHANGE_IMPACT.md) · [UX/UI evidence limits](UX_UI_EVALS.md)

This test is **synthetic and offline**, not an independent real-client or deployed-product pilot. It does not inspect or modify any actual user or employer repository. Five reusable project definitions are frozen at `main@3fb90c41162da1cb4f0fb58c15dc72729feb5703` in [the case file](../fixtures/project_portability_20261024.json). Case selection and acceptance criteria are assistant-authored; no independent human validation is claimed.

| Type | Project markers | QA expectation | Risk selection | Visual phase |
| --- | --- | --- | --- | --- |
| Python backend | pyproject, pytest | `qa-python` | API contracts, negative requests, database forward/rollback | Not applicable |
| Frontend UI | package, Playwright config | `qa-ui` | UI state, browser flow | New site: **three directions**, mandatory human review |
| Fullstack | pyproject, package, Playwright config | `qa-fullstack` | UI/API/DB, migration rollback, cross-layer | Major redesign: **three directions**, mandatory human review |
| Agent service | pyproject | `qa-python` | Queue retry/idempotency and authorization/privacy boundaries | Not applicable |
| Docs-heavy | README/policy/docs | `qa-core` | Documentation review; **no executable tests inferred** | Not applicable |

## Reproduce without credentials

```bash
python scripts/project_portability_matrix.py
python -m unittest tests.test_project_portability_matrix -v
```

The script creates five **temporary marker-only folders** using Python standard-library `TemporaryDirectory`. It invokes the existing read-only `project_adoption_preflight.inspect` and `qa_change_impact.plan` using **only filenames and a supplied synthetic changed-path list**, then checks project snapshots are byte-identical before/after. It checks the existing `ux_ui_evals.catalog` for both visual scenario gates; it does **not** produce a browser screenshot, render a design or record owner approval. An absent or altered critical QA check or visual gate is a **failure**, not a silent `PASS`.

Every change-impact check is still `NOT_RUN`; each project's policies remain `PRESENT_UNREAD`, not verified for meaning. The report labels discovery/use `NOT_RUN`, real L6 improvement `NOT_MEASURED`, rendered design `NOT_PRODUCED` and human approval `NOT_OBSERVED`. No install, client activation, source changes in target repositories, model/API calls or production deployment occurred. Tests demonstrate **cross-archetype static routing and denial behaviors only**.

Do not replace the independent portability trials recommended in [QA_PORTABILITY.md](QA_PORTABILITY.md) with these synthetic results. If real-client testing is ever authorized, use isolated neutral fixtures, actual test oracles, browser captures and independent visual acceptance rather than reusing these labels as an accuracy benchmark.
