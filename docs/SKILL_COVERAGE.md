# Local skill coverage advisory (Issue #199)

[Русская версия](ru/SKILL_COVERAGE.md) | [MCP](../scripts/toolkit_mcp.py) | [Routing regressions](SKILL_ROUTING_EVALS.md) | [External skill review](EXTERNAL_METHODS_ADOPTION.md)

The project-scoped `scripts/toolkit_mcp.py` now offers the read-only MCP tool `toolkit_assess_skill_coverage` (one required string argument: `query`, 1-500 characters). The existing `toolkit_route_task` also returns a `skill_coverage` object. This is an **offline, source-only diagnostic**, not a semantic completeness verdict or proof of Codex/Claude/ChatGPT skill activation.

| `coverage` | Meaning | Safe next action |
|---|---|---|
| `FOUND_LOCAL` | Query exactly equals the slug of a readable, declared Toolkit skill | Read that skill, validate suitability and permissions |
| `AMBIGUOUS` | Some skills have lexical matches; no coverage claim is justified | Inspect candidate descriptions and project requirements |
| `MISSING` | No skills have lexical matches | Record the gap; consider an explicitly authorized external search |

Returned candidate names/scores are **lexical hints only** (maximum five). `MISSING` does **not** prove semantic absence; Russian synonyms and cross-language prompts may be misclassified. A default `general` profile is a routing fallback, not a claim that the task's specialist capability exists.

For every result: `external_skill_search=NOT_RUN`, `external_skill_install=NOT_AUTHORIZED`, `client_activation=NOT_OBSERVED`, `requires_review=true`. Task text is untrusted data and is never executed. This change does not install plugins, add providers, invoke paid APIs, call Agensi, or download external files.

## Verification

```bash
python -m unittest tests.test_toolkit_mcp -v
python scripts/validate_pack.py
python -m unittest discover -s tests -v
```

The assertions cover exact local name, ambiguous lexical query, missing match, oversized/empty input, prompt-injection text treated as data and absence of project writes. They are source-level regressions, **not** real AI-client trials. Confirmed live MCP/tool invocation from Codex remains a separate acceptance step.

## Follow-ups and boundaries

- [#199](https://github.com/MikeMoore1337/ai-development-toolkit/issues/199): improve discovery/relevance, clarify external source allowlists and real-client acceptance.
- [#200](https://github.com/MikeMoore1337/ai-development-toolkit/issues/200): provenance, license, package/security and explicit import approval. No automatic remote import before this gate.
- [#190](https://github.com/MikeMoore1337/ai-development-toolkit/issues/190): separately shipped personal MCP / ChatGPT plugin update and exact-client compatibility. The repository also includes this advisory in the personal MCP source at `integrations/personal-mcp/adt-personal/mcp/adt_mcp.py` (v0.1.9 source). **Do not assume** an already installed personal MCP or ChatGPT plugin exposes it; publishing, installation and live client invocation are separate evidence gates.
- [#11](https://github.com/MikeMoore1337/ai-development-toolkit/issues/11): paired effectiveness trials, never inferred from lexical ranks.

No production runtime or user-project data is modified by this advisory.
