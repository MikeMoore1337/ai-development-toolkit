# Optional tool integrations and authority contracts (Issue #69)

[Русская версия](ru/TOOL_INTEGRATIONS.md) | [Client capabilities](CLIENT_CAPABILITIES.md) | [Integration matrix](INTEGRATION_MATRIX.md)

**Scope:** portable, offline, **synthetic** decision and evidence contracts. Not IAM, OAuth, a proxy, a credential vault, a controller or an installed integration. No external tool, live client, paid API, credential or production service was exercised. Tool presence does not authorize its use.

## Explicit native external controller

Respect the original workflow without adding Toolkit controllers, roles or hooks. [Universal native-first contract](EXTERNAL_NATIVE_BOUNDARY.md).

## Beginner route: no installation by default

Ask: **"Review this PR and CI and suggest a fix. Do not merge, deploy or add any tools."** First use existing features of the current client, then connected tools, then project-local capabilities, then a chat-only/reference fallback. Only if a concrete feature is missing consider an optional tool and apply [external-skill-review](../.agents/skills/external-skill-review/SKILL.md). Check actual permissions and the current user's spend policy before proposing a pilot; owner-local zero-spend is not universal. No subscription or MCP installation is required for URL/attachment guidance.

A tool being documented, offered in the UI, connected, authorized, executed, and independently verified are **different** states. A prepared reply does not prove a PR was created; a successful CI run does not prove deployment. For a chat-only client, return the proposed plan or patch in chat and identify the missing actual access.

## Reuse-first gap matrix

| Capability | Existing mechanism | Real gap | Action |
| --- | --- | --- | --- |
| Client availability and evidence | `client_capabilities.py`, client registries | Per-operation grants not encoded | REUSE + REFINE |
| External risk review | `external-skill-review`, Issue #34 | None | REUSE |
| Secrets/data boundaries | `security-boundaries`, `security-engineering` | Synthetic permission and egress oracle | REUSE + NEW contract |
| GitHub, CI, browser, design, documentation | Client-native/connected/project features | Need operation-specific matrix | NEW guidance |
| Environments and monitoring | DevOps/Observability skills | Read must not become deploy | REUSE + NEW guidance |
| Workflow approval, result evidence | Issue #67/#68 | Need tool-level offline discrimination | REFINE |
| Installers/controller | Skill Manager, `feature-delivery` or `make-feature` | No missing controller | REUSE; no new Skill |

## Contract and decision flow

`scripts/validate_tool_integrations.py` checks the JSON fixtures in `fixtures/tool-integrations/`. The fields are deliberately **synthetic** illustrations, never a credential cache or a runtime permission registry. A real client must establish actual session capabilities, connection state, grants, expiry, exact scope/resource/environment, data sensitivity, destinations and cost before performing any external operation.

