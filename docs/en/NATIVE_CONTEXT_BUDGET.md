# Native profile metadata budget preview (#439)

Toolkit keeps its **existing 49 profiles**, Skill Manager and lexical skill router as the sole sources of profile selection and delivery. Pinned source comparison: `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, `manifests/context-profiles/lean@1.json`, `full@1.json` and `scripts/profile.js`. ECC's lean proposes three **ECC-only** discovery skills and an 8000-token blocking metadata threshold; full previews all skill metadata and reports that limit without host activation. Neither profile can be imported literally without an external ECC registry and duplicate router, and neither has measured live model-context tokens.

Toolkit already reports profile skill counts, installed file bytes, skill Markdown bytes, references, and overlap in `scripts/profile_metrics.py`; `scripts/skill_routing_eval.py` separately provides source-only suggestions. The **new nonduplicative gap** is an explicit, bounded frontmatter-bytes budget comparison using existing profile membership **without loading extra skills or changing routing**.

Run on a trusted Toolkit checkout:

```sh
python scripts/profile_metrics.py --profile general --metadata-budget-bytes 8000
```

The output adds `metadata_budget_preview` with exact UTF-8 bytes of each selected `SKILL.md` YAML frontmatter, aggregate bytes, excess over the byte limit, and `within_budget`. The original complete selected profile is retained, **never silently pruned**. It is a local read-only source comparison, **not model tokens**: `tokens=NOT_MEASURED`, `host_context=NOT_OBSERVED`, `activation=NOT_VERIFIED`, `applied=false`. The 8000 value above is **bytes**, not the ECC 8000-token threshold; the two are not equivalent. This intentionally does not add a token estimator, hidden model call, alternate agent, auto-router, CLI runtime, or profile mutation.

Invalid budgets, missing skills, linked sources and malformed YAML delimiters fail closed. Revert by removing the optional function/CLI argument and docs/tests in a reviewed PR. Real Codex Desktop routing, token usage and output quality improvements require separately observed client evidence and are **NOT_VERIFIED**.

## Input validation and safe failure

The preview reuses Toolkit's **existing** skill validator (`scripts/validate_pack.py`, with PyYAML already pinned in `requirements-dev.txt`). It rejects malformed YAML, duplicate keys, a `name`/directory mismatch, missing mandatory metadata, non-UTF-8 sources, symlinks and Windows junctions, paths escaping the repository root, and invalid profile membership. If the validator dependency is unavailable, preview fails closed rather than reporting an unverified positive result. On a clean developer checkout, use `python -m pip install -r requirements-dev.txt`. No model provider, service or additional library is introduced.

The counted byte span includes the opening and closing YAML delimiter lines (including the terminal newline when present). The skill body, `references/`, host system instructions, model inputs and runtime context are **excluded**. This does not establish that a particular host eagerly loads every listed metadata block.

Reproduce the synthetic/offline checks and the existing profile preview:

```sh
python -m unittest tests.test_profile_budget_preview -v
python scripts/profile_metrics.py --profile general --metadata-budget-bytes 8000
```

An over-budget result is advisory only: required skills, profile order and membership remain unchanged. Disable the optional feature by omitting `--metadata-budget-bytes`. Existing routing and controller-conflict policies remain authoritative; semantic equivalence and live model token cost are not measured by this feature. Selecting a more compact profile requires an independent user decision. Unsupported clients are neither activated nor verified by the offline preview.
