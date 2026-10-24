# Profile context: verified 3-vs-5 load and safe deduplication (#299)

[Русская версия](ru/PROFILE_CONTEXT_AUDIT.md) | [Profile source metrics](../scripts/profile_metrics.py) | [Personal MCP](../integrations/personal-mcp/README.md)

## Scope and reproducibility

This is an **offline, read-only** audit at baseline `main@f0903be39787df39584a22087329840cb4feaa4b`. It reuses the already available `scripts/profile_metrics.py`, `Toolkit.prepare_task` `context_load_metrics` (from Issue #276), and the existing Personal MCP adapter rather than modifying protected skill sources.

```bash
python scripts/profile_context_audit.py
python scripts/profile_context_audit.py --audit-duplicates --audit-directives
python -m unittest tests.test_profile_context_audit -v
```

The five **same-task** comparisons run `general`, `backend`, `fullstack`, `qa-python`, and `ui-orchestra` with no already-installed skills, identical task text and roles, and explicit `max_skills=3` versus `max_skills=5`. The report contains selected skill slugs, order, real **returned UTF-8 instruction text bytes** including a role, deferred skills, and deferred reference count. By policy, neither 3 nor 5 preloads references; all unreturned skills remain available through `toolkit_get_skill`, and references through `toolkit_get_reference`. **More source bytes are not model tokens, user latency or measurable benefit**; L4-L6 and inference cost remain `NOT_MEASURED` / `NOT_RUN`.

## Findings and actual fix

- Source overlap: `general` / `backend` / `fullstack` share the `implementation` and `qa-strategy` skills where appropriate. Shared membership **is not duplicate loading within a single request**. The adapter de-duplicates selected skill slugs, honors client-reported existing skills, and defers lower-priority instructions after the first three. Role and safety instructions must be identical in both limits. No protected skills are deleted or reworded.
- Possible overlapping instructions are detected with `--audit-duplicates` (exact SHA256 source equality and profile Jaccard ≥ 0.75) and `--audit-directives` (bounded normalized text candidates). These are **review candidates**, not proven semantic duplicates: negations, exceptions, author rights and context may differ. A shared skill used by two profiles is not a reason to eliminate it.
- **Confirmed guardrail bug fixed:** explicitly requesting `profile=ui-orchestra` with a new site/screen used to suppress the `create-design` phase that the automatic router sets. Explicit profile choice is **not** visual acceptance. The adapter now preserves `create-design` in that case; a regression test checks explicit and automatic routing. It does not create a UI or auto-approve any designs.
- **Controller collision regression:** only one of `feature-delivery`, `adaptive-delivery` or `make-feature` can be selected per task; other unrelated QA skills remain selectable.
- **Negative guardrails:** fail if source instructions are truncated, client inventory is misrepresented, a selected skill is duplicated, references are silently preloaded, a task writes/installs into a project, or critical policies such as obeying `AGENTS.md`, owner approval and not inventing test results are dropped. These are **testable source-level conditions**, not proof that any particular AI client obeyed them.

## Decision

Retain the already optimized default of **3** instructions introduced under #276, with opt-in **5** and deferred reads available. No further trimming of protected/reused SKILL.md contents is justified by this dataset. The only behavioral change is restoring the **previously intended mandatory visual gate** on explicit UI profile selection. Report observed source-byte differences from exact-head CI; do not translate them into model token savings. No model, API, project execution, background installation or paid runtime was used.

## Separate, measured offline CLI/MCP latency baseline (Roadmap VI/#334)

Context source bytes above are **not performance timings**. A new independent
read-only diagnostic measures process startup or in-process handler duration:

```bash
python scripts/cli_mcp_latency.py --samples 12
python -m unittest tests.test_cli_mcp_latency -v
```

The diagnostic runs 6 local operations: two cold CLI subprocess commands
(profile list and status against a disposable temporary directory), two
in-process Project MCP handlers (catalog and skill read), and two in-process
Personal MCP handlers (info and prepare_task). Each operation has one untimed
warmup and at least 10 actual wall-clock samples. It reports median,
nearest-rank p95, min/max, Python, OS and exact local Git SHA. No project,
real AI client, model, network provider, cost or tokens are exercised.

**Measurement boundaries:** in-process MCP timings exclude stdio IPC and
client/model/tool scheduling. Cold CLI timings include Python startup.
Small-sample CI latencies are environment-specific diagnostics, **not**
production SLAs, evidence of speedup or justification for automatic
optimization. A slower case requires further reproduction and a real impact
assessment before code changes. The optional test prints one scoped sample
report into exact-head CI logs without adding a benchmark pass/fail threshold.
