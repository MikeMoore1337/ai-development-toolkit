# Release checklist

Before creating a public release:

1. Run `python scripts/check_public_package.py`.
2. Run `python scripts/validate_pack.py` and tests.
3. Optionally run official `skills-ref` validation after installing it.
4. Review staged changes: `git diff --cached --stat` and `git diff --cached`.
5. Verify no personal archive, credentials, tokens, private data or third-party copies without redistribution rights.
6. Commit on `main` only once the release content is reviewed and then push.
7. Record CI results and a meaningful changelog entry.

The initial build is prepared for publication; the project is not automatically published by these checks.
