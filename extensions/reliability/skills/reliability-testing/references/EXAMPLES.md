# Offline synthetic example (Issue #58)

Run `python scripts/validate_reliability.py --json` within an authorized Toolkit
development checkout. The script uses only temporary local SQLite files,
deterministic schedules, a virtual retry clock and an independent expected-state
fixture; it writes no persistent report to the repository.

Nine fictional cases: duplicate delivery, timeout after a committed effect,
lost update, partial transfer, bounded retry, stale event, ack-before-commit,
reopening a durable store and a version conflict. Each deliberately broken
variant must violate the same expected-state oracle that the reference passes.

A duplicate event E1 applies delta 7 exactly once. Replaying E1 leaves the
counter at 7 and only one recorded event. The bad variant adds 7 again while
the event log still contains one ID. The oracle fails on the **business total**.

A successful commit followed by a lost response is an **unknown client
outcome**, not proof of a failed operation. A stable key and atomic guard prevent
the unsafe second effect in the fictional example.

The lost-update scenario forces both reads before the writes; it is not proof
that a real database is race-free. The restart scenario closes and reopens an
SQLite connection; it does **not** simulate killing the OS process. The retry
test uses virtual delays: [1, 2] and at most three attempts. The ack model
is an abstract protocol check, not a real broker reliability measurement.

**Beginner prompt:** "Проверь, не удвоится ли результат при повторном запросе,
если ответ сервера потерялся. Сначала предложи безопасные локальные тесты и
покажи, что осталось непроверенным."

**Expert prompt:** "Построй инварианты для at-least-once processing, dedupe,
ack-after-commit, optimistic concurrency и restart recovery. Зафиксируй
controlled interleavings, bounded retry, независимые oracles и ограничения
синтетической модели."

No real production, API, queue or external payment call is performed.
