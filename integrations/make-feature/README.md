# Make Feature 0.3.0

The actual author-provided skill, its scripts, templates, references and tests are bundled in `extensions/make-feature/skills/make-feature/`. Only the recipient-specific issued-license file is excluded.

```bash
python scripts/install.py --target /path/to/repo --profile make-feature
python scripts/install.py --target /path/to/repo --profile make-feature --apply
```

Run its own tests from its source directory using `python -m unittest discover -s tests -v`. Attribution and redistribution caveat: see `PORTABILITY_NOTES.md` and `docs/PUBLICATION_POLICY.md`.

Use Make Feature **instead of**, not alongside, the overlapping `feature-delivery` workflow to coordinate a particular task. Installation does not execute any scripts or authorize production changes.
