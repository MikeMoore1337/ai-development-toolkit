# Client capabilities, evidence and routing (Issue #68)

[Русский](ru/CLIENT_CAPABILITIES.md) | [Client compatibility](CLIENT_COMPATIBILITY.md) | [Beginner workflow](BEGINNER_WORKFLOW.md)

**Reviewed 2026-10-21.** These are **offline documentation and contract tests**. Runtime sessions of Codex, Claude Code, ChatGPT and Claude.ai were **not** conducted. Keep Issue #11 zero-spend and explicit-permission gates.

## Reuse-first decision matrix

| Capability | Existing solution | Gap | Decision |
| --- | --- | --- | --- |
| Agent Skills format / metadata / links | validate_pack.py, validate_with_skills_ref.py, verify_client_compatibility.py | No new format | REUSE |
| Codex and Claude Code install, preview, collisions, rollback | skill_manager.py | None demonstrated | REUSE |
| Codex <-> Claude migration and managed ownership | skill_manager.py | None demonstrated | REUSE |
| Filesystem registry and contract | compatibility/clients.json (schema v1) | Conversational clients lack filesystem layout | REFINE (add typed companion only) |
| URL guidance / local IDE / two links / ZIP | AGENT_START, BEGINNER_WORKFLOW | Typed capabilities and evidence missing | REFINE |
| Capability routing and execution claims | No machine-readable contract | Detect unsupported actions and false results | NEW offline contract |
| ZIP metadata preflight | Client attachments / Python zipfile | Need bounded, read-only optional check | NEW offline preflight (no extraction) |
| Export/import package | Source URL, existing files, current release archives | No proven missing destination | REUSE; exporter NONE |
| Live discovery and invocation | Client features, Issue #11 | Actual logs absent | NOT_TESTED; no new runner |
| Model effectiveness | Issue #11 | No controlled comparison | NOT_MEASURED |

No second installer, workflow controller, runtime or external service is needed.

## Typed registries and evidence

The original [filesystem registry](../compatibility/clients.json) remains **schema v1**, with **codex, claude-code, hermes** intact. New [conversation companion](../compatibility/conversational_clients.json), also schema v1, holds **chatgpt, claude-ai** only. The two disjoint types share one validation entry point (`scripts/verify_client_compatibility.py`), preventing parallel claims about the same client.

- `FILESYSTEM_SKILL_CLIENT`: project skills under `.agents/skills` (Codex), `.claude/skills` (Claude Code), and documented Hermes paths. An offline managed install verifies a safe file layout, not live activation.
- `CONVERSATIONAL_REFERENCE_CLIENT`: URL/file/attachment guidance in an ordinary chat. There is **no invented project-local directory**. ChatGPT and Claude.ai also have **distinct, native hosted Skills** where eligible; enabling them requires that client's own UI and conditions, **not** Toolkit's Skill Manager.
- Client capability keys: `toolkit_access, file_read, file_write, terminal, browser, github_access, attachments, zip_handling, skill_installation, skill_discovery, tool_invocation, separate_agents, external_actions`. Values: `AVAILABLE, UNAVAILABLE, NOT_TESTED, UNKNOWN, REQUIRES_PERMISSION, NOT_APPLICABLE`. A published product feature does not establish an `AVAILABLE` capability in the current session.
- Support status vocabulary: `VERIFIED, PARTIAL, NOT_TESTED, UNSUPPORTED, UNKNOWN, BLOCKED, OWNER_REPORTED_PASS, EVIDENCE_NOT_ATTACHED`. `NOT_MEASURED` and `NOT_APPLICABLE` are distinct evidence-level states.

| Client/mode | L1 static | L2 filesystem | L3 source | L4 discovered | L5 invoked | L6 benefit |
| --- | --- | --- | --- | --- | --- | --- |
| Codex managed skills | VERIFIED | VERIFIED (offline) | VERIFIED (docs 2026-10-19) | NOT_TESTED | NOT_TESTED | NOT_MEASURED |
| Claude Code managed skills | VERIFIED | VERIFIED (offline) | VERIFIED (docs 2026-10-19) | NOT_TESTED | NOT_TESTED | NOT_MEASURED |
| Hermes | VERIFIED | PARTIAL (offline) | VERIFIED (pinned docs 2026-10-19) | NOT_TESTED | NOT_TESTED | NOT_MEASURED |
| ChatGPT ordinary chat, URL guidance | NOT_APPLICABLE | NOT_APPLICABLE | VERIFIED (docs 2026-10-21) | NOT_TESTED | NOT_TESTED | NOT_MEASURED |
| Claude.ai ordinary chat, URL guidance | NOT_APPLICABLE | NOT_APPLICABLE | VERIFIED (docs 2026-10-21) | NOT_TESTED | NOT_TESTED | NOT_MEASURED |

L1-L3 **never imply** L4-L6. The live discovery/invocation and usefulness of separately installed *hosted* Skills also remain NOT_TESTED / NOT_MEASURED for Toolkit. A user-reported ZIP+URL success on 2026-10-20 for ChatGPT, Claude, DeepSeek and Qwen is **OWNER_REPORTED_PASS** only: detailed client versions, invocation logs and baseline results were not attached (**EVIDENCE_NOT_ATTACHED**). DeepSeek/Qwen require no new mandatory adapter.

## Verified vendor documentation (2026-10-21)

