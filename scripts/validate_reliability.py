#!/usr/bin/env python3
"""Issue #58: bounded offline reliability oracles over fictional SQLite state.

Synthetic evidence only: NOT a real broker, distributed system or production test.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "fixtures" / "reliability" / "cases.json"
CASE_IDS = (
    "duplicate-delivery", "timeout-after-effect", "lost-update",
    "partial-transaction", "retry-budget", "out-of-order",
    "ack-before-commit", "restart-recovery", "version-conflict",
)
MUTANTS = {
    "duplicate-delivery": "duplicate-effect",
    "timeout-after-effect": "unsafe-timeout-retry",
    "lost-update": "stale-write",
    "partial-transaction": "partial-commit",
    "retry-budget": "unbounded-retry",
    "out-of-order": "stale-event-overwrite",
    "ack-before-commit": "early-ack",
    "restart-recovery": "volatile-dedup",
    "version-conflict": "missing-version-check",
}
REQUIRED = {
    "case_id", "system", "source_requirement", "business_invariant",
    "initial_state", "operation", "failure_point", "failure_type",
    "injection_method", "expected_observable_result", "expected_persistent_state",
    "recovery_behavior", "execution_bound", "test_level", "actual_evidence",
    "result_status", "limitations",
}
STATUSES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "NOT_MEASURED", "NOT_APPLICABLE"}
RECOVERY = {"RECOVERED", "RECOVERY_PENDING", "RECOVERY_BLOCKED", "STATE_UNKNOWN"}


class InjectedFailure(RuntimeError):
    """A deterministic local fault at a documented operation boundary."""


def validate_case(case: object) -> list[str]:
    if not isinstance(case, dict):
        return ["case must be an object"]
    errors = []
    missing = REQUIRED - case.keys()
    if missing:
        errors.append("missing contract fields: " + ", ".join(sorted(missing)))
    if not isinstance(case.get("case_id"), str) or case.get("case_id") not in CASE_IDS:
        errors.append("unknown case_id")
    if not case.get("business_invariant"):
        errors.append("missing business invariant")
    if not isinstance(case.get("expected_persistent_state"), dict):
        errors.append("missing expected persistent state")
    if case.get("result_status") not in STATUSES:
        errors.append("unknown result status")
    if not isinstance(case.get("execution_bound"), int) or isinstance(
        case.get("execution_bound"), bool
    ) or not 1 <= case["execution_bound"] <= 30:
        errors.append("unsafe execution bound")
    if case.get("actual_evidence") not in (None, "NOT_RUN"):
        errors.append("fixture must not claim execution evidence")
    if not isinstance(case.get("limitations"), list) or not case["limitations"]:
        errors.append("limitations must be explicit")
    return errors


def digest(case: dict) -> str:
    data = json.dumps(case, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def load_cases(path: Path = CASES) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("fixture_version") != "1.0.0":
        raise ValueError("unsupported fixture version")
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("empty case catalog")
    ids = [item.get("case_id") for item in cases if isinstance(item, dict)]
    if len(ids) != len(cases) or len(ids) != len(set(ids)) or set(ids) != set(CASE_IDS):
        raise ValueError("missing or duplicated case IDs")
    for case in cases:
        problems = validate_case(case)
        if problems:
            raise ValueError(f"{case.get('case_id')}: {problems}")
    return cases


def _open(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path, timeout=2, isolation_level=None)
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("CREATE TABLE IF NOT EXISTS counter (id INTEGER PRIMARY KEY, n INTEGER NOT NULL)")
    conn.execute("CREATE TABLE IF NOT EXISTS applied (event_id TEXT PRIMARY KEY)")
    conn.execute("INSERT OR IGNORE INTO counter VALUES (1, 0)")
    return conn


def _apply(conn: sqlite3.Connection, key: str, delta: int, unsafe: bool) -> None:
    conn.execute("BEGIN IMMEDIATE")
    inserted = conn.execute("INSERT OR IGNORE INTO applied VALUES (?)", (key,)).rowcount
    if inserted or unsafe:
        conn.execute("UPDATE counter SET n=n+? WHERE id=1", (delta,))
    conn.commit()


def _counter(conn: sqlite3.Connection) -> dict:
    return {
        "count": conn.execute("SELECT n FROM counter WHERE id=1").fetchone()[0],
        "unique_events": conn.execute("SELECT COUNT(*) FROM applied").fetchone()[0],
    }


def simulate(case_id: str, mutant: bool = False) -> dict:
    """Run one bounded, deterministic schedule. No network or background workers."""
    if case_id not in CASE_IDS:
        raise ValueError("unknown scenario")
    with tempfile.TemporaryDirectory(prefix="adt-reliability-") as folder:
        db = Path(folder) / "fictional.sqlite3"
        conn = _open(db)
        try:
            if case_id == "duplicate-delivery":
                _apply(conn, "E1", 7, False)
                _apply(conn, "E1", 7, mutant)
                return _counter(conn)

            if case_id == "timeout-after-effect":
                _apply(conn, "E2", 9, False)
                # Commit succeeded. The response is lost before the client sees it.
                try:
                    raise InjectedFailure("response lost after commit")
                except InjectedFailure:
                    _apply(conn, "E2", 9, mutant)
                return _counter(conn)

            if case_id == "lost-update":
                # Forced schedule: read A, read B, write A, write B.
                a = conn.execute("SELECT n FROM counter WHERE id=1").fetchone()[0]
                b = conn.execute("SELECT n FROM counter WHERE id=1").fetchone()[0]
                conn.execute("UPDATE counter SET n=? WHERE id=1", (a + 4,))
                if mutant:
                    conn.execute("UPDATE counter SET n=? WHERE id=1", (b + 7,))
                else:
                    conn.execute("UPDATE counter SET n=n+7 WHERE id=1")
                return {"count": _counter(conn)["count"]}

            if case_id == "partial-transaction":
                conn.execute("CREATE TABLE wallets (name TEXT PRIMARY KEY, amount INTEGER)")
                conn.executemany("INSERT INTO wallets VALUES (?,?)", [("A", 20), ("B", 0)])
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    conn.execute("UPDATE wallets SET amount=amount-5 WHERE name='A'")
                    if mutant:
                        conn.commit()
                    raise InjectedFailure("after debit before credit")
                except InjectedFailure:
                    conn.rollback()
                return dict(conn.execute("SELECT name, amount FROM wallets ORDER BY name"))

            if case_id == "retry-budget":
                attempts = 0
                virtual_delays = []
                maximum = 4 if mutant else 3
                for index in range(maximum):
                    attempts += 1
                    # Dependency is permanently failing. Virtual delays, no sleep.
                    if index < maximum - 1:
                        virtual_delays.append(min(2 ** index, 4))
                return {"attempts": attempts, "delays": virtual_delays,
                        "outcome": "EXHAUSTED"}

            if case_id == "out-of-order":
                conn.execute("CREATE TABLE stream (version INTEGER, value INTEGER)")
                conn.execute("INSERT INTO stream VALUES (0, 0)")
                for version, value in ((2, 20), (1, 10)):
                    old = conn.execute("SELECT version FROM stream").fetchone()[0]
                    if mutant or version > old:
                        conn.execute("UPDATE stream SET version=?, value=?",
                                     (version, value))
                version, value = conn.execute("SELECT version, value FROM stream").fetchone()
                return {"version": version, "value": value}

            if case_id == "ack-before-commit":
                ack = False
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    if mutant:
                        ack = True
                    raise InjectedFailure("after ack decision, before durable effect")
                except InjectedFailure:
                    conn.rollback()
                return {"acknowledged": ack, "count": _counter(conn)["count"]}

            if case_id == "restart-recovery":
                _apply(conn, "E7", 6, False)
                conn.close()
                conn = _open(db)  # Real connection reopen, not a process crash.
                _apply(conn, "E7", 6, mutant)
                return _counter(conn)

            if case_id == "version-conflict":
                conn.execute("CREATE TABLE object (version INTEGER, value INTEGER)")
                conn.execute("INSERT INTO object VALUES (0, 0)")
                read_version = conn.execute("SELECT version FROM object").fetchone()[0]
                first = conn.execute(
                    "UPDATE object SET version=version+1,value=4 WHERE version=?",
                    (read_version,),
                ).rowcount
                if mutant:
                    second = conn.execute("UPDATE object SET value=9").rowcount
                else:
                    second = conn.execute(
                        "UPDATE object SET version=version+1,value=9 WHERE version=?",
                        (read_version,),
                    ).rowcount
                version, value = conn.execute("SELECT version,value FROM object").fetchone()
                return {"version": version, "value": value,
                        "first_accepted": first == 1, "second_rejected": second == 0}
            raise AssertionError("unreachable")
        finally:
            conn.close()


def run_case(case: dict, mutant: bool = False) -> dict:
    started = time.monotonic()
    observed = simulate(case["case_id"], mutant)
    duration = time.monotonic() - started
    # Independent expected state comes from the pinned fixture, not simulate().
    expected = case["expected_persistent_state"]
    success = observed == expected and duration <= case["execution_bound"]
    return {
        "case_id": case["case_id"],
        "fixture_version": "1.0.0",
        "input_sha256": digest(case),
        "tested_invariant": case["business_invariant"],
        "failure_point": case["failure_point"],
        "execution_method": "local deterministic SQLite/virtual-schedule model",
        "test_environment": "Python stdlib; temporary SQLite database",
        "expected_state": expected,
        "observed_state": observed,
        "oracle_outcome": "PASS" if success else "FAIL",
        "retry_count": max(0, observed.get("attempts", 1) - 1),
        "recovery_outcome": "RECOVERED" if success else "STATE_UNKNOWN",
        "bounded_duration_seconds": round(duration, 6),
        "reproduction": {"case_id": case["case_id"], "mutant": mutant,
                         "failure_point": case["failure_point"], "seed": None},
        "remaining_limitations": case["limitations"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print bounded evidence")
    args = parser.parse_args()
    try:
        cases = load_cases()
        results = []
        for case in cases:
            good = run_case(case)
            broken = run_case(case, mutant=True)
            if good["oracle_outcome"] != "PASS" or broken["oracle_outcome"] != "FAIL":
                raise AssertionError("oracle failed to distinguish reference from mutant")
            results.append({"reference": good, "mutant": broken,
                            "mutant_name": MUTANTS[case["case_id"]]})
    except (ValueError, OSError, sqlite3.Error, AssertionError) as exc:
        print(f"FAIL: {exc}")
        return 1
    if args.json:
        print(json.dumps({"status": "PASS", "synthetic_cases": len(results),
                          "mutants_detected": len(results), "results": results},
                         indent=2, ensure_ascii=False))
    else:
        print(f"PASS: {len(results)} reference oracles and "
              f"{len(results)} deliberately broken implementations rejected; "
              "no real infrastructure tested")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
