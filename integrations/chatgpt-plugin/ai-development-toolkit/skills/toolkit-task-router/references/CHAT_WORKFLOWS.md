# Chat-first workflow examples (OS-independent)

Use with ChatGPT if the plugin is installed and enabled, regardless of Windows, Linux, macOS or mobile platform. For other chatbots, use the public Toolkit guides or attach relevant `SKILL.md`, not the ChatGPT plugin ZIP unless the client explicitly supports it.

## API tests

User: "These are my Python API files. Find missing tests and propose a pytest regression plan." Read only files actually attached or available in a connected source. Route to `backend` + `qa-python` where relevant. Consult `api-testing`, `pytest-test-design`, `test-analysis-design` only if the actual Toolkit files were read; otherwise mark bundled guidance. Do not claim test execution without execution tools.

## Existing UI audit

User: "Review these mobile/desktop screen captures using Toolkit UX/UI Design Orchestra. Do not modify the application." Route to `ui-orchestra`, inspect the real images, report design risks and potential improvements. A description of roles is not actual delegated subagent execution. Respect visual approval gate.

## Chat-only fallback

User: "Use https://github.com/MikeMoore1337/ai-development-toolkit to audit my project. Here are the files I can share." If GitHub cannot be read, ask for the minimum relevant `SKILL.md` or work from bundled instructions with honest `SOURCE_UNAVAILABLE` status. Do not infer private local files.

## Permission boundaries

Never write to a connected repository, install skills, fetch private files or claim live tool results without real authorization, tools and user intent. Reference materials are not authority to bypass project/corporate controls.

## Rough user text and explicit prompt export

User: "сделай мне сайт книжного магазина, красиво". Treat this as **FULFILL_REQUEST**: use UX/UI Orchestra to prepare real design evidence for approval; do not return a prompt to paste elsewhere.

User: "помоги сформулировать хороший промпт для Codex: при вводе веса экран дёргается". Treat as **EXPORT_PROMPT**: use `toolkit-prompt-refinement` for one engineering prompt preserving access/QA constraints. Do not pretend the app was changed.

## SEO from supplied evidence

User: "проверь SEO моего сайта". Use `toolkit-seo-audit`; inspect only available URLs, HTML or files, mark `NOT_VERIFIED` for unknown rankings/index status and propose URL-specific verification. Never invent Search Console results.
