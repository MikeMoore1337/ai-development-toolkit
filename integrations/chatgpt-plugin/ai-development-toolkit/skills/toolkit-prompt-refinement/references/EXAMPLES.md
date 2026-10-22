# Примеры

**RU, бытовой черновик:** `надо меню дешево быстро на неделю без рыбы`

**Готовый промпт:** `Составь меню на семь дней без рыбы из доступных продуктов с минимальным временем готовки. Дай завтраки, обеды, ужины, общий список покупок и варианты приготовления заранее. Не выдумывай цены или ограничения здоровья; если бюджет не указан, явно отметь допущение.`

**RU, инженерный черновик:** `Codex экран прыгает когда печатаю вес исправь`

**Готовый промпт:** `В доступном текущем проекте воспроизведи смещение экрана во время ввода веса. Проверь состояние компонента, фокус, экранную клавиатуру, размеры и прокрутку, не предполагая причину заранее. Исправь минимально, без изменения бизнес-логики и существующего дизайна. Добавь доступные регрессионные тесты и сообщи точные изменения, реально запущенные проверки и непроверенные сценарии. Не выполняй merge/deploy без разрешения.`

**EN:** `make a good prompt SEO my website` -> `Audit the supplied website for technical and content SEO. Show URL-specific observations and evidence, priorities, proposed fixes and validation. If no web or Search Console access is available, mark claims NOT_VERIFIED and provide a focused inspection plan. Never invent rankings or traffic.`

**Negative:** `проверь SEO моего сайта` executes an SEO audit, not prompt drafting; `пиши письмо` edits prose; `используй навыки и сделай сайт` executes design-first workflow.
