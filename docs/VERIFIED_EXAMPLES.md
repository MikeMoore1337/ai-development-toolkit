# Four reproducible, zero-cost Toolkit examples

[Русская версия](ru/VERIFIED_EXAMPLES.md) · [Beginner workflow](BEGINNER_WORKFLOW.md) · [Client capabilities](CLIENT_CAPABILITIES.md)

These commands use only checked-in Toolkit source, Python 3.12+ and installed development dependencies. They **do not** install Skills, invoke a model, access a private project, modify a repository, or run a deployment. In `tests/test_verified_examples.py`, CI executes the exact four commands and checks the shape of their results. CI success applies to the runner and revision it tested, **not** to every AI client.

Run from the repository root after `python -m pip install -r requirements-dev.txt` (this downloads the pinned PyYAML dependency; omit installation if your environment already has it). For Python 3.14 on Windows use `py -3.14` in place of `python`.

## Example 1 — discover profiles without installation

```bash
python scripts/adt.py --json profile list
```

Expected: valid JSON with a `profiles` object. **Does not** install, route a request in an AI client or verify runtime activation. CLI execution on the test runner: checked; native client activation: **NOT_TESTED**.

## Example 2 — curated lexical routing self-check

```bash
python scripts/skill_routing_eval.py --strict
```

Expected: exit code 0 when existing curated checks pass. These tests are offline lexical checks, not LLM semantic precision, user effectiveness or a live client invocation. Source-only validation: checked; real AI task: **NOT_RUN**.

## Example 3 — untuned RU/EN routing diagnostic

```bash
python scripts/skill_routing_eval.py --holdout fixtures/skill_routing_untuned_20261024.json
```

Expected: diagnostic JSON with `count=16`, split by language and task type. Partial matches are **not** a build failure or calibrated semantic accuracy. Human-independent gold labels: **NOT_VERIFIED**; client skill selection: **NOT_OBSERVED**.

## Example 4 — synthetic QA evidence validator

```bash
python scripts/validate_qa_orchestration.py fixtures/qa_orchestra_valid.json
```

Expected: internally consistent **synthetic** report and exit 0. No browser, tests, agent, database, or target environment has actually been exercised. Actual project test status: **NOT_RUN**.

## Evidence and safety boundaries

- Verification: `tests/test_verified_examples.py` invokes all four commands using Python and enforces read-only behavior. `tests/test_supply_chain_pins.py` verifies immutable GitHub Action commit pins across workflow files and the PyYAML version.
- The GitHub Actions `uses` entries are pinned by **commit SHA**, resolved from the official upstream tags on 2026-10-24. An immutable SHA controls action revision drift but is **not** code-signature verification or a guarantee that upstream source is safe.
- `requirements-dev.txt` pins `PyYAML==6.0.3` to avoid time-varying resolver choice across Linux, macOS and Windows (including Python 3.14). CI still obtains packages from the configured package index; wheel provenance and whole-environment reproducibility are **not fully verified**.
- No screenshots, real integrations, client behavior or cost savings are claimed from offline fixtures. Before adapting any example to a real project, follow the target project's permissions and existing QA/release gates.
