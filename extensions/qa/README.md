# QA Engineering Pack

27 portable Agent Skills and 11 reference roles adapted from the **user-authored QA archive** from a work project. This extension preserves test-design, test-oracle, failure-triage, CI, security and release-evidence coverage, without importing the original project's hard-coded environment or its private policy files.

The source archive had no embedded redistribution license. The contributor has stated they authored the material. Before external publication, verify the relevant employment/IP obligations and that no confidential project-specific content is reproduced. The files in this pack are newly written, portable adaptations.

## Skills and roles

- `extensions/qa/skills`: 27 opt-in QA skills; original-to-portable mapping in [SOURCE_MAPPING.md](SOURCE_MAPPING.md).
- `extensions/qa/roles`: 11 reference role descriptions. They are not executable subagents.
- `extensions/qa/recipes`: compact flows for new features, failed CI and release review.
- QA profiles from the root manifest: `qa-core`, `qa-python`, `qa-fullstack`, `qa-ci`, `qa-release`, `qa-security`, `qa-contract`, `qa-ui`, `qa-management`, `qa-collaboration`.

```bash
python scripts/install.py --target /path/to/project --profile qa-core
python scripts/install.py --target /path/to/project --profile qa-core --apply
```

Activate framework-dependent skills only in compatible projects. Do not require Jira, Test IT, Graphify, Playwright, pytest or a particular branching strategy globally. Existing `AGENTS.md` and repository approval policies remain authoritative.
