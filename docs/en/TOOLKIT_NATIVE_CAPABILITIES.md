# Built-in Toolkit capabilities derived from ECC (#435, #446)

**Toolkit is a standalone product.** These four skills ship **inside Toolkit**: consumers do not install or launch ECC, `ecc-universal`, ECC CLI, MCP, plugin, hooks or any sidecar. The first three original `SKILL.md` files and the complete Windows UIA reference are preserved byte-for-byte from [ECC 2.2.3 `25278e7...`](https://github.com/affaan-m/ECC/tree/25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b), with Affaan Mustafa's copyright and the original MIT license under `third_party/ecc-v2.2.3/LICENSE`. No extra paid API, model call, daemon, hook or CLI is needed.

| Native Toolkit skill | Unique value beyond existing Toolkit | Apply when |
| --- | --- | --- |
| `contract-first` | Consumer/provider coordination around an authoritative OpenAPI, AsyncAPI, Proto or JSON Schema | Parallel frontend/backend, contract ownership; complements `api-design` and `contract-testing` |
| `api-connector-builder` | Repo-convention-aware API provider/connector implementation and registry checks | Adding a provider to an existing integration architecture |
| `code-tour` | CodeTour `.tour` with verified source and line anchors | Onboarding, PR navigation, architecture and incident walkthroughs |
| `windows-desktop-e2e` | Native Windows UI Automation via pywinauto with a concise safe entrypoint and exact original reference | Explicitly approved Windows native GUI testing, not browser or Electron HTML automation |

## Use through Toolkit (no external ECC installation)

From an installed Toolkit checkout, use the **existing Toolkit installer** for one focused profile:

```sh
python scripts/install.py --target /path/to/project --profile native-code-tours
python scripts/install.py --target /path/to/project --profile native-code-tours --apply
```

Available profiles: `native-contract-first`, `native-api-connectors`, `native-code-tours`, `native-windows-desktop-e2e`. The first command previews; `--apply` explicitly installs the one named built-in skill and its bundled MIT license in the authorized existing destination project. No AGENTS, user config, models, MCP or hooks are overwritten. An ECC plugin or CLI is not needed.

The original skill text contains examples; it is **not execution permission** to use shell commands, pip, credentials, external APIs or network. Local Codex Desktop/Hermes activation is NOT_VERIFIED until independently observed. CI verifies exact source identity, no-clobber installation and provenance, not actual model effectiveness.

**Windows UIA (#450):** the original 889-line source is unchanged under `optional-original-skills/windows-desktop-e2e/references/ORIGINAL_SKILL.md`; the short native `SKILL.md` links to it and requires explicit owner consent before any Windows UIA execution. Structural tests on Windows do not prove actual GUI testing, which remains NOT_VERIFIED until a separately approved live run.

**Security boundary:** upstream ECC's `install-plan.js --skills windows-desktop-e2e` resolves to four modules and potentially unrelated config. Toolkit already has a focused installer that copies only the authorized built-in skill; there is no new installer or ECC module/control-plane dependency. Remove only explicitly installed files for rollback and never delete unrelated user-owned skills. The remaining 597 source components are evaluated case-by-case under [#435](https://github.com/MikeMoore1337/ai-development-toolkit/issues/435); no blanket import or duplicate controller.