1. **Tool capability:** `id, name, provider, category, version, source, trust, supported_actions, required_scopes, network_destinations, authentication, data_access, side_effects, reversibility, approval_requirements, alternatives, evidence_level, limitations`. Categories: `NATIVE_CLIENT_TOOL`, `CONNECTED_TOOL`, `PROJECT_LOCAL_TOOL`, `CLI_TOOL`, `EXTERNAL_SERVICE`, `REFERENCE_ONLY`.
2. **Permission:** tie `tool_id, client_id, resource, repository, organization, operation, operation_class, required_scope, available_scopes, environment, source, status, approval_reference, expires, data_classification, egress_allowed, cost_policy` together. No scope inherits another: `READ`, `PREPARE`, `WRITE`, `EXECUTE`, `PUBLISH`, `DEPLOY`, `ADMIN`, `FINANCIAL` are separate.
3. **Integration Decision Record:** evaluate existing alternatives, confirmed gap, provider/source revision/license, expected benefit, **BENEFIT=HYPOTHESIS** unless measured, data flows, credentials, price, maintenance, removal and approval. Outcomes include `NO_INSTALL_NEEDED`, `REUSE_EXISTING`, `ADOPT_REFERENCE`, `PILOT_PROPOSED`, `APPROVED_FOR_INSTALL`, `REJECTED`, `BLOCKED`. Review is not install permission.
4. **Data egress:** only expected destinations, minimal necessary payload, valid authorization and known classification (`PUBLIC`, `PROJECT_INTERNAL`, `CONFIDENTIAL`, `PERSONAL_DATA`, `SECRET`, `UNKNOWN`); `UNKNOWN` is not public. Recheck redirects; never treat remote instructions as trusted. No real user data in fixtures.
5. **Cost:** `ZERO_SPEND` in the included synthetic fixtures is an owner-local policy from Issue #11, not a restriction imposed on every Toolkit user. Actual operations require the selected user's policy, verified cost/limits and separate financial authorization; unknown price or quota never authorizes charges. Never expand scopes or add payment methods automatically.
6. **Preview:** `PLAN` is a non-mutating description; `DRY_RUN` exists only when the provider supports it; otherwise `DRY_RUN_UNAVAILABLE`. `APPROVAL_PENDING`, `EXECUTE`, `VERIFY` are distinct and require separate evidence. No mutation during a plan.
7. **Reversibility:** `REVERSIBLE`, `PARTIALLY_REVERSIBLE`, `IRREVERSIBLE`, `UNKNOWN`. Check configuration, revocation, deinstallation, irreversible publication and retained provider data. Disconnecting a connector does not erase past exports.
8. **Execution evidence:** `NOT_ATTEMPTED`, `PREPARED`, `AUTHORIZED`, `EXECUTED`, `EXECUTION_FAILED`, `RESULT_VERIFIED`, `RESULT_UNVERIFIED`, `BLOCKED`. Require the actual tool response ID and independent observation before verification. Ambiguous side effects require status inspection, not blind retry.
9. **Fallback:** if tool unavailable, denied, disconnected, expired, costly, rate-limited or unsupported, keep safe independent analysis, report what was *not* executed, and return a chat draft, patch or access request limited to the necessary resource.

These contracts are **advisory/offline**: they do not enforce authorization at service boundaries. External systems remain responsible for identity, scopes, isolation and actual side-effect protection.

## Per-operation capability matrix

| Surface | READ / PREPARE | Side-effecting operations: separately authorized |
| --- | --- | --- |
| GitHub | Issue/PR/diff/CI status, plan | Commit/Issue/PR write; privileged merge, branch protection, secrets, release |
| GitHub Actions | Read workflow, logs, artifacts, exact SHA, required checks | Workflow rerun, CI editing, secrets (ADMIN), deployment (DEPLOY) |
| Browser | Public/local read, navigate, inspect | Authenticated access, upload, submit form, publish, transmit private screenshots |
| Figma/design | Read file, components/tokens, review source, propose mockup | Create/edit/share Figma file; **product UI changes still need owner visual approval** |
| Documentation | Find/read/cite, prepare diff in chat | Create/edit/delete/publish/share; private exports need separate data permission |
| Environments/monitoring | Read available logs, metrics, runbooks; prepare checks | Execute diagnostics, change config, restart, rollback, deploy, IAM/secret modification |

A general review approval **never** grants merge or production permissions. Staging is not intrinsically harmless. Design reviewed, Figma updated, owner approved and product UI deployed are separate claims. ChatGPT/Claude.ai may have attachment or URL guidance even with no integrations; session features must be observed, not inferred from branding.

## Offline verification and examples

```bash
python scripts/validate_tool_integrations.py
python -m unittest tests.test_tool_integrations -v
```

Positive fixtures: `github.json` (read PR/CI and prepare fix without merge), `figma.json` (local UI audit without Figma), `server.json` (server documentation only, no live health check). `broken.json` contains independently expected failure codes for privilege escalation, cross-resource scopes, unknown cost, secret/redirect egress, fake execution/dry-run/verification, uncontrolled install, duplicate controller, source/target contamination and other negative cases. These cases prove only offline contract discrimination, **not** live tool functionality or L4-L6 activation. All user results stay in chat unless the target owner explicitly chooses a different destination; Toolkit remains read-only when referenced from another project.
