"""Local transactional ledger, not an agent runner or security boundary."""
import json
import sqlite3
import hashlib
import subprocess
import time
from contextlib import closing
from pathlib import Path


class Store:
    def __init__(self, root, state_dir=None):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        metadata = self.root
        if state_dir is not None:
            p = Path(state_dir)
            if p.is_absolute() or ".." in p.parts or "\\" in str(state_dir) or p.as_posix() != str(state_dir):
                raise ValueError("canonical relative state directory required")
            metadata = (self.root / p).resolve()
            if not metadata.is_relative_to(self.root):
                raise ValueError("state directory must stay inside project")
            metadata.mkdir(parents=True, exist_ok=True)
        self.db = metadata / "state.sqlite3"
        if self.db.is_symlink():
            raise ValueError("state DB cannot be a symlink")
        with closing(sqlite3.connect(self.db)) as con, con:
            con.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY CHECK(id=1), data TEXT NOT NULL)")
            con.execute("CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)")

    def read(self):
        with closing(sqlite3.connect(self.db)) as con, con:
            row = con.execute("SELECT data FROM state WHERE id=1").fetchone()
        return json.loads(row[0]) if row else None

    def transition(self, d, e):
        fields = {"init": "budget permissions", "spec": "revision approval criteria tasks",
                  "claim": "task owner", "recover": "reason", "reconcile": "task reason",
                  "bind": "task owner worker provenance",
                  "block": "task owner reason", "review": "task reviewer provenance report spec quality"}
        if not isinstance(e, dict) or e.get("op") not in fields:
            raise ValueError("unknown event")
        op = e["op"]
        if set(e) != {"op", *fields[op].split()}:
            raise ValueError("missing or unknown fields")
        if op == "init":
            if type(e["budget"]) is not int or e["budget"] < 1:
                raise ValueError("positive integer budget required")
            if not isinstance(e["permissions"], list) or any(p not in ("local_write", "test") for p in e["permissions"]):
                raise ValueError("only local_write and test can be recorded")
            if d is not None:
                raise ValueError("already initialized")
            return {"budget": e["budget"], "permissions": e["permissions"], "used": 0,
                    "revision": 0, "criteria": {}, "tasks": {}, "implementers": []}
        if d is None:
            raise ValueError("initialize first")
        if op == "spec":
            if any(t["status"] in ("running", "interrupted") for t in d["tasks"].values()):
                raise ValueError("reconcile active work before spec revision")
            if not isinstance(e["criteria"], dict) or not all(isinstance(k,str) and k.strip() and isinstance(v,str) and v.strip() for k,v in e["criteria"].items()):
                raise ValueError("criteria IDs and descriptions required")
            if not isinstance(e["tasks"], list):
                raise ValueError("tasks must be array")
            for t in e["tasks"]:
                if not isinstance(t,dict) or set(t) != {"id","criteria","deps","files"}:
                    raise ValueError("unknown task fields")
                if not isinstance(t["id"],str) or not t["id"].strip():
                    raise ValueError("task ID required")
                for field in ("criteria","deps","files"):
                    if not isinstance(t[field],list) or not all(isinstance(x,str) and x.strip() for x in t[field]) or len(set(t[field])) != len(t[field]):
                        raise ValueError("invalid task array")
                if not t["files"]:
                    raise ValueError("tracked files required")
                for name in t["files"]:
                    p = Path(name)
                    if p.is_absolute() or ".." in p.parts or "\\" in name or p.as_posix() != name or name.startswith("state.sqlite3"):
                        raise ValueError("canonical relative file required")
            if type(e["revision"]) is not int or e["revision"] != d["revision"] + 1 or not isinstance(e["approval"],str) or not e["approval"].strip():
                raise ValueError("revision or approval missing")
            tasks = {t["id"]: dict(t) for t in e["tasks"]}
            if len(tasks) != len(e["tasks"]) or not tasks or not e["criteria"]:
                raise ValueError("duplicate or empty tasks/criteria")
            covered = set()
            def visit(tid, stack):
                if tid not in tasks or tid in stack:
                    raise ValueError("missing dependency or cycle")
                for dep in tasks[tid]["deps"]:
                    visit(dep, stack | {tid})
            for tid, t in tasks.items():
                visit(tid, set())
                if not t["criteria"] or not set(t["criteria"]) <= set(e["criteria"]):
                    raise ValueError("unknown or empty criteria")
                covered.update(t["criteria"])
                t.update(status="pending", attempts=d["tasks"].get(tid, {}).get("attempts", 0))
            if covered != set(e["criteria"]):
                raise ValueError("uncovered criteria")
            d.update(revision=e["revision"], criteria=e["criteria"], tasks=tasks)
            return d
        if op == "review":
            t = d["tasks"][e["task"]]
            if t["status"] != "built" or not self.fresh(t):
                raise ValueError("not built or stale evidence")
            if not e["reviewer"].strip() or e["reviewer"] in d["implementers"] or not e["provenance"].strip():
                raise ValueError("independent review provenance required")
            if e["spec"] not in ("pass", "fail") or e["quality"] not in ("pass", "fail"):
                raise ValueError("invalid verdict")
            t["review"] = dict(e, hash=self.digest(e["report"]))
            t["status"] = "verified" if e["spec"] == e["quality"] == "pass" else "blocked"
            return d
        if op == "claim":
            self.claim(d, e)
            return d
        if op == "bind":
            t = d["tasks"][e["task"]]
            if t["status"] not in ("running", "interrupted") or t["owner"] != e["owner"]:
                raise ValueError("running/interrupted assignment owner required")
            if not isinstance(e["worker"], str) or not e["worker"].strip() or not isinstance(e["provenance"], str) or not e["provenance"].strip():
                raise ValueError("actual worker and dispatch provenance required")
            if "worker_id" in t:
                raise ValueError("worker already bound; reconcile before another assignment")
            t.update(worker_id=e["worker"], worker_provenance=e["provenance"])
            if e["worker"] not in d["implementers"]:
                d["implementers"].append(e["worker"])
            return d
        if op == "recover":
            if not e["reason"].strip():
                raise ValueError("reason required")
            for t in d["tasks"].values():
                if t["status"] == "running":
                    t.update(status="interrupted", reason=e["reason"])
            return d
        if op in ("block", "reconcile"):
            t = d["tasks"][e["task"]]
            if not e["reason"].strip():
                raise ValueError("reason required")
            if op == "block":
                if t["status"] != "running" or t["owner"] != e["owner"]:
                    raise ValueError("not running owner")
                t.update(status="blocked", reason=e["reason"])
            else:
                if t["status"] not in ("interrupted", "blocked", "built", "verified"):
                    raise ValueError("not blocked/interrupted")
                t.update(status="pending", reason=e["reason"])
            return d
        raise ValueError("unknown operation")

    def claim(self, d, e):
        t = d["tasks"][e["task"]]
        if not e["owner"].strip() or t["status"] != "pending":
            raise ValueError("not pending or empty owner")
        if any(x["status"] in ("running", "interrupted") for x in d["tasks"].values()):
            raise ValueError("local single-worker mode: running or interrupted owner exists; reconcile interrupted work first")
        if any(not self.valid(d, dep) for dep in t["deps"]):
            raise ValueError("unverified predecessor")
        if d["used"] >= d["budget"]:
            raise ValueError("attempt budget exhausted; blocked")
        if "local_write" not in d["permissions"]:
            raise ValueError("local_write permission absent")
        t.pop("review", None)
        t.pop("evidence", None)
        t.pop("worker_id", None)
        t.pop("worker_provenance", None)
        if e["owner"] not in d["implementers"]:
            d["implementers"].append(e["owner"])
        d["used"] += 1
        t.update(status="running", owner=e["owner"], attempts=t["attempts"] + 1)

    def digest(self, name):
        p = (self.root / name).resolve()
        if not p.is_relative_to(self.root) or p == self.db or not p.is_file():
            raise ValueError("artifact must be a regular project file")
        # Bind both artifact and review fingerprints to execution-relevant mode.
        # Legacy byte-only fingerprints compare unequal and require a fresh check.
        return {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
                "execute_bits": p.stat().st_mode & 0o111,
                "resolved_path": p.relative_to(self.root).as_posix()}

    def snapshot(self, task):
        return {name: self.digest(name) for name in task["files"]}

    def fresh(self, task):
        try:
            ev = task["evidence"]
            valid = ev["exit"] == 0 and ev["hashes"] == self.snapshot(task)
            if "review" in task:
                valid = valid and task["review"]["hash"] == self.digest(task["review"]["report"])
            return valid
        except (KeyError, ValueError, OSError):
            return False

    def valid(self, d, tid):
        t = d["tasks"][tid]
        return t["status"] == "verified" and self.fresh(t) and all(self.valid(d, x) for x in t["deps"])

    def audit(self):
        d = self.read()
        memo = {}
        def valid(tid):
            if tid not in memo:
                t = d["tasks"][tid]
                memo[tid] = t["status"] == "verified" and self.fresh(t) and all(valid(x) for x in t["deps"])
            return memo[tid]
        flags = {tid: valid(tid) for tid in d["tasks"]}
        return {"complete": bool(flags) and all(flags.values()), "current": flags}

    def check(self, tid, owner, argv, coverage, allow_execute=False, timeout=30):
        # Only explicit caller opt-in executes argv; JSON events cannot invoke this.
        if not allow_execute:
            raise ValueError("explicit --allow-execute required; inspect command first")
        if not isinstance(argv, list) or not argv or not all(isinstance(x, str) and x for x in argv):
            raise ValueError("argv must be a nonempty string array")
        if not 0 < timeout <= 300:
            raise ValueError("timeout must be 1..300 seconds")
        with closing(sqlite3.connect(self.db, timeout=5)) as con, con:
            con.execute("BEGIN IMMEDIATE")
            d = json.loads(con.execute("SELECT data FROM state WHERE id=1").fetchone()[0])
            t = d["tasks"][tid]
            if t["status"] != "running" or t["owner"] != owner or "test" not in d["permissions"]:
                raise ValueError("running owner and test permission required")
            if set(coverage) != set(t["criteria"]) or any(not isinstance(v, list) or not v or not all(isinstance(x,str) and x.strip() for x in v) for v in coverage.values()):
                raise ValueError("coverage labels required for every criterion")
            before = self.snapshot(t)
            started = time.time()
            try:
                result = subprocess.run(argv, cwd=self.root, capture_output=True, timeout=timeout, shell=False)
                code, out, err = result.returncode, result.stdout.decode("utf-8", "replace"), result.stderr.decode("utf-8", "replace")
            except subprocess.TimeoutExpired as ex:
                code, out, err = 124, (ex.stdout or b"").decode("utf-8", "replace"), "timeout; inspect subprocess descendants before retry"
            except OSError as ex:
                code, out, err = 127, "", str(ex)
            try:
                after = self.snapshot(t)
            except (ValueError, OSError):
                after = {}
            if before != after:
                code = 125
                err += "\ntracked files changed during check"
            ev = {"argv":argv, "exit":code, "stdout":out, "stderr":err, "hashes":before,
                  "coverage":coverage, "revision":d["revision"], "started":started, "finished":time.time()}
            t.update(evidence=ev, status="built" if code == 0 else "blocked")
            t.pop("review", None)
            con.execute("UPDATE state SET data=? WHERE id=1", (json.dumps(d),))
            con.execute("INSERT INTO events(payload) VALUES (?)", (json.dumps({"op":"check","task":tid,"evidence":ev}),))
            return ev

    def apply(self, event):
        with closing(sqlite3.connect(self.db, timeout=5)) as con, con:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT data FROM state WHERE id=1").fetchone()
            data = json.loads(row[0]) if row else None
            data = self.transition(data, event)
            con.execute("INSERT OR REPLACE INTO state VALUES (1, ?)", (json.dumps(data),))
            con.execute("INSERT INTO events(payload) VALUES (?)", (json.dumps(event),))
            return data


