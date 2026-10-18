"""Reserve a run's delegations and repairs; no LLM executor or token meter."""
import argparse
import json
import sqlite3
import sys
import time
from contextlib import closing
from workspace import workspace

DEFAULTS = {"quick": (2, 1, 10), "normal": (6, 1, 25), "deep": (12, 2, 45)}


class Budget:
    def __init__(self, project, slug):
        _, folder = workspace(project, slug)
        if not folder.is_dir():
            raise ValueError("create the feature workspace first")
        self.db = folder / "budget.sqlite3"
        if self.db.is_symlink():
            raise ValueError("budget DB cannot be a symlink")
        with closing(sqlite3.connect(self.db)) as con, con:
            con.execute("CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)")

    def initialize(self, mode, delegations=None, repairs=None, minutes=None):
        if mode not in DEFAULTS:
            raise ValueError("unknown mode")
        calls, fixes, duration = DEFAULTS[mode]
        calls = calls if delegations is None else delegations
        fixes = fixes if repairs is None else repairs
        duration = duration if minutes is None else minutes
        if any(type(x) is not int or x < 0 for x in (calls, fixes, duration)) or duration == 0:
            raise ValueError("nonnegative integer counts and positive integer minutes required")
        started = time.time()
        data = {"mode": mode, "started": started, "deadline": started + duration * 60,
                "limits": {"delegation": calls, "repair": fixes},
                "reservations": {}}
        with closing(sqlite3.connect(self.db)) as con, con:
            con.execute("BEGIN IMMEDIATE")
            if con.execute("SELECT 1 FROM budget WHERE id=1").fetchone():
                raise ValueError("budget already initialized; do not reset on resume or mode change")
            con.execute("INSERT INTO budget VALUES (1, ?)", (json.dumps(data),))
        return self.summary(data)

    def read(self):
        with closing(sqlite3.connect(self.db)) as con:
            row = con.execute("SELECT data FROM budget WHERE id=1").fetchone()
        if not row:
            raise ValueError("initialize budget first")
        return json.loads(row[0])

    def summary(self, data):
        used = {k: sum(v["kind"] == k for v in data["reservations"].values()) for k in data["limits"]}
        left = max(0, int(data["deadline"] - time.time()))
        return {"mode": data["mode"], "used": used,
                "remaining": {k: data["limits"][k] - used[k] for k in used},
                "seconds_left": left, "deadline": data["deadline"],
                "total_llm_tokens": None, "usage_source": "not measured by this helper"}

    def reserve(self, kind, key):
        if kind not in ("delegation", "repair") or not isinstance(key, str) or not key.strip():
            raise ValueError("valid kind and nonempty unique assignment key required")
        with closing(sqlite3.connect(self.db, timeout=5)) as con, con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT data FROM budget WHERE id=1").fetchone()
            if not row:
                raise ValueError("initialize budget first")
            data = json.loads(row[0])
            if key in data["reservations"]:
                raise ValueError("assignment already reserved; inspect its outcome before another dispatch")
            if time.time() >= data["deadline"]:
                raise ValueError("run time budget exhausted")
            used = sum(v["kind"] == kind for v in data["reservations"].values())
            if used >= data["limits"][kind]:
                raise ValueError(f"{kind} budget exhausted")
            data["reservations"][key] = {"kind": kind, "reserved_at": time.time()}
            con.execute("UPDATE budget SET data=? WHERE id=1", (json.dumps(data),))
        return dict(self.summary(data), reserved={"kind": kind, "key": key})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", required=True)
    p.add_argument("--slug", required=True)
    commands = p.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--mode", choices=DEFAULTS, required=True)
    for key in ("delegations", "repairs", "minutes"):
        init.add_argument("--" + key, type=int)
    commands.add_parser("status")
    reserve = commands.add_parser("reserve")
    reserve.add_argument("--kind", choices=("delegation", "repair"), required=True)
    reserve.add_argument("--key", required=True)
    args = p.parse_args()
    try:
        b = Budget(args.project, args.slug)
        if args.command == "init":
            result = b.initialize(args.mode, args.delegations, args.repairs, args.minutes)
        elif args.command == "reserve":
            result = b.reserve(args.kind, args.key)
        else:
            result = b.summary(b.read())
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, sqlite3.Error) as ex:
        print(json.dumps({"error": str(ex)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