- [Agent Skills specification](https://agentskills.io/specification) - SKILL.md required frontmatter; optional references/scripts, does not mandate discovery in every client.
- [Codex skills](https://learn.chatgpt.com/docs/build-skills) - project-local .agents/skills and user/admin paths; actual activation depends on runtime, configuration and client version.
- [Claude Code skills](https://code.claude.com/docs/en/skills) - project-local .claude/skills and personal/enterprise paths; optional client-specific metadata and discovery controls; CLAUDE.md is not rewritten. Some newer Claude Code sessions can sync hosted Claude.ai Skills under independent client controls.
- [ChatGPT Skills](https://help.openai.com/en/articles/20001066-skills-in-chatgpt) and [file uploads](https://help.openai.com/en/articles/8555545-uploading-files-and-audio-to-chatgpt) - hosted Skills depend on eligible plans/workspaces, while ordinary chat attachments have separate limits and access rules. A pasted Toolkit URL does not install a Skill.
- [Claude.ai Skills](https://support.claude.com/en/articles/12512180-use-skills-in-claude), [custom Skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills), [projects](https://support.claude.com/en/articles/9517075-what-are-projects) - native uploaded Skills available in eligible configured accounts, including Free per current help center, with code execution enabled. Distinct from Claude Code managed project layouts. Actual tools, web access and file operations vary per session.

Provider documentation is not an actual client session or a plan-entitlement check. Client versions **UNKNOWN**, approval needed for write/external actions. Documentation may change; verify again before enabling optional hosted workflows.

## Four capability-based routes

1. **NATIVE_FILESYSTEM_SKILL** - filesystem client, actual skill already installed, file read and discovery confirmed. Copy alone cannot select this route.
2. **TOOLKIT_REFERENCE** - external URL contents actually read; `GUIDANCE_ONLY`, no installation or invocation claim.
3. **ATTACHMENT_GUIDANCE** - the attached Toolkit material was actually readable; the user's project archive is a **separate** input.
4. **MANUAL_FALLBACK** - no usable files/tools; prepare a design, code excerpt, or next step in chat. This is a valid outcome, not failure.

Use `client_capabilities.select_route` only with measured in-session capabilities, not inferred marketing descriptions. It deliberately returns `skill_invoked: false` and `tests_executed: false`. `validate_execution_claim` refuses unsupported native discovery, missing source/attachment, false file writes/tests/model calls, unproven subagents and paid API calls. These are **synthetic contract oracles**, not a guarantee that a live model always follows them.

## Supported user scenarios

- **Local IDE, no GitHub URL for user's project**: open existing workspace, inspect project instructions, read relevant Toolkit material without installing; implement in the actual target only when permitted; verify and report. Example: "Use https://github.com/MikeMoore1337/ai-development-toolkit to repair the save button in my currently open project."
- **Two links**: Toolkit URL is a read-only guidance source; the second URL is the work target. Public read permission does not imply commit/PR permission.
- **ZIP + Toolkit URL**: identify the *user* project ZIP, distinguish it from the Toolkit source, check file availability and path safety; read applicable guidance without automatically installing Skills. If the ZIP is unavailable, state `ATTACHMENT_UNAVAILABLE`; if writing or tests are unavailable, return draft/code suggestions with `TESTS_NOT_RUN`. Never store the ZIP or outputs in any Toolkit checkout.
- **Ordinary chat with no files**: `GUIDANCE_PREPARED / IMPLEMENTATION_NOT_PERFORMED / FILES_NOT_ACCESSIBLE / TESTS_NOT_RUN`. Ask for the minimum blocking file only when necessary.
- **Optional installation**: only via existing Skill Manager Discover -> Preview -> Consent -> Apply -> Status. Existing user skills/AGENTS.md/CLAUDE.md, rollback, checksums and drift remain protected; installation does not prove runtime invocation.

For `ZIP` fixtures only, `client_capabilities.inspect_zip` inspects metadata with Python `zipfile` **without extraction**. It rejects absent/malformed/empty archives, traversal/absolute/case-colliding entries, symlinks, secrets, nested archives, encrypted/unsupported entries and oversized expansion. Defaults: at most 1000 regular entries, 64 MiB total decompressed, per-entry compression ratio at most 80. This is bounded *preflight*, **not malware detection or safe extraction**. Do not insist on it when the client's attachment reader already provides bounded safe access.

## Canonical source / package contract

**No export adapter was built.** A Toolkit URL, relevant files or the existing release archive provides a simpler path; there is no demonstrated client gap requiring a generated package. Any future opt-in export must remain read-only and contain: package ID, exact Toolkit revision, selected skills, canonical source paths, SHA256 per file, included references/scripts, license and provenance, destination client type, packaging mode, validation result, and limitations. Preserve original skill content; no client fork or metadata rewrite is allowed without explicit deterministic documentation and digest comparison. Reject missing or extra files, link escapes, name collisions, invalid references, missing licenses and changed source SHA. A SHA256 value is **not** a signature or a security assessment.

Live protocol (separately gated by Issue #11): record client/version, configuration, install layout, exact Skill SHA, discovery observation, invocation evidence, task + acceptance criteria, baseline and candidate, cost, permissions and limitations. Mark each of discovery, invocation, task completion and useful benefit **independently**. No trial, live agent delegation, paid API, account setup or deployment was performed for #68.

Issue #69 receives the *capability vocabulary* for optional integrations, credential/permission boundaries and scoped actions; it does **not** inherit any verified external-tool permissions.

## Tool-level permissions (Issue #69)

The companion [optional integrations and authority contracts](TOOL_INTEGRATIONS.md) add a synthetic per-operation permission/egress/cost/evidence model without changing the existing client registries or L1-L6 levels. A client capability does not grant tool authorization or prove an executed action.
