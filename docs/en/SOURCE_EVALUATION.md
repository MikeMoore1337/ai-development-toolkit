# Sources and integration decisions (17 October 2026)

[Русский оригинал](../SOURCE_EVALUATION.md) | [Language policy](../LANGUAGE_POLICY.md)

Assessment based on reading GitHub README files; the specified commit SHAs were obtained from the GitHub API for the listed repositories. Other links identify a URL, **not a pinned version**. P1/P2/P3 indicate Toolkit adoption priority, not a quality ranking of the external project.

| Repository | Priority | Potential value | Toolkit decision |
| --- | --- | --- | --- |
| [artemiimillier/bulletproof](https://github.com/artemiimillier/bulletproof) | P1 | 12-step adaptive engineering | Inspire adaptive-delivery without wholesale hooks; prefer S/M/L sizing |
| [artemiimillier/claude-code-starter](https://github.com/artemiimillier/claude-code-starter) | P2 | Project onboarding template | Read for starter project only; never override the project's AGENTS.md |
| [artemiimillier/anti-ai-skill](https://github.com/artemiimillier/anti-ai-skill) | P2 | Russian-language copy style | Optional editorial-naturalness for Russian; not technical QA |
| [blader/humanizer](https://github.com/blader/humanizer) | P2 | English AI prose cleanup | Editorial-naturalness only; overlaps anti-ai and Clear Voice |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | P1 | Premium frontend style and design guidance | Use for landing pages and redesigns; preserve established design systems in product dashboards |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | P1 | UI design pattern reference | Selective lookup; no generic palette mandates |
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | P2 | Social and web platform access | Optional external tool; cookies and dependencies require separate approval |
| [WorldFlowAI/everything-claude-code](https://github.com/WorldFlowAI/everything-claude-code) | P1 | Claude Code agent, rules and hooks library | Extract selective verification/checkpoint ideas; do not copy Claude hooks into Codex |
| [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) | P2 | Prototype of a fast browser agent | Browser-workflow-evidence inspiration, not a Playwright replacement |
| [NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector) | P1 | Security scanner for agent skills | Consider as an optional external scanner; static analysis does not prove safety |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | P2 | Durable, stateful agent framework | Architecture choice only when the task needs durable workflows |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | P2 | Agents and flow orchestration framework | LangGraph alternative; not a reusable coding skill |
| [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | P1 | Codebase knowledge graphs | Potential optional CLI for large repositories; graph edges need supporting evidence |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | P1 | Simple, maintainable code changes | Use minimal-safe-change principles; do not import every-session overrides or hooks |
| [iconoir-icons/iconoir](https://github.com/iconoir-icons/iconoir) | P3 | Icon family | Choose one consistent family per project, not four at once |
| [phosphor-icons/homepage](https://github.com/phosphor-icons/homepage) | P3 | Icon family and website | For React use its corresponding package; visual styles can differ |
| [tabler/tabler-icons](https://github.com/tabler/tabler-icons) | P3 | Large icon library | Choose only when it fits the existing design system |
| [lucide-icons/lucide](https://github.com/lucide-icons/lucide) | P2 | Icon toolkit | Prefer incumbent Lucide when already used; avoid wholesale replacement |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | P1 | Animation and design critique | Use motion-quality; portions of originals were already in the source archive |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | P1 | Frontend audit and styling commands | Original archive already contained a skill and EXE; avoid duplicates and the binary |
| [abi/screenshot-to-code](https://github.com/abi/screenshot-to-code) | P2 | Screenshot-to-UI application | Screenshot-fidelity process only; the application needs API keys |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | P2 | Standalone agent runtime and skills | Third-party agent-runtime architecture reference; not a drop-in replacement for an existing system |
| [mnfst/awesome-free-llm-apis](https://github.com/mnfst/awesome-free-llm-apis) | P2 | Community listing of LLM free tiers | Verify official quotas and terms each time with provider-reality-check |
| [tashfeenahmed/freellmapi](https://github.com/tashfeenahmed/freellmapi) | P2 | LLM free-tier router | External runtime candidate; free-quota claims are unverified |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | P2 | Complete agent harness | Alternative product architecture only; 1.x rework is not a drop-in replacement |

## Pinned SHAs of reviewed HEADs

- [artemiimillier/bulletproof](https://github.com/artemiimillier/bulletproof/tree/49e9c28f317c549de2767c6bbe11848fdfc9587a): `49e9c28f317c549de2767c6bbe11848fdfc9587a`
- [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail/tree/16352ac229eb08a9598dcae48fe9f2b342567d86): `16352ac229eb08a9598dcae48fe9f2b342567d86`
- [NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector/tree/cf5cac7ba5c756a6e0ebf52dc9763f49422f889f): `cf5cac7ba5c756a6e0ebf52dc9763f49422f889f`
- [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/tree/f624f37a8c650b9cc550253104925efe4c8de246): `f624f37a8c650b9cc550253104925efe4c8de246`
- [pbakaus/impeccable](https://github.com/pbakaus/impeccable/tree/08d5b470495d242ca0470f4aeae1956c3a074f83): `08d5b470495d242ca0470f4aeae1956c3a074f83`
- [emilkowalski/skills](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202): `2d228630ba1446365f614a108cb8252f1feda202`
- [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify/tree/86c57be8204673c2a1b9849a3292a7dd3ab373d8): `86c57be8204673c2a1b9849a3292a7dd3ab373d8`
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent/tree/edab579989a1680a6cbd2bb98ad30dc165c36c8b): `edab579989a1680a6cbd2bb98ad30dc165c36c8b`

## Licensing and provenance

- Eleven new `SKILL.md` files were original adaptations of principles; external code, hooks, models, binaries and source skill text were not copied.
- `optional-original-skills` was retained unchanged from v2. Licenses of those source snapshots were not re-verified; **do not publicly redistribute without a rights audit**.
- External projects were reviewed through their README files, not a complete code audit, and were not installed. A GitHub license label does not replace checking terms before importing material.
- The `WorldFlowAI/everything-claude-code` README includes instructions referring to `affaan-m/...`; do not assume that fork is the canonical upstream without checking ownership/history.
- `NousResearch/hermes-agent` is a separate project, not a reference application. Matching names are not proof of compatibility.
- Icon libraries are software/design dependencies, not independent Agent Skills.
- New recommendations were not validated by A/B tests in the user's real projects.
