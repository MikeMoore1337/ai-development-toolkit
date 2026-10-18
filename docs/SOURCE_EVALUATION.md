# Источники и решения по интеграции (17.10.2026)

Проверено чтением README через GitHub; приведённые SHA взяты из GitHub API для указанных репозиториев.
Остальные ссылки фиксируют URL, но **не конкретную версию**. Оценка P1/P2/P3 - приоритет для набора, не оценка качества всего проекта.

| Репозиторий | Приоритет | Что даёт | Решение |
|---|---|---|---|
| [artemiimillier/bulletproof](https://github.com/artemiimillier/bulletproof) | P1 | 12-step adaptive engineering | Inspire adaptive-delivery, no wholesale hooks; prefer S/M/L sizing |
| [artemiimillier/claude-code-starter](https://github.com/artemiimillier/claude-code-starter) | P2 | project onboarding template | Read for starter project only; avoid overriding project AGENTS.md |
| [artemiimillier/anti-ai-skill](https://github.com/artemiimillier/anti-ai-skill) | P2 | Russian copy style | Editorial-naturalness for Russian, optional and not technical QA |
| [blader/humanizer](https://github.com/blader/humanizer) | P2 | English AI prose cleanup | Editorial-naturalness only; overlaps anti-ai/clear-voice |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | P1 | premium frontend style/design taste | Use for landing/redesign where appropriate; product dashboards use incumbent design |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | P1 | UI design pattern reference | Selective lookup, no generic palette mandates |
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | P2 | social/web platform reach | External tool if needed; cookie and dependency setup need separate approval |
| [WorldFlowAI/everything-claude-code](https://github.com/WorldFlowAI/everything-claude-code) | P1 | Claude Code agents/rules/hooks library | Extract selective verification/checkpoint patterns; do not copy Claude hooks into Codex |
| [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) | P2 | prototype fast browser agent | Browser-workflow-evidence design inspiration, NOT Playwright replacement |
| [NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector) | P1 | security scanner for agent skills | Adopt as optional external scanner; static analysis cannot prove safe |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | P2 | durable stateful agent framework | Architecture option only if task requires durable workflows |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | P2 | agents and flow orchestration framework | Alternative to LangGraph; not a reusable coding skill |
| [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | P1 | codebase knowledge graphs | Potential optional CLI for large repos; graph edges require evidence |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | P1 | simple maintainable code decisions | Minimal-safe-change; do not import every-session overrides or hooks |
| [iconoir-icons/iconoir](https://github.com/iconoir-icons/iconoir) | P3 | icon library | Choose one consistent project family, not four simultaneously |
| [phosphor-icons/homepage](https://github.com/phosphor-icons/homepage) | P3 | icon family / website | For React package use phosphor-icons/react; styles may differ |
| [tabler/tabler-icons](https://github.com/tabler/tabler-icons) | P3 | large icon library | Icon choice only when relevant to design system |
| [lucide-icons/lucide](https://github.com/lucide-icons/lucide) | P2 | icon toolkit | Prefer incumbent Lucide when already used, avoid wholesale swap |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | P1 | animation and design critique | Motion-quality; originals already partly present in source archive |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | P1 | frontend audits and styling command set | Original archive already contained skill and EXE: avoid duplicates and binary |
| [abi/screenshot-to-code](https://github.com/abi/screenshot-to-code) | P2 | screenshot-to-UI application | Screenshot-fidelity workflow only; app requires API keys |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | P2 | standalone agent runtime and skills | Architectural reference for Hermes, NOT same project or drop-in update |
| [mnfst/awesome-free-llm-apis](https://github.com/mnfst/awesome-free-llm-apis) | P2 | community listing of provider free tiers | Provider-reality-check: verify official quota/terms each time |
| [tashfeenahmed/freellmapi](https://github.com/tashfeenahmed/freellmapi) | P2 | LLM free-tier router | External runtime candidate; free quota claims not verified |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | P2 | full agent harness | Alternative product architecture only; rework of 1.x not drop-in |

## Закреплённые SHA проверенных HEAD

- [artemiimillier/bulletproof](https://github.com/artemiimillier/bulletproof/tree/49e9c28f317c549de2767c6bbe11848fdfc9587a): `49e9c28f317c549de2767c6bbe11848fdfc9587a`
- [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail/tree/16352ac229eb08a9598dcae48fe9f2b342567d86): `16352ac229eb08a9598dcae48fe9f2b342567d86`
- [NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector/tree/cf5cac7ba5c756a6e0ebf52dc9763f49422f889f): `cf5cac7ba5c756a6e0ebf52dc9763f49422f889f`
- [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill/tree/f624f37a8c650b9cc550253104925efe4c8de246): `f624f37a8c650b9cc550253104925efe4c8de246`
- [pbakaus/impeccable](https://github.com/pbakaus/impeccable/tree/08d5b470495d242ca0470f4aeae1956c3a074f83): `08d5b470495d242ca0470f4aeae1956c3a074f83`
- [emilkowalski/skills](https://github.com/emilkowalski/skills/tree/2d228630ba1446365f614a108cb8252f1feda202): `2d228630ba1446365f614a108cb8252f1feda202`
- [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify/tree/86c57be8204673c2a1b9849a3292a7dd3ab373d8): `86c57be8204673c2a1b9849a3292a7dd3ab373d8`
- [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent/tree/edab579989a1680a6cbd2bb98ad30dc165c36c8b): `edab579989a1680a6cbd2bb98ad30dc165c36c8b`

## Лицензии и происхождение

- Новые 11 SKILL.md - оригинальная переработка принципов; код, хуки, модели, бинарники и тексты сторонних навыков не копировались.
- `optional-original-skills` сохранён из v2 без изменений. Лицензии этих исходных снимков не перепроверены; не распространяйте публично без аудита прав.
- Внешние проекты проверены по README, не проходили полный аудит кода и не устанавливались. Наличие лицензии на GitHub не заменяет чтение условий при дальнейшем импорте.
- Для `WorldFlowAI/everything-claude-code` README содержит инструкции с `affaan-m/...`: не следует считать указанный форк канонической upstream-версией без проверки владельца и истории.
- `NousResearch/hermes-agent` - отдельный проект, не `reference application`. Совпадение названий не даёт совместимости.
- Наборы иконок являются программными/дизайн-зависимостями, а не самостоятельными agent skills.
- Новые рекомендации не подтверждены A/B-проверкой на реальных репозиториях пользователя.
