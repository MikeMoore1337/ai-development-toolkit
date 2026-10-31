# Toolkit routing quick reference

Other request examples: “Use Toolkit guidance to review the repository I connected.” and “Сделай хороший промпт для Codex из моих заметок.”

| Intent | Route | Notes |
| --- | --- | --- |
| New website, landing page, major redesign, UX/UI critique | `ui-orchestra` / `ux-ui-design-orchestra` | Use original tool-native design exploration without imposed style bans or concept quotas; preserve preferred visual baseline and obtain owner approval before implementing |
| Known narrow CSS bug in already-approved UI | `ui-fix` | Do not force full redesign |
| REST API, Python services, backend | `backend` | Add QA complement when requested |
| Frontend implementation | `frontend` | Only after visual approval when substantial design decisions remain |
| Cross-stack delivery | `fullstack` | Choose one delivery coordinator, avoid conflicting controllers |
| Python tests or regression analysis | `qa-python` / `qa-core` | Respect existing runners, do not assume pytest is installed |
| Browser tests | `qa-ui` | Do not claim Playwright available without checking |
| Security and infrastructure | focused security/DevOps profile | Least privilege; distinguish analysis from authorized changes |
| Messy input asking for an actual website/bug fix | task-specific skill / `FULFILL_REQUEST` | Normalize internally and execute; don't return a new prompt for re-submission |
| Explicitly "write/improve a prompt" | `toolkit-prompt-refinement` / `EXPORT_PROMPT` | One copy-ready prompt without task execution |
| Technical/on-page SEO and indexability audit | `toolkit-seo-audit` | Evidence, `NOT_VERIFIED` for unavailable indexing/rank data |

- Project-native skills and rules take precedence; never silently overwrite unmanaged skills.
- The Toolkit MCP in Codex is **independent** of the ChatGPT skills-only plugin.
- Reassess skills at meaningful stage changes; use only supported read tools, bounded batches and a client-kept record of complete instructions still in context. Follow the user's exclusions and project gates on every pass. A client without the stage tool can perform targeted reads; neither path proves native activation.
- A GitHub link is not a local filesystem bridge.
- Share the **decision contract**, not the CLI/MCP implementation: distinguish `intent_mode` (`FULFILL_REQUEST` by default or explicit `EXPORT_PROMPT`), `status`, primary profile/skills, auxiliary candidates, excluded clauses, evidence basis, uncertainty, and client activation. Do not infer a primary profile from lexical skill hints alone.
- The ChatGPT plugin cannot execute Python routing code by merely reading this document. Use actual available project context, ignore explicit prohibited work, and state `NOT_OBSERVED` when client skill activation was not verified. Never claim `execution`, `installation_performed` or `project_files_changed` without observed actions.
- For unavailable content use `SOURCE_UNAVAILABLE` rather than pretending to have activated it.
- If asked for a diagnostic, follow the read-only contract in `docs/CLIENT_CAPABILITIES.md`: name the adapter, separately distinguish adapter version and Toolkit source version, exact verified source SHA or `NOT_VERIFIED`, specific skill instructions actually read, and confirmed bundled fallback or `NOT_VERIFIED`. Treat L4 client discovery, L5 native invocation and L6 benefit as independent unknowns unless directly evidenced. The ChatGPT skills-only plugin does not run MCP/CLI code or prove that native skills were activated. No project path, private data or implicit network activity should be emitted as a prerequisite.

## Tool-native creative freedom (#489)

The personal ChatGPT adapter routes to the existing `ux-ui-design-orchestra` but does not override the original designer tools with Toolkit aesthetic restrictions. Do not require three drafts/risks or forbid cards, hero, gradients, colours, fonts, imagery, glass or familiar e-commerce/SaaS layouts. Preserve the user's preferred visual baseline, compare new variants honestly and distinguish technical checks from artistic judgment. Actual upstream tool activation remains separately verifiable (#449). No user media or reports are stored inside Toolkit.