def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="project root; DB and tracked files live here")
    parser.add_argument("--state-dir", help="relative metadata directory; tracked files remain relative to root")
    parser.add_argument("--full", action="store_true", help="print complete receipts instead of a compact summary")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    sub.add_parser("audit")
    event = sub.add_parser("apply")
    event.add_argument("event_file", help="strict JSON event; never executes commands")
    check = sub.add_parser("check")
    check.add_argument("task")
    check.add_argument("owner")
    check.add_argument("--coverage", required=True, help="JSON criterion-to-labels object")
    check.add_argument("--allow-execute", action="store_true")
    check.add_argument("--timeout", type=int, default=30)
    args_in = sys.argv[1:]
    argv = []
    if "--" in args_in:
        idx = args_in.index("--")
        args_in, argv = args_in[:idx], args_in[idx+1:]
    args = parser.parse_args(args_in)
    try:
        store = Store(args.root, args.state_dir)
        code = 0
        if args.cmd == "show":
            result = store.read()
        elif args.cmd == "audit":
            result = store.audit()
            code = 0 if result["complete"] else 1
        elif args.cmd == "apply":
            result = store.apply(json.loads(Path(args.event_file).read_text(encoding="utf-8")))
        else:
            result = store.check(args.task, args.owner, argv, json.loads(args.coverage), args.allow_execute, args.timeout)
            code = 0 if result["exit"] == 0 else 1
        if not args.full and args.cmd in ("apply", "show") and result is not None:
            result = {"revision": result["revision"], "used": result["used"], "budget": result["budget"],
                      "tasks": {k: {field: t[field] for field in ("status", "owner", "worker_id") if field in t}
                                for k, t in result["tasks"].items()},
                      "current": store.audit()["current"], "receipt_db": str(store.db)}
        elif not args.full and args.cmd == "check":
            result = {"task": args.task, "exit": result["exit"],
                      "argv_preview": [x[:160] + ("…" if len(x) > 160 else "") for x in result["argv"][:12]],
                      "argv_count": len(result["argv"]),
                      "coverage_criteria": list(result["coverage"]), "duration_seconds": result["finished"] - result["started"],
                      "receipt_db": str(store.db), "error_tail": result["stderr"][-1200:] if code else ""}
        if not args.full and len(json.dumps(result, ensure_ascii=False)) > 8000:
            result = {"summary_truncated": True, "command": args.cmd, "receipt_db": str(store.db),
                      "exit": result.get("exit") if isinstance(result, dict) else None,
                      "hint": "Use --full to inspect complete evidence before acting on omitted details"}
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.full else None))
        return code
    except (ValueError, KeyError, TypeError, AttributeError, OSError, sqlite3.Error) as ex:
        print(json.dumps({"error": str(ex)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
