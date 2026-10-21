# Project integration matrix

[Русский оригинал](../INTEGRATION_MATRIX.md) | [Language policy](../LANGUAGE_POLICY.md)

| Context | Suggested skills | Do not install or enable automatically |
| --- | --- | --- |
| Any new Codex project | task-scoping, implementation, qa-strategy, minimal-safe-change | All hooks, servers or third-party dependencies |
| Mobile/web UI | design-system-consistency, screenshot-fidelity, motion-quality only when needed | New design systems, unrelated icon collections, different release rules |
| Domain backend | feature-delivery, qa-strategy, research-verification | Unverified domain-specific calculations and external-skill claims (medical, financial and engineering facts need sources) |
| Agent runtime | agent-framework-fit, codebase-knowledge-map, provider-reality-check, external-skill-review | The entire NousResearch/hermes-agent stack, unreviewed cookie stores, autopilot/deploy hooks |
| Knowledge base | codebase-knowledge-map for large imports, editorial-naturalness, qa-strategy | Unnecessary browser engines, new LLM providers or design generators |
| Research Scout | provider-reality-check, research-verification | Claims of free API quotas or quality without verifying terms and actual calls |

**Before using a tool in any external project:**

1. Confirm the required capability is actually missing from the present stack.
2. Read the licensed upstream source and record version/commit.
3. Assess permissions, secrets and external network effects.
4. Compare costs and use an isolated branch/pilot for evidence.
5. Never import third-party instructions that override release or approval procedures.

For images/icons, use **one consistent existing icon family per product**, not Lucide, Tabler, Phosphor and Iconoir simultaneously.

Any claim of skill effectiveness needs matched real tasks and comparable baselines: regressions, end-to-end task success, scope creep, operator approvals, elapsed time, tokens and manual edits. Without such tests, improvements are engineering hypotheses, **not measured outcomes**.

## Actual file layouts (structural compatibility)

Machine-readable registry and L1-L6 evidence limits: [client compatibility](../CLIENT_COMPATIBILITY.md).

| Client | Project directory | Toolkit management | Limitation |
| --- | --- | --- | --- |
| Codex | `.agents/skills/` | Skill Manager `--layout codex` | No real discovery/use test |
| Claude Code | `.claude/skills/` | Skill Manager `--layout claude` | Do not modify an existing `CLAUDE.md` |
| Custom client | Explicit `--skills-dir` | `install.py` only | No guarantee of Agent Skills behavior or managed ownership |
| Hermes | Documented `.agents/skills/` or `.hermes/skills/` | No dedicated Hermes adapter | Not executed; project trust needs separate verification |

Two managed clients in one project can have separate schema-v1 lockfiles. `migrate` copies **only managed files** whose contents match the current Toolkit version; it refuses local drift and collisions. See [client migration](../CLIENT_MIGRATION.md). File-level compatibility and successful copying **cannot prove** client/model discovery or use.

## External tool permissions

See the [tool capability, permission and execution evidence contracts](../TOOL_INTEGRATIONS.md) (Issue #69): availability, actual connection, scoped authority, pricing, egress and verified outcome are separate. No tool is installed by default.
