# Toolkit routing quick reference

| Intent | Route | Notes |
| --- | --- | --- |
| New website, landing page, major redesign, UX/UI critique | `ui-orchestra` / `ux-ui-design-orchestra` | Design first, compare real visual alternatives, obtain owner approval before implementing unapproved visuals |
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
- A GitHub link is not a local filesystem bridge.
- Share the **decision contract**, not the CLI/MCP implementation: distinguish `intent_mode` (`FULFILL_REQUEST` by default or explicit `EXPORT_PROMPT`), `status`, primary profile/skills, auxiliary candidates, excluded clauses, evidence basis, uncertainty, and client activation. Do not infer a primary profile from lexical skill hints alone.
- The ChatGPT plugin cannot execute Python routing code by merely reading this document. Use actual available project context, ignore explicit prohibited work, and state `NOT_OBSERVED` when client skill activation was not verified. Never claim `execution`, `installation_performed` or `project_files_changed` without observed actions.
- For unavailable content use `SOURCE_UNAVAILABLE` rather than pretending to have activated it.
