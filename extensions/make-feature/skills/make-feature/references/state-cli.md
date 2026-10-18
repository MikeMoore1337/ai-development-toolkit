# Журнал исполнения для зависимых фаз

Включай при необходимости зависимых фаз/восстановления. Для одной функции Markdown и общего budget достаточно. Python 3.10+, stdlib. PROJECT — корень исходников; `.make-feature/SLUG` — metadata конкретной функции. Из каталога навыка через `terminal`:

```text
python3 scripts/state.py --root PROJECT --state-dir .make-feature/SLUG apply init.json
python3 scripts/state.py --root PROJECT --state-dir .make-feature/SLUG apply spec.json
python3 scripts/state.py --root PROJECT --state-dir .make-feature/SLUG apply claim.json
python3 scripts/state.py --root PROJECT --state-dir .make-feature/SLUG apply bind.json
python3 scripts/state.py --root PROJECT --state-dir .make-feature/SLUG check T1 assignment-key --coverage '{"C1":["unit:test_name","scenario:main"]}' --allow-execute -- python3 -m unittest discover -v
python3 scripts/state.py --root PROJECT --state-dir .make-feature/SLUG apply review.json
python3 scripts/state.py --root PROJECT --state-dir .make-feature/SLUG audit
python3 scripts/state.py --root PROJECT --state-dir .make-feature/SLUG show
```

Shell quoting адаптируй к фактической оболочке; Python API `Store.check(..., allow_execute=True)` — тот же явный opt-in. Команды после `--` передаются argv без shell. Однако интерпретатор или тест сам может исполнить произвольный код: inspect + sandbox средствами среды, не вера в shell=False.

`apply` читает одно JSON-событие и никогда не исполняет команды. Неизвестные/missing поля отклоняются, в том числе внутри task. Ключи схемы:

| op | обязательные поля помимо op |
|---|---|
| init | budget (положительное целое), permissions (список только local_write/test) |
| spec | revision (предыдущая + 1), approval (реальная ссылка на согласие), criteria (ID: непустое описание), tasks |
| claim | task, owner (уникальный ключ задания до dispatch) |
| bind | task, owner (ключ claim), worker (реальный ID), provenance (вызов dispatch) |
| block | task, owner, reason |
| recover | reason (все running → interrupted; не kill/retry) |
| reconcile | task, reason (interrupted/blocked/built/verified → pending) |
| review | task, reviewer, provenance, report (относительный файл), spec, quality (pass/fail) |

Task имеет ровно id, criteria (ID array), deps (task ID array), files (непустой список канонических относительных файлов). Файлы могут появиться при реализации, но к check должны существовать. Указывай весь transitive source/test/config/lock manifest; glob не поддерживается. Добавляй screenshot/наблюдения в manifest перед проверкой. Сам DB не является артефактом задачи. PROJECT — cwd команды; DB находится в --state-dir, а без него — в PROJECT.

`claim` запрещён, пока любой узел running или interrupted, даже если files не пересекаются. `recover` сохраняет owner и глобальную блокировку; только явный `reconcile` после остановки worker и проверки эффектов освобождает interrupted узел. Отклонённый claim не расходует бюджет и не меняет state.

`init` не перезаписывает существующую state. Этот бюджет — максимум исполнительских claim, включая первые запуски и repairs, не общий предел делегаций/денег/токенов. Общий budget.py остаётся независимым и не сбрасывается при инициализации ledger. Он неизменяем через CLI: при исчерпании stop, не новый DB для обхода. Пересмотр бюджета владельцем требует отдельного аудируемого продолжения за пределами этого протокола; автоматического increase нет.

Spec заменяется атомарно, требует согласия и отсутствия running/interrupted работ. История событий остаётся в events; общий used сохраняется, прежние task attempts переносятся для совпавших IDs. Новая revision сбрасывает verification всех задач. Не используй revision как способ принять scope reduction без пользователя.

`check` сохраняет argv, exit, stdout/stderr, timestamps, revision, coverage labels и fingerprint каждого listed file: `hashes[name] = {"sha256": "…", "execute_bits": mode & 0o111, "resolved_path": "путь адресата относительно PROJECT"}`. Смена адресата symlink и изменение execute bits без изменения байтов тоже инвалидируют evidence; во время check это exit 125. Старые fingerprints без resolved_path считаются stale: reconcile → claim → check → новый review, без переписывания старых receipts. Fingerprint не отслеживает ACL, владельца, mount flags, окружение или неуказанные файлы. Exit 124 = timeout; 125 = source изменился во время команды; 127 = запуск невозможен. Failed command → blocked; exit 0 → built, НЕ verified. Coverage labels — утверждения автора, reviewer обязан проверить семантику, skipped/filtering и полноту. Своди набор проверок в проверенный test suite с ненулевым exit при любом сбое, не в `echo OK`.

`review` принимает только built со свежим evidence, reviewer не входит в накопленный список implementers проекта (ключи заданий и реальные worker IDs из bind), provenance непустая, report существует. Fingerprint report фиксируется в `review.hash` в том же формате sha256 + execute_bits + resolved_path; смена режима или адресата report тоже инвалидирует audit. Pass/pass → verified, любой fail → blocked. Идентичность и реальность независимого контекста — честная provenance, не криптография. Review текста недостаточно для UI: explicit visual criterion/report проверяется координатором. Изменение report или любого listed file инвалидирует audit и dependency gates.

`claim.owner` — уникальный ключ назначения, который передаётся работнику. После dispatch `bind` записывает task, этот owner, реальный worker ID и provenance вызова. Bind разрешён для running и interrupted: при обрыве до регистрации восстанови прежний ID до reconcile, сохранив блокировку. Родитель выполняет `check` после bind и возврата работника; reviewer указывает собственный реальный ID. Повторный bind требует reconcile и нового claim. Режим без bind сохранён для старых журналов, где owner уже был реальным ID; новые назначения используют bind.

`apply`/`check`/`show` по умолчанию возвращают компактный статус и путь receipt_db; полные argv/output/hashes остаются в SQLite. Для чтения evidence: `state.py --root PROJECT --state-dir .make-feature/SLUG --full show` или --full перед check. Python API сохраняет прежний полный результат. `show` содержит сохранённые статусы и отдельно фактические current flags. `audit` — фактическая актуальность всех узлов и предков, код выхода 0 только при complete=true; иначе 1. Ошибки схемы/полномочий дают CLI exit 2. Check failure даёт CLI 1 и настоящий child exit в JSON. Audit перед init ошибочен: сначала init/spec.

Для исправления: reconcile с причиной → новый claim (спишет попытку) → check → новый независимый review. Не редактируй старый pass report, не обнуляй DB. Состояние не даёт права push/delete/deploy; этих операций здесь нет. Не включай секреты в argv, reports или stdout: они сохраняются локально, автоматической redaction нет.
