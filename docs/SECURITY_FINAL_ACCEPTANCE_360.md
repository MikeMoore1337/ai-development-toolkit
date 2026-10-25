# Independent security acceptance - Issue #360

[Русская версия](ru/SECURITY_FINAL_ACCEPTANCE_360.md) | [Exact SHA and run inventory](../fixtures/security_360_evidence.json)

This is a **source-only, cross-project acceptance record**, not a new scanner,
marketplace, customer-facing feature, runtime permission or security certificate.
Evidence was checked against GitHub's PR merge revisions and completed
exact-head/post-merge workflow checks on **2026-10-25**.

## Evidence and precedence

The structured JSON inventory provides exact repository paths, issue and PR
numbers, merge and tested-head SHAs, CI run IDs, upstream pins, scope limits,
and production impact. Refer to that inventory for source links; do not infer
that `CLOSED` proves successful E2E by itself.

| Stage | Release | Security decision | Explicit limits |
| --- | --- | --- | --- |
| I - external SkillSpector candidate check | `PASS` | Opt-in, pinned static scan **after** local integrity checks, before any human-authorized import | No semantic guarantee for Russian or English instructions, local review remains mandatory |
| II - Cisco MCP descriptor analysis | `PASS` | Optional pinned YARA/schema scan of Personal and Project first-party tool declarations | Prompts, resources, server instructions, live RPC and real side effects `NOT_RUN` |
| III - isolated SRT vs Docker comparison | `PASS` | `NO_ADOPT` extra sandbox; retain existing Docker protections | Native Windows SRT and resident production execution `NOT_RUN` |
| IVa - existing downstream SkillSpector | `PASS` | Reused upstream pin, conditional CI; developer-tooling-only `NO_DEPLOY` | Real Ubuntu/Windows synthetic scans do not prove generalized prompt-injection detection |
| Snyk Agent Scan | `NOT_RUN` | `NO_ADOPT` as a mandatory offline security analyzer | Full scan requires a remote analysis API; `inspect` is inventory, not security analysis |

Completed CI is reported as **PASS only for jobs actually executed**. CI
lanes intentionally skipped by scope routing are `NOT_APPLICABLE` (not PASS).
Unperformed production or native-host probes are `NOT_RUN`. `REVIEW_REQUIRED`
and `BLOCKED` remain possible independent scanner verdicts, not approvals.

## Reproducible independent negative regression

```bash
python -m unittest tests.test_security_360_acceptance -v
python -m unittest tests.test_skillspector_adapter tests.test_cisco_mcp_gate -v
```

The new offline test checks recorded source pins, exact-head/post-merge evidence
schema, real local first-party declaration export, no owner consent/no scan,
incomplete or corrupt analyzer responses, LLM-disabled requirements, and
synthetic bilingual `HIGH` findings. These findings are *injected mock scanner
outputs*; they test fail-closed **verdict mapping**, not detector recall.
The stage-II CI independently exercised the real pinned Cisco CLI against clean
first-party descriptions, and stage IVa independently ran the real pinned
SkillSpector on harmless RU/EN fixtures on Linux and Windows.

Neither scan may install or activate external skills/MCP connections. Static
checks are necessary, not sufficient: provenance, owner approval, source-code
inspection and actual operating-system sandbox restrictions retain authority.

## No duplicated security gate

1. The existing local source manifest/SHA/allowlist gate stays authoritative
   before optional SkillSpector. The existing Skill Manager preview and
   explicit apply boundary are unchanged.
2. Cisco scans MCP tool descriptor snapshots; it does **not** replace the
   skill source gate, permission control, or live service tests.
3. The isolated Docker comparison retains a no-adoption decision; no extra
   resident SRT dependency, OS privilege, credential, or production deploy.
4. Downstream static SkillSpector checks stay conditional on relevant skill
   changes; unrelated product CI and application deployment are excluded.

## Snyk policy: NO_ADOPT without a separate owner decision

Reviewed upstream
[README](https://github.com/snyk/agent-scan/blob/main/README.md) and
[CLI reference](https://github.com/snyk/agent-scan/blob/main/docs/cli-reference.md)
at the evidence inventory's source commit.

The documented `scan` pipeline discovers, inspects, redacts and sends component
information (including tool descriptions, configuration signatures and skill
content) to Snyk for remote analysis. It is therefore **not** a demonstrated
zero-egress offline scanner, even if upload to another product is disabled.
`inspect` provides inventory rather than an independent security verdict,
and inspection of MCP configuration may start stdio servers or contact remote
MCP endpoints. The output schema is explicitly experimental across versions.
There is no need to grant tokens, execute Snyk, upload user data or accept a
new required paid/cloud service for this plan. This is a risk/fit decision,
not a claim that Snyk offers no free plan.

## Release gate

This document, the RU copy, evidence JSON and offline tests are developer
governance/source only. Required exact-head tests across supported OSes must
pass before merging. Post-merge `main` checks and source-archive generation
must be independently verified, and Issue #360 may only be closed after that.
No client activation, no Codex CLI, no paid API and no owner data collection.
