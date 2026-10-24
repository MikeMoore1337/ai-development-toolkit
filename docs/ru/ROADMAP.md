# План развития

[English source](../ROADMAP.md)

## Текущее состояние (24 октября 2026 года)

Последний **опубликованный релиз исходников** - [v5.5.6](https://github.com/MikeMoore1337/ai-development-toolkit/releases/tag/v5.5.6), `MANIFEST.json.version = 5.5.6` в неизменяемом теге на коммите `490cec222c4c2551a7bbe6f20bb0e9a316af13e1`. [GitHub Actions](https://github.com/MikeMoore1337/ai-development-toolkit/actions/runs/40109117878) подтвердил SHA256 и техническую проверку происхождения архива, однако документация при публикации содержала устаревшие ссылки, исправляемые отдельно. Реальная эффективность агентов и независимая проверка прав не доказаны. Изменения `main` после тега автоматически не публикуются. См. [инструкцию по релизу](RELEASE_PROCESS.md).

В этой ревизии каталог содержит **82 навыка, 45 профилей и 16 ролей**. Актуальные числа определяются по [MANIFEST.json](../../MANIFEST.json). CI проверяет исходники, упаковку, происхождение компонентов, архив и автономные контракты, но **не доказывает** обнаружение навыков реальным агентом или повышение качества решения задач.

Эта страница - план развития, **не автоматически обновляемый список Issues**. Действующий статус и доказательства приёмки смотрите по ссылкам GitHub.

## Уже выполнено

- **Фундамент:** закреплённая структурная проверка `skills-ref` [#24](https://github.com/MikeMoore1337/ai-development-toolkit/issues/24); реестр происхождения и релизный gate [#28](https://github.com/MikeMoore1337/ai-development-toolkit/issues/28); целостность документации [#26](https://github.com/MikeMoore1337/ai-development-toolkit/issues/26); безопасная установка и откат [#12](https://github.com/MikeMoore1337/ai-development-toolkit/issues/12); поддерживаемые файловые схемы и клиентские контракты [#30](https://github.com/MikeMoore1337/ai-development-toolkit/issues/30), [#32](https://github.com/MikeMoore1337/ai-development-toolkit/issues/32); инженерные навыки и профили [#40](https://github.com/MikeMoore1337/ai-development-toolkit/issues/40), [#36](https://github.com/MikeMoore1337/ai-development-toolkit/issues/36); автономные метрики исходников [#38](https://github.com/MikeMoore1337/ai-development-toolkit/issues/38).
- **Этап I, задачи закрыты:** [#271](https://github.com/MikeMoore1337/ai-development-toolkit/issues/271) версия опубликованного релиза, [#272](https://github.com/MikeMoore1337/ai-development-toolkit/issues/272) контракты маршрутизации клиентов, [#273](https://github.com/MikeMoore1337/ai-development-toolkit/issues/273) дополнительные отрицательные и диагностические проверки.
- **Этап II, задачи закрыты:** [#274](https://github.com/MikeMoore1337/ai-development-toolkit/issues/274) диагностика источников и версий, [#275](https://github.com/MikeMoore1337/ai-development-toolkit/issues/275) безопасное обновление и откат исходников, [#276](https://github.com/MikeMoore1337/ai-development-toolkit/issues/276) измерение объёма контекста, [#277](https://github.com/MikeMoore1337/ai-development-toolkit/issues/277) упрощённый старт от задачи.
- **Этап III, задачи закрыты:** [#278](https://github.com/MikeMoore1337/ai-development-toolkit/issues/278) доказательства QA change-impact, [#279](https://github.com/MikeMoore1337/ai-development-toolkit/issues/279) автономные решения по оркестрации, [#280](https://github.com/MikeMoore1337/ai-development-toolkit/issues/280) закреплённые зависимости и бесплатные воспроизводимые примеры.
- **Релиз закрыт:** [#293](https://github.com/MikeMoore1337/ai-development-toolkit/issues/293) - опубликован v5.5.5, проверены ZIP исходников, provenance и послерелизная документация. Редакторская базовая приёмка двух языков завершена в [#259](https://github.com/MikeMoore1337/ai-development-toolkit/issues/259).

Статус «выполнено» относится **только к явно подтверждённому объёму** каждой задачи. Это не означает, что все клиенты и навыки проверены в реальной работе.

## Roadmap IV (завершён в согласованном объёме)

Все восемь задач ниже закрыты в ограниченном принятом объёме; ссылки содержат подтверждения реализации. Проверки исходников не доказывают независимую пользу реальных агентов:

1. **P0:** [#294](https://github.com/MikeMoore1337/ai-development-toolkit/issues/294) актуальность документации и плана RU/EN.
2. **P1:** [#295](https://github.com/MikeMoore1337/ai-development-toolkit/issues/295) понятный выбор ChatGPT / Personal MCP / Project MCP / Skill Manager; [#296](https://github.com/MikeMoore1337/ai-development-toolkit/issues/296) новые RU/EN стресс-тесты маршрутизации.
3. **P1:** [#297](https://github.com/MikeMoore1337/ai-development-toolkit/issues/297) реальные наблюдаемые проверки клиентов L4/L5; [#298](https://github.com/MikeMoore1337/ai-development-toolkit/issues/298) сравнение полезности навыков с исходным решением, только бесплатно и при наличии разрешений.
4. **P2:** [#299](https://github.com/MikeMoore1337/ai-development-toolkit/issues/299) удаление доказанного дублирования контекста; [#300](https://github.com/MikeMoore1337/ai-development-toolkit/issues/300) переносимые синтетические QA/UX/UI-сценарии.
5. **P3:** [#301](https://github.com/MikeMoore1337/ai-development-toolkit/issues/301) простое сопровождение каталога и происхождения навыков.

## Ограничения и отложенные направления

- [#11](https://github.com/MikeMoore1337/ai-development-toolkit/issues/11) - **CLOSED / NOT_PLANNED** из-за запрета владельца на платные испытания (**ZERO-SPEND**). CLI-средство испытаний описано, но реальные платные вызовы моделей запрещены в реализации, даже с флагами подтверждения. Нельзя считать испытания проведёнными или незаметно возобновить их за деньги.
- [#141](https://github.com/MikeMoore1337/ai-development-toolkit/issues/141) - **CLOSED / COMPLETED в ограниченном объёме бесплатного исследовательского пилота оркестрации**. Это не подтверждает независимо уровни L4-L6, эффективность всех навыков, универсальную экономию времени или статистически убедительное A/B-сравнение. См. [матрицу совместимости](CLIENT_COMPATIBILITY.md) и [порядок испытаний](REAL_AGENT_PILOT.md).
- Полноценные обнаружение и применение навыков реальными клиентами и измерение пользы остаются `NOT_TESTED` / `NOT_MEASURED`, пока не появились отдельные доказательства. Лексическая маршрутизация не является семантической моделью, а успешные заранее подготовленные проверки - не измерение независимой точности.
- Приватные и сторонние навыки публикуются только при доказанных правах и независимости от конкретных проектов, согласно [правилам публикации](PUBLICATION_POLICY.md). Не следует создавать второй runtime или подключать платный API ради выполнения плана.
