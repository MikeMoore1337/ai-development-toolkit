# Project integration matrix

[Русский оригинал](../INTEGRATION_MATRIX.md) | [Client compatibility](../CLIENT_COMPATIBILITY.md) | [Language policy](../LANGUAGE_POLICY.md)

| Context | Skills | Do not enable automatically |
| --- | --- | --- |
| Any new project using Codex | task-scoping, implementation, qa-strategy, minimal-safe-change | All hooks, servers and third-party dependencies |
| Mobile/web UI | design-system-consistency, screenshot-fidelity, motion-quality, as needed | New design systems, extra icon libraries or modified release rules |
| Domain-specific backend | feature-delivery, qa-strategy, research-verification | Unverified domain formulas, policies or claims imported from external skills (e.g. medical, financial or engineering claims without sources) |
| Agent runtime | agent-framework-fit, codebase-knowledge-map, provider-reality-check, external-skill-review | Whole NousResearch/hermes-agent framework, unverified cookie stores, autopilot/deploy hooks |
| Knowledge base | codebase-knowledge-map for large imports, editorial-naturalness, qa-strategy | Unnecessary browser engines, LLM providers and design generators |
| Research Scout | provider-reality-check, research-verification | Assuming an API is free or good without checking real terms and calls |

Criteria before enabling **any external project**:

1. Confirm that the capability is genuinely missing from the current stack.
2. Read the licensed original and record its version or commit.
3. Review privileges, secrets and outbound calls.
4. Compare costs and test in an isolated branch or pilot.
5. Never automatically copy release or approval instructions from third parties.

For images and icons, choose **one** established library per product rather than mixing Lucide, Tabler, Phosphor and Iconoir by default.

Claims about skill improvements need equivalent-task evaluation: regressions, whole-task success, scope creep, operator approvals, elapsed time, tokens and manual edits. Without such a comparison, any benefit is still an **engineering hypothesis**.

## Actual layouts (structural compatibility)

The machine-readable register and the L1–L6 limits of evidence are described in [client compatibility](../CLIENT_COMPATIBILITY.md).

| Client | Project directory | Toolkit management | Important limitation |
| --- | --- | --- | --- |
| Codex | `.agents/skills/` | Skill Manager `--layout codex` | No live discovery/use test |
| Claude Code | `.claude/skills/` | Skill Manager `--layout claude` | Do not modify existing `CLAUDE.md` |
| Custom | Explicit `--skills-dir` | `install.py` only | No guaranteed Agent Skills compatibility or ownership tracking |
| Hermes | Documented `.agents/skills/` and `.hermes/skills/` | No dedicated Hermes adapter | Not run; client trust rules require independent verification |

Two managed clients in one repository can use independent schema-v1 lockfiles. `migrate` transfers only manager-owned files **identical to the current Toolkit sources**; local drift or conflicting paths block transfer. See [client migration](../CLIENT_MIGRATION.md). Structural compatibility and successful copying **do not establish that a model discovered or used the skill**.
