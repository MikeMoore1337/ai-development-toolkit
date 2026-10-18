# Clear Voice

A portable, Russian-first editorial Agent Skill for clear writing, fact-preserving edits, text review, UI copy, knowledge-base entries and research summaries. English editing is supported.

## Profiles

- `profiles/general.md` - generic writing and documentation
- `profiles/product-ui.md` - interface strings and user-facing descriptions
- `profiles/knowledge-base.md` - factual notes and structured knowledge
- `profiles/research-digest.md` - cautious summaries of research and news

The skill also has on-demand `references/`, a compact `adapters/editorial-worker/` prompt, and 61 synthetic checks in `evals/`.

## Use

Install the complete `clear-voice/` directory using the Toolkit `editorial` profile and activate `$clear-voice` for a writing task. Do not let stylistic editing alter numbers, protected fields, formats, source claims or permissions. The adapter is provided as source text only; it does not modify or deploy any runtime.

## Validate

```bash
python .agents/skills/clear-voice/evals/validate_package.py
```

See `SOURCES.md`, `LICENSE` and `THIRD_PARTY_NOTICES.md` for attribution.
