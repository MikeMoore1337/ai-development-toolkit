# Replica Skill - проверяемое сравнение публичных сценариев

**Toolkit #373**, upstream [Jakeschincariol/replica-skill](https://github.com/Jakeschincariol/replica-skill) pinned `77c9436fb3d18c3d58169efb8caf4fe906b0dc51`, лицензия MIT (файл LICENSE проверен). В Toolkit не включён чужой исполняемый код и нет автоматической установки навыков.

## Что переиспользуется

- `replica-recon/SKILL.md` - методика картирования экранов, состояний и пользовательских сценариев по публичным источникам.
- `replica-diff/SKILL.md` + оригинальный `replica-diff/parity.py` - расчёт полноты функций. Единственный исполняемый оригинальный компонент, только после проверки чистой pinned-копии.
- `replica-test/SKILL.md` - план QA для **собственного** YFC, без нагрузочного/активного тестирования чужих сервисов.

Нельзя копировать логотипы, тексты, ассеты или приватные API конкурентов, переходить через логин/paywall или автоматически создавать функции, UI и релизы YFC. Для визуальных изменений необходим отдельный аппрув владельца. Методы дополняют существующие Toolkit UX/UI Design Orchestra, screenshot-fidelity и QA, не заменяя их.

## Запуск без дополнительного API

В отдельном временном каталоге, **не** в рабочем проекте:

```sh
git clone https://github.com/Jakeschincariol/replica-skill.git /tmp/replica-skill-pinned
git -C /tmp/replica-skill-pinned checkout --detach 77c9436fb3d18c3d58169efb8caf4fe906b0dc51
python scripts/replica_public_parity.py --upstream /tmp/replica-skill-pinned
python scripts/replica_public_parity.py --upstream /tmp/replica-skill-pinned --matrix /path/to/reviewed_features.csv
```

CSV - UTF-8 с колонками `feature,area,priority,original,clone,notes,evidence_url,target_evidence`. `priority`: must/should/could; `original`: yes/no; `clone`: yes/partial/no/skip. Для существующей функции конкурента обязателен публичный HTTPS URL. Для `clone=yes/partial` обязательна конкретная ссылка на подтверждение в YFC (исходник, тест, скриншот). **UNKNOWN не считать NO**, а отказаться от расчёта до подтверждения. Никакой автоматической загрузки страниц/изображений, передачи приватного исходного кода или модели.

Результат выводится в stdout. Оригинальный `parity.py` запускается с `python -I`, только по подтверждённому SHA и Git blob. Не применяется к незафиксированному или изменённому upstream. Входной CSV ограничен 1 МиБ / 250 строк. Нет оплаты и автоматической записи в YFC.

## Статус доказательств

Офлайн-тесты адаптера: `python -m unittest discover -s tests -p test_replica_public_parity.py -v`. Они проверяют **контракт**, не утверждают фактическую полноту YFC. Для завершения #373 дополнительно нужен запуск оригинального upstream в изолированном окружении и хотя бы одно подтверждённое сравнение публичного сценария YFC. Без этой процедуры реальная оценка конкурента - `NOT_RUN`.
