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

## Task-aware roles and execution

Start with one **focused profile**, not `qa-all`. A profile makes its skills available; it does not prove they were loaded or activated. When the target project does not use pytest/Playwright, omit those framework-specific skills and apply the stack-neutral methods instead. The installer copies skills, including `references/`, but **does not install or start role agents**.

Each of the [QA role contracts](roles/qa-architect.md) now declares inputs, applicable skills, an observable outcome, negative cases and an evidence handoff. Use the smallest set that can verify the request:

| Request | Suggested role flow | Focused skills |
| --- | --- | --- |
| Clarify acceptance criteria | `requirement-analyst` -> `test-designer` | `requirement-analysis`, `test-analysis-design` |
| Implement tests | `test-designer` -> `test-implementer` -> `test-reviewer` | test design, actual framework, independent test review |
| Failed CI | `ci-investigator`, add `flaky-analyst` only with nondeterminism evidence | `failure-triage`, conditional `flaky-analysis` |
| Release review | `coverage-analyst` -> `quality-gatekeeper` | `coverage-analysis`, `quality-gate-assessment` |
| Security change | `security-reviewer`, add implementer only for authorized negative tests | `security-review`, `security-testing` |

For a small defect, one actor may perform analysis, implementation and a clearly marked self-review **serially**. For genuinely separable work, a supported client can delegate roles to distinct workers, preserving file ownership and one selected feature controller. Never label serial self-review independent; without an independent worker record `INDEPENDENT_REVIEW_NOT_PERFORMED` and respect project gates requiring it. A role's Markdown is not proof of a running subagent or permission to merge/deploy.

**Evidence:** `source commit | requirement/case ID | environment | actually executed check | observable oracle | PASS/FAIL/NOT_RUN/NOT_VERIFIED | evidence | unresolved risk`. Work begins read-only; reports stay in the conversation unless the user authorizes a destination. Toolkit and its copies must not accumulate other projects' logs or test artifacts.

All 27 QA skills include local `references/`. The extra guidance is loaded only for complex tasks; the short `SKILL.md` remains sufficient for routine use. Guides are synthetic examples and do not replace live client trials. Actual discovery/activation/effectiveness stays `NOT_MEASURED` until observed.
