# Поиск внешних Skill по GitHub с явным разрешением — Issue #199

[English](../GITHUB_SKILL_DISCOVERY.md) · [Локальная проверка кандидата](EXTERNAL_SKILL_CANDIDATE_REVIEW.md) · [Security Gate](EXTERNAL_SKILL_GATE.md)

`scripts/github_skill_discovery.py` — необязательный поиск **метаданных**, а не доверенный каталог навыков. Без флага `--discover` сеть не используется. С ним разрешены только анонимные HTTPS-запросы с ограничением времени к фиксированному `api.github.com` для явно переданных оператором репозиториев с полным 40-символьным commit SHA.

```bash
# Обычный локальный режим, без сети
python scripts/github_skill_discovery.py --query "qa-strategy"

# Явно разрешённый запрос. Замените вымышленные данные после проверки источника
python scripts/github_skill_discovery.py --query "backend" --discover \
  --allow-repo "https://github.com/approved-owner/public-repo@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
```

Пример SHA **не подтверждён**; это заглушка, не адрес реального проверенного источника. Скрипт подтверждает commit SHA через публичный API GitHub, получает tree SHA, просматривает только ограниченное дерево путей и ищет `SKILL.md` по лексическому совпадению, включая скрытый каталог `.agents/skills/` и короткие термины `QA`/`UI`. Не более трёх репозиториев и 20 результатов. Отсутствие совпадений не означает отсутствия подходящего навыка. Ошибки сети/лимитов GitHub API, перенаправления, частичные деревья, превышение размера и неподтверждённые SHA дают отказ.

Все найденные пути — **недоверенные подсказки**, не подтверждение полезности, лицензии и автора. Поля результата: `license=NOT_VERIFIED`, `content=NOT_DOWNLOADED`, `remote_security_gate=NOT_RUN`, `installation=NOT_AUTHORIZED`. Скрипт не скачивает `SKILL.md`, не исполняет чужие файлы, не читает секреты, не меняет конфигурацию Codex и не запускает Hermes-агентов. Платные API не используются; для анонимного GitHub API действуют лимиты.

**Следующий этап:** вручную проверить источник и лицензию, получить изолированную копию на конкретном SHA, независимо сравнить хеши, выполнить [offline Security Gate](EXTERNAL_SKILL_CANDIDATE_REVIEW.md). Даже `ALLOW_FOR_REVIEW` не разрешает установку.

```bash
python -m unittest tests.test_github_skill_discovery -v
python scripts/validate_pack.py
python scripts/verify_checksums.py
```

CI проверяет поддельные HTTP-ответы, а не реальный GitHub или установленный персональный MCP. Живой сетевой поиск и интеграция в работающем Codex остаются отдельными этапами приёмки.
