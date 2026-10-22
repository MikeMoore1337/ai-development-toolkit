# Change-impact regression advisor (offline)

Use this deterministic, read-only helper when planning regression coverage from changed paths. It extends the existing `change-impact-analysis` workflow; it does **not** run tests, inspect file contents, trace callers, or change the project.

Create a JSON array of relative paths, for example:

```json
["src/auth/session.py", "db/migrations/001.sql", "frontend/screens/workout.tsx"]
```

Then run `python scripts/change_impact_advisor.py --paths-json changed.json`.

The report contains a risk level, affected surfaces, recommended checks with path evidence, and explicit `NOT_RUN`, `NOT_OBSERVED` markers. Auth changes require negative access-control checks; database schema changes require forward/rollback and integrity checks. Unknown paths are flagged for manual inspection rather than declared safe. A path-only report is **not** a replacement for reading the diff, identifying downstream consumers, approving test scope, executing checks, or verifying the actual CI result.

No external API, runtime agent, dependency installation or paid service is involved. Related issue: [#191](https://github.com/MikeMoore1337/ai-development-toolkit/issues/191).
