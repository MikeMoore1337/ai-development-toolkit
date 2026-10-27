# Источники и решения по интеграции (17.10.2026)

[English translation](en/SOURCE_EVALUATION.md) | [Политика языков](ru/LANGUAGE_POLICY.md)

Проверено чтением README через GitHub; приведённые SHA взяты из GitHub API для указанных репозиториев.
Остальные ссылки фиксируют URL, но **не конкретную версию**. Оценка P1/P2/P3 - приоритет для набора, не оценка качества всего проекта.

| Репозиторий | Приоритет | Что даёт | Решение |
|---|---|---|---|
| [artemiimillier/bulletproof](https://github.com/artemiimillier/bulletproof) | P1 | 12-шаговая адаптивная разработка | Идеи для adaptive-delivery без копирования всех хуков; предпочтительна оценка S/M/L |
| [artemiimillier/claude-code-starter](https://github.com/artemiimillier/claude-code-starter) | P2 | Шаблон подготовки нового проекта | Изучить только для шаблона проекта; не перезаписывать проектный AGENTS.md |
| [artemiimillier/anti-ai-skill](https://github.com/artemiimillier/anti-ai-skill) | P2 | Стиль естественного текста на русском | Только необязательный editorial-naturalness; не заменяет технический QA |
| [blader/humanizer](https://github.com/blader/humanizer) | P2 | Редактура англоязычного AI-текста | Только editorial-naturalness; пересекается с anti-ai и Clear Voice |
| [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) | P1 | Выразительный стиль frontend-дизайна | Использовать для лендингов и редизайна; в продуктовых интерфейсах сохранять действующую дизайн-систему |
| [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) | P1 | Справочник паттернов UI-дизайна | Выборочное использование; не навязывать общую цветовую палитру |
| [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) | P2 | Доступ к социальным и веб-платформам | Внешний инструмент только по необходимости; cookies и зависимости требуют отдельного разрешения |
| [WorldFlowAI/everything-claude-code](https://github.com/WorldFlowAI/everything-claude-code) | P1 | Библиотека агентов, правил и хуков Claude Code | Заимствовать только идеи проверки и контрольных точек; не копировать Claude-хуки в Codex |
| [browser-use/jev-ultrafast](https://github.com/browser-use/jev-ultrafast) | P2 | Прототип быстрого браузерного агента | Вдохновение для browser-workflow-evidence, но не замена Playwright |
| [NVIDIA/SkillSpector](https://github.com/NVIDIA/SkillSpector) | P1 | Сканер безопасности навыков агентов | Рассматривать как необязательный внешний сканер; статический анализ не доказывает безопасность |
| [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph) | P2 | Фреймворк для агентов с долговечным состоянием | Архитектурный вариант только при необходимости устойчивых workflow |
| [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) | P2 | Фреймворк оркестрации агентов и процессов | Альтернатива LangGraph, но не готовый навык программирования |
| [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) | P1 | Граф знаний о кодовой базе | Потенциальная необязательная CLI для больших репозиториев; рёбра графа требуют доказательств |
| [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail) | P1 | Оригинальные навыки минималистичной разработки и проверки | Шесть исходных SKILL.md v5.3.2 хранятся как исходный снимок **только для ручного подключения** в `third_party/ponytail-v5.3.2/skills/`; без хуков и автоматической установки. [Инструкция](PONYTAIL_UPSTREAM.md) |
| [iconoir-icons/iconoir](https://github.com/iconoir-icons/iconoir) | P3 | Набор иконок | Выбирать одну согласованную библиотеку, не четыре одновременно |
| [phosphor-icons/homepage](https://github.com/phosphor-icons/homepage) | P3 | Семейство иконок и сайт | Для React использовать соответствующий пакет; стили могут отличаться |
| [tabler/tabler-icons](https://github.com/tabler/tabler-icons) | P3 | Большая библиотека иконок | Использовать только при соответствии существующей дизайн-системе |
| [lucide-icons/lucide](https://github.com/lucide-icons/lucide) | P2 | Набор инструментов иконок | Предпочитать уже используемый Lucide; не заменять библиотеку целиком без причины |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | P1 | Критика анимации и дизайна | Использовать motion-quality; исходные материалы частично есть в архиве |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) | P1 | Команды для аудита и оформления frontend | В исходном архиве уже были навык и EXE; избегать дубликатов и бинарного файла |
| [abi/screenshot-to-code](https://github.com/abi/screenshot-to-code) | P2 | Приложение для переноса скриншота в UI | Только идеи screenshot-fidelity; самому приложению нужны ключи API |
| [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) | P2 | Отдельный агентный runtime и навыки | Архитектурный пример для Hermes, не тот же продукт и не готовое обновление |
| [mnfst/awesome-free-llm-apis](https://github.com/mnfst/awesome-free-llm-apis) | P2 | Общественный список бесплатных тарифов LLM API | В provider-reality-check каждый раз проверять официальные лимиты и условия |
| [tashfeenahmed/freellmapi](https://github.com/tashfeenahmed/freellmapi) | P2 | Маршрутизатор бесплатных тарифов LLM | Внешний кандидат для runtime; заявления о бесплатных квотах не проверены |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | P2 | Полноценная среда работы агентов | Только альтернативная архитектура продукта; переработка 1.x не является готовой заменой |

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

- Исторические 11 SKILL.md являются оригинальной переработкой принципов. Дополнительно в #422 по явному запросу владельца добавлены **шесть неизменённых** исходных Ponytail v5.3.2 SKILL.md с MIT-лицензией, без hooks/бинарников и без автоматической установки; их Git blob SHA проверяются тестом.
- `optional-original-skills` сохранён из v2 без изменений. Лицензии этих исходных снимков не перепроверены; не распространяйте публично без аудита прав.
- Внешние проекты проверены по README, не проходили полный аудит кода и не устанавливались. Наличие лицензии на GitHub не заменяет чтение условий при дальнейшем импорте.
- Для `WorldFlowAI/everything-claude-code` README содержит инструкции с `affaan-m/...`: не следует считать указанный форк канонической upstream-версией без проверки владельца и истории.
- `NousResearch/hermes-agent` - отдельный проект, не `reference application`. Совпадение названий не даёт совместимости.
- Наборы иконок являются программными/дизайн-зависимостями, а не самостоятельными agent skills.
- Новые рекомендации не подтверждены A/B-проверкой на реальных репозиториях пользователя.
