# Built-in Toolkit capabilities derived from ECC (#435, #446)

**Toolkit is a standalone product.** These thirteen skills ship **inside Toolkit**: consumers do not install or launch ECC, `ecc-universal`, ECC CLI, MCP, plugin, hooks or any sidecar. The twelve original `SKILL.md` files and the complete Windows UIA reference are preserved byte-for-byte from [ECC 2.2.3 `25278e7...`](https://github.com/affaan-m/ECC/tree/25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b), with Affaan Mustafa's copyright and the original MIT license under `third_party/ecc-v2.2.3/LICENSE`. No extra paid API, model call, daemon, hook or CLI is needed.

| Native Toolkit skill | Unique value beyond existing Toolkit | Apply when |
| --- | --- | --- |
| `contract-first` | Consumer/provider coordination around an authoritative OpenAPI, AsyncAPI, Proto or JSON Schema | Parallel frontend/backend, contract ownership; complements `api-design` and `contract-testing` |
| `api-connector-builder` | Repo-convention-aware API provider/connector implementation and registry checks | Adding a provider to an existing integration architecture |
| `code-tour` | CodeTour `.tour` with verified source and line anchors | Onboarding, PR navigation, architecture and incident walkthroughs |
| `windows-desktop-e2e` | Native Windows UI Automation via pywinauto with a concise safe entrypoint and exact original reference | Explicitly approved Windows native GUI testing, not browser or Electron HTML automation |
| `module-regression` | Downstream acceptance-command ledger with verified dependency edges and observed exit codes | Multimodule changes where A can regress B; not for small isolated projects |
| `error-handling` | Original typed error, retry, boundary and user-error examples for TypeScript, Python and Go | Explicit API/service error-handling implementation and review tasks |
| `mcp-dependency-review` | Static review of mutable npm/Python/Docker package and image selectors in MCP configuration; no server execution | Before approving repo-scoped MCP config changes |
| `agent-introspection-debugging` | Four-stage diagnosis of agent tool failures without hidden runtime | After repeated agent loops/failures |
| `content-hash-cache-pattern` | SHA-256 content-based cache with safe invalidation guidelines | Repeated expensive file transformations |
| `loop-design-check` | Check machine-decidable goals, damping and runaway feedback loops | Design/review autonomous loops with real stop criteria |
| `make-interfaces-feel-better` | Opt-in UI finish checklist; does not control UX/UI Orchestra | Explicit request for typography/spacing/motion polish |
| `article-writing` | Evidence-aware editorial drafting without publishing | SEO-related article and guide preparation |
| `click-path-audit` | Identify sequential store updates that undo UI intent | Debug buttons that do nothing or state races |

## Use through Toolkit (no external ECC installation)

From an installed Toolkit checkout, use the **existing Toolkit installer** for one focused profile:

```sh
python scripts/install.py --target /path/to/project --profile native-code-tours
python scripts/install.py --target /path/to/project --profile native-code-tours --apply
```

Available profiles: `native-contract-first`, `native-api-connectors`, `native-code-tours`, `native-windows-desktop-e2e`, `native-module-regression`, `native-error-handling`, `native-mcp-dependency-review`, `native-agent-introspection-debugging`, `native-content-hash-cache-pattern`, `native-loop-design-check`, `native-make-interfaces-feel-better`, `native-article-writing`, `native-click-path-audit`. The first command previews; `--apply` explicitly installs the one named built-in skill and its bundled MIT license in the authorized existing destination project. No AGENTS, user config, models, MCP or hooks are overwritten. An ECC plugin or CLI is not needed.

The original skill text contains examples; it is **not execution permission** to use shell commands, pip, credentials, external APIs or network. Local Codex Desktop/Hermes activation is NOT_VERIFIED until independently observed. CI verifies exact source identity, no-clobber installation and provenance, not actual model effectiveness.

**Error handling (#435):** `native-error-handling` adds an unchanged original ECC `SKILL.md` and MIT license with no ECC runtime or dependency. The source supplies coding examples rather than an executable engine; user/project contracts and authorization still govern actual changes. Source/installer tests do not prove client activation (NOT_VERIFIED).

**MCP dependency review (#435):** `native-mcp-dependency-review` installs the exact original MIT instructions and license only. It does not implement or execute a scanner, resolve dependencies, contact registries or start MCP servers. Source and isolated no-clobber installation CI are not live classification or AI-client activation evidence (NOT_VERIFIED).

**Module regression (#435):** Original pinned source, example template and MIT license ship with `native-module-regression`. This opt-in instruction is not a scanner or permission to run ledger commands; offline source/install checks do not prove actual client activation (NOT_VERIFIED).

**Windows UIA (#450):** the original 889-line source is unchanged under `optional-original-skills/windows-desktop-e2e/references/ORIGINAL_SKILL.md`; the short native `SKILL.md` links to it and requires explicit owner consent before any Windows UIA execution. Structural tests on Windows do not prove actual GUI testing, which remains NOT_VERIFIED until a separately approved live run.

**Security boundary:** upstream ECC's `install-plan.js --skills windows-desktop-e2e` resolves to four modules and potentially unrelated config. Toolkit already has a focused installer that copies only the authorized built-in skill; there is no new installer or ECC module/control-plane dependency. Remove only explicitly installed files for rollback and never delete unrelated user-owned skills. The remaining 588 source components are evaluated case-by-case under [#435](https://github.com/MikeMoore1337/ai-development-toolkit/issues/435); no blanket import or duplicate controller.

---

# Toolkit Native Host Config Security (#432)

This is an **opt-in static host configuration audit**, added to the existing Toolkit `external_skill_gate.py` rather than a second controller. Toolkit does not install or run ECC, AgentShield, a plugin, model, external scanner, MCP server, hook or daemon.

## Usage

Point at an **explicitly selected synthetic or approved project directory**, not the home directory:

```sh
python scripts/external_skill_gate.py --host-config-root /path/to/approved/project
python scripts/external_skill_gate.py --host-config-root /path/to/approved/project --format sarif
python -m unittest tests.test_external_skill_gate -v
```

Exit codes: `0 PASS` means *only the configured subset* is free of these static findings, `1 REVIEW_REQUIRED` means uncertainty or medium findings, `2 BLOCKED` means high-risk or invalid input. Output is JSON or SARIF 2.1.0 to stdout; the JSON `evidence.files` includes relative allowlisted paths, byte counts and SHA-256 of inspected bytes, not contents. No evidence files are written without an operator choosing a redirect. Never treat a clean scan as a runtime authorization.

## Supported exact file paths and checks

| File | Static checks |
| --- | --- |
| `.codex/config.toml` | `danger-full-access`, approval `never`, declared MCP server env/roots |
| `.codex/hooks.json` | Command strings nested under hooks: network egress, pipe to shell, untrusted interpolation, destructive command |
| `.claude/settings.json` and `settings.local.json` | Hooks as above, explicit `Bash(*)`/`Write(*)`/`Edit(*)` and shell-interpreter allow permissions |
| `.mcp.json` | Inline credential-looking env values, broad filesystem roots, npx/bunx auto-install signal |

Malformed JSON/TOML, duplicate JSON keys, invalid structures, oversized data, linked paths and unreadable files produce high-severity findings. A missing allowlisted file is *out of scope*, not clean evidence for that subsystem; no supported file produces `REVIEW_REQUIRED`.

**Security boundaries:** No user secrets are echoed. Files are inspected up to 128 KiB each and 512 KiB total. Input is never executed or sent to a model or network. `HOST_CONFIG...` findings are advisory policy decisions; no Codex Desktop or Claude hook interception is registered. An `approval_policy` setting in a file does **not** prove the actual client honored it. Static flags are a conservative subset and can have false positives or miss threats; code execution and permissions still require host control.

## Differentiation, provenance and rollback

This complements (not replaces) `external_skill_gate.py`'s existing third-party Skill checks, Cisco MCP declaration scans (#359) and SkillSpector (#200). Original research comparison: [AgentShield source `b0891303bdcd6037376a94263d45cfd2ff3dfb98`](https://github.com/affaan-m/agentshield/tree/b0891303bdcd6037376a94263d45cfd2ff3dfb98), license MIT. The implementation is Toolkit-authored Python; no original TypeScript, package dependency, binary, or model inference is copied. Upstream source review is not live AgentShield execution.

Remove/rollback only this opt-in code revision via normal Git history; no files or permissions are changed by the audit. The original Skill candidate scan mode and its output remain supported. Native Windows Codex Desktop security enforcement, upstream parity and complete Host AgentShield-grade coverage remain **NOT_VERIFIED**. Issue #432 stays open pending remaining security controls and accepted real-client evidence.

## Additional native checks and coverage matrix (#432, synthetic diagnostic)

The existing opt-in host scan also recognizes PowerShell
`Invoke-RestMethod`/`irm` commands with explicit HTTP(S) destinations,
and advisory signals for known collector URLs or sensitive filesystem
paths in MCP server argv. The latter two use **MEDIUM / REVIEW_REQUIRED**:
legitimate troubleshooting configurations may use them. No command,
path, network endpoint or hook is executed or contacted. Only predefined
relative source paths and SHA-256 checksums appear in JSON/SARIF; the
scanner never echoes the argument or its value.

| Surface | Native/optional source coverage | Remaining limitation |
| --- | --- | --- |
| Agent instructions | `audit_agent_instructions.py` structural references/duplicates; external Skill text heuristics | Role/semantic override not comprehensively detected |
| MCP descriptions | `cisco_mcp_gate.py --native` tool and nested JSON-schema heuristic; optional pinned Cisco YARA/schema | Obfuscation, remote server behavior, prompts/resources not inspected |
| Hooks | Explicit Codex/Claude hook-command strings under approved root | No hook execution, dynamic command flow or host interception |
| Permissions | Explicit sandbox/approval and blanket shell/write/edit/interpreter settings | Other client versions, effective permissions and runtime enforcement unknown |
| Secrets | Inline MCP environment credential signals, redacted reports | No full secret discovery, user stores or runtime exfiltration check |
| External skills | Existing candidate Skill inventory, checksums and text gate; optional SkillSpector | No proof third-party source is safe or authenticated |
| Integrity | Bounded allowlisted files, malformed JSON/TOML, duplicate JSON keys, unsafe links, junction roots and SHA-256 | Races after scan, unsupported paths and junction platforms require separate assurance |

`host_report_sarif` emits SARIF 2.1.0 rule IDs and severity with
relative paths only. A JSON evidence receipt records inspected-file
SHA-256 and size; it does **not** certify producer provenance or prevent
a post-scan change. The 38-case offline diagnostic and aggregate baseline
are documented in [MCP security scan](../MCP_SECURITY_SCAN.md).
Upstream reference: [AgentShield MIT source at pinned revision](https://github.com/affaan-m/agentshield/tree/b0891303bdcd6037376a94263d45cfd2ff3dfb98).
No original source or runtime is required or installed. Roll back by
reverting only the Toolkit change in Git; opt-in scanning never mutates
host settings. A source comparison is not validated rule parity:
`UPSTREAM_COMPARISON=NOT_RUN`, `CLIENT_RUNTIME=NOT_VERIFIED`,
`REPRESENTATIVE_ACCURACY=NOT_MEASURED`; Issue #432 must remain open.
