# Native profile metadata budget preview (#439)

Toolkit keeps its **existing 49 profiles**, Skill Manager and lexical skill router as the sole sources of profile selection and delivery. Pinned source comparison: `affaan-m/ECC@25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b`, `manifests/context-profiles/lean@1.json`, `full@1.json` and `scripts/profile.js`. ECC's lean proposes three **ECC-only** discovery skills and an 8000-token blocking metadata threshold; full previews all skill metadata and reports that limit without host activation. Neither profile can be imported literally without an external ECC registry and duplicate router, and neither has measured live model-context tokens.

Toolkit already reports profile skill counts, installed file bytes, skill Markdown bytes, references, and overlap in `scripts/profile_metrics.py`; `scripts/skill_routing_eval.py` separately provides source-only suggestions. The **new nonduplicative gap** is an explicit, bounded frontmatter-bytes budget comparison using existing profile membership **without loading extra skills or changing routing**.

Run on a trusted Toolkit checkout:

```sh
python scripts/profile_metrics.py --profile general --metadata-budget-bytes 8000
```

The output adds `metadata_budget_preview` with exact UTF-8 bytes of each selected `SKILL.md` YAML frontmatter, aggregate bytes, excess over the byte limit, and `within_budget`. The original complete selected profile is retained, **never silently pruned**. It is a local read-only source comparison, **not model tokens**: `tokens=NOT_MEASURED`, `host_context=NOT_OBSERVED`, `activation=NOT_VERIFIED`, `applied=false`. The 8000 value above is **bytes**, not the ECC 8000-token threshold; the two are not equivalent. This intentionally does not add a token estimator, hidden model call, alternate agent, auto-router, CLI runtime, or profile mutation.

Invalid budgets, missing skills, linked sources and malformed YAML delimiters fail closed. Revert by removing the optional function/CLI argument and docs/tests in a reviewed PR. Real Codex Desktop routing, token usage and output quality improvements require separately observed client evidence and are **NOT_VERIFIED**.
