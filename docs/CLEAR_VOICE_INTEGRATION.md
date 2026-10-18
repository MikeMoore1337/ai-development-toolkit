# Clear Voice integration

Full Clear Voice 1.1.0 portable is bundled under `.agents/skills/clear-voice/`. It contains generic profiles (general, product-ui, knowledge-base, research-digest), editorial references, synthetic evaluation cases, licensing notes and a generic editorial worker adapter. No privately named project profiles or user project URLs are included.

```bash
python scripts/install.py --target /path/to/repo --profile editorial
python scripts/install.py --target /path/to/repo --profile editorial --apply
python .agents/skills/clear-voice/evals/validate_package.py
```

Style instructions never override factual correctness, schemas, access permissions or deployment gates.
