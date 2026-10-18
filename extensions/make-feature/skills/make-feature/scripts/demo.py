"""Offline fixture: real tiny CLI/tests, explicitly synthetic review identities."""
import argparse
import json
import sys
from pathlib import Path
from state import Store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.output
    if root.exists():
        parser.error("output must be a new directory; never overwrite an earlier run")
    root.mkdir(parents=True)
    # Only fixed, inspectable code below is generated/executed. No downloaded code.
    (root / "app.py").write_text('import sys\ndef greet(name):\n    return "Hello, " + name.strip()\nif __name__ == "__main__":\n    print(greet(sys.argv[1]))\n', encoding="utf-8")
    (root / "test_app.py").write_text('import subprocess, sys, unittest\nfrom app import greet\nclass Tests(unittest.TestCase):\n    def test_spaces(self):\n        self.assertEqual(greet(" Ada "), "Hello, Ada")\n    def test_cli(self):\n        r = subprocess.run([sys.executable,"app.py","Ada"],capture_output=True,text=True)\n        self.assertEqual(r.returncode,0)\n        self.assertEqual(r.stdout.strip(),"Hello, Ada")\n', encoding="utf-8")
    s = Store(root)
    s.apply({"op":"init","budget":3,"permissions":["local_write","test"]})
    s.apply({"op":"spec","revision":1,"approval":"SYNTHETIC DEMO consent","criteria":{"C1":"CLI greets and trims whitespace"},"tasks":[{"id":"T1","criteria":["C1"],"deps":[],"files":["app.py","test_app.py"]}]})
    s.apply({"op":"claim","task":"T1","owner":"SYNTHETIC-worker-1"})
    s.apply({"op":"recover","reason":"SIMULATED interruption; no external operation"})
    s = Store(root)
    s.apply({"op":"reconcile","task":"T1","reason":"Fixture files inspected; no external writes or live worker"})
    s.apply({"op":"claim","task":"T1","owner":"SYNTHETIC-worker-2"})
    ev = s.check("T1","SYNTHETIC-worker-2",[sys.executable,"-m","unittest","discover","-v"],{"C1":["unit:test_spaces","CLI:test_cli"]},allow_execute=True)
    (root/"review.md").write_text("SYNTHETIC protocol fixture, not an independent LLM review. Tests were actually run. This verdict exists only to exercise ledger transitions.",encoding="utf-8")
    s.apply({"op":"review","task":"T1","reviewer":"SYNTHETIC-reviewer","provenance":"SYNTHETIC fixture; no separate agent executed","report":"review.md","spec":"pass","quality":"pass"})
    before = s.audit()["complete"]
    with (root/"app.py").open("a", encoding="utf-8") as f:
        f.write("\n# edit invalidates previous evidence\n")
    result = {"synthetic_review":True,"test_exit":ev["exit"],"test_output":ev["stderr"],"attempts":s.read()["tasks"]["T1"]["attempts"],"complete_before_edit":before,"complete_after_edit":s.audit()["complete"]}
    (root/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    print(json.dumps(result,indent=2))
    return 0 if ev["exit"] == 0 and before and not result["complete_after_edit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
