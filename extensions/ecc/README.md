# ECC Original Skills - selective, opt-in only

This opt-in integration references **four unmodified original Agent Skills** stored under `optional-original-skills/` from [affaan-m/ECC](https://github.com/affaan-m/ECC/tree/25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b/skills), pinned at commit `25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b` (version 2.2.3). Copyright remains with Affaan Mustafa; see [the original MIT notice](../../third_party/ecc-v2.2.3/LICENSE). The exact original Git blob for each SKILL.md is checked by an offline regression, and any upstream update requires explicit re-review.

| Skill | Actual additional function | Use only for |
| --- | --- | --- |
| `windows-desktop-e2e` | pywinauto / UI Automation of native WPF, Win32, WinForms and Qt applications | Native Windows GUI, **not** HTML WebView or Playwright |
| `contract-first` | Shared OpenAPI/AsyncAPI/Proto/JSON Schema consumer-provider handshake | Independently changed frontend/backend or services; not a single local API edit |
| `api-connector-builder` | Extending existing in-repo provider/connector style | Adding new API providers; not generic HTTP tutorials |
| `code-tour` | CodeTour `.tour` JSON with verified source and line anchors | Guided onboarding or PR/RCA tours; not general codebase analysis |

Toolkit's existing `api-design`, `contract-testing`, `codebase-knowledge-map`, `qa-strategy`, `playwright-testing`, `service-architecture` and release gates remain authoritative for their original tasks. Enable only a focused skill. The original ECC skills include general descriptions and sample shell commands: their contents are **reference instructions**, not permission to run any command, install Python packages, start an agent, access credentials, or modify an external project.

## Install using Toolkit's existing exact-skill installer

From the Toolkit checkout, in an explicitly authorized *existing* destination project:

```sh
python scripts/install.py --target /path/to/project --profile ecc-windows-native
python scripts/install.py --target /path/to/project --profile ecc-windows-native --apply
```

Other profiles: `ecc-contract-first`, `ecc-api-connectors`, `ecc-code-tours`; `ecc-optin` deliberately selects all four and is **not default**. Preview before apply. The installer refuses existing destination names and never overwrites an existing skill, `AGENTS.md`, hooks, config or model settings. It only copies the exact user-approved skill folders into `.agents/skills/` of the specified project. An installed skill's activation still depends on the client, and **native Codex Desktop execution has not been observed**.

This is a deliberate *narrow original-source inclusion*: the upstream `install-plan.js --skills windows-desktop-e2e` expands into multiple shared modules, including Memory Vault and platform config. By using Toolkit's **pre-existing** per-skill installer for four MIT-licensed original skill files, none of the extra upstream code/config/hook modules is installed. No new installer or duplicated execution engine has been introduced.

**Rollback:** remove only each explicitly installed `.agents/skills/<name>/` after identifying ownership and local changes, or revert the reviewed optional-original-skills and manifest/provenance in Toolkit. Never delete another project's existing skills automatically.

**Scope and evidence:** source integrity and selective installer tests can pass in CI; actual behavior changes, quality improvement, Windows Desktop or Hermes runtime activation and zero-cost provider behavior remain NOT_VERIFIED until real client E2E. No API subscription, Codex CLI, Claude CLI, paid model, resident hook, release or background service is enabled.
