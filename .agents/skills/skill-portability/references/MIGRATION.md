# Minimal source-preserving migration

- Preserve original body, compute SHA-256 before/after, record metadata-only changes.
- Missing header: add standards-compliant name and a description summarizing existing scope (never expand capabilities).
- Unsupported metadata: move to `metadata` string fields with a vendor-prefixed key. If the old field controlled activation, keep its explicit effect in the body and label the lack of portable enforcement.
- Do not normalize binary code or execute bundled installers as a side effect.
- `SKILL.md` length is guidance; no need to split a small file solely to satisfy line count if that worsens coherence.
- Imported skill is **not enabled** merely because formatting passes.
