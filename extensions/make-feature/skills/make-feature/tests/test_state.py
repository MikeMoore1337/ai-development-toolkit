import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
try:
    import state
except ModuleNotFoundError:
    state = None

class StateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
    def test_init_persists_without_reset(self):
        self.assertIsNotNone(state, "state helper must exist")
        s = state.Store(self.root)
        s.apply({"op":"init", "budget":3, "permissions":["local_write", "test"]})
        self.assertEqual(state.Store(self.root).read()["budget"], 3)
        with self.assertRaises(ValueError):
            s.apply({"op":"init", "budget":99, "permissions":[]})

    def test_spec_graph_and_revision(self):
        s = state.Store(self.root)
        s.apply({"op":"init", "budget":3, "permissions":["local_write","test"]})
        spec = {"op":"spec", "revision":1, "approval":"user message reference", "criteria":{"C1":"persists"}, "tasks":[{"id":"T1","criteria":["C1"],"deps":[],"files":["app.py"]}]}
        self.assertTrue(hasattr(s, "transition"), "spec transition must exist")
        s.apply(spec)
        self.assertEqual(s.read()["revision"], 1)
        with self.assertRaises(ValueError): s.apply(spec)
        bad = dict(spec, revision=2, tasks=[{"id":"T1","criteria":["C1"],"deps":["T1"],"files":["app.py"]}])
        with self.assertRaises(ValueError): s.apply(bad)
        self.assertEqual(s.read()["revision"], 1)

    def ready(self, budget=3):
        s = state.Store(self.root)
        s.apply({"op":"init", "budget":budget, "permissions":["local_write","test"]})
        s.apply({"op":"spec", "revision":1, "approval":"user-ref", "criteria":{"C1":"works"}, "tasks":[{"id":"T1","criteria":["C1"],"deps":[],"files":["app.py"]}]})
        return s

    def test_claim_owner_recover_budget(self):
        s = self.ready(2)
        self.assertTrue(hasattr(s, "claim"), "claim protocol missing")
        s.apply({"op":"claim","task":"T1","owner":"worker-1"})
        with self.assertRaises(ValueError): s.apply({"op":"claim","task":"T1","owner":"worker-2"})
        s.apply({"op":"recover","reason":"parent exited; effects unknown"})
        self.assertEqual(state.Store(self.root).read()["tasks"]["T1"]["status"], "interrupted")
        with self.assertRaises(ValueError): s.apply({"op":"claim","task":"T1","owner":"worker-2"})
        s.apply({"op":"reconcile","task":"T1","reason":"files inspected; no external effects; worker stopped"})
        s.apply({"op":"claim","task":"T1","owner":"worker-2"})
        s.apply({"op":"block","task":"T1","owner":"worker-2","reason":"test failure"})
        s.apply({"op":"reconcile","task":"T1","reason":"root cause found"})
        with self.assertRaises(ValueError): s.apply({"op":"claim","task":"T1","owner":"worker-3"})
        self.assertEqual(s.read()["used"], 2)

    def test_interrupted_owner_blocks_all_other_claims_until_reconcile(self):
        for other_file in ("app.py", "unrelated.py"):
            with self.subTest(other_file=other_file):
                s = state.Store(self.root / other_file)
                s.apply({"op":"init", "budget":3, "permissions":["local_write", "test"]})
                s.apply({"op":"spec", "revision":1, "approval":"SYNTHETIC", "criteria":{"C1":"works"}, "tasks":[
                    {"id":"T1", "criteria":["C1"], "deps":[], "files":["app.py"]},
                    {"id":"T2", "criteria":["C1"], "deps":[], "files":[other_file]}]})
                s.apply({"op":"claim", "task":"T1", "owner":"old-worker"})
                s.apply({"op":"recover", "reason":"worker outcome unresolved"})
                s = state.Store(s.root)
                before = s.read()
                with self.assertRaisesRegex(ValueError, "single-worker"):
                    s.apply({"op":"claim", "task":"T2", "owner":"new-worker"})
                self.assertEqual(s.read(), before)
                self.assertEqual(before["tasks"]["T1"]["owner"], "old-worker")
                s.apply({"op":"reconcile", "task":"T1", "reason":"worker stopped; effects inspected; ownership safe to release"})
                s.apply({"op":"claim", "task":"T2", "owner":"new-worker"})
                self.assertEqual(s.read()["tasks"]["T2"]["status"], "running")
                self.assertEqual(s.read()["used"], 2)

    def running_fixture(self):
        s = self.ready()
        (self.root / "app.py").write_text("assert 2 + 2 == 4\n")
        s.apply({"op":"claim","task":"T1","owner":"worker"})
        return s

    def test_actual_check_and_independent_review(self):
        s = self.running_fixture()
        self.assertTrue(hasattr(s, "check"), "actual command evidence missing")
        argv = [sys.executable, "app.py"]
        with self.assertRaises(ValueError): s.check("T1", "worker", argv, {"C1":["scenario"]})
        result = s.check("T1", "worker", argv, {"C1":["scenario"]}, allow_execute=True)
        self.assertEqual(result["exit"], 0)
        review = {"op":"review","task":"T1","reviewer":"reviewer-session", "provenance":"separate session reference", "report":"review.md", "spec":"pass","quality":"pass"}
        (self.root/"review.md").write_text("Independent review fixture (SYNTHETIC, not an LLM review).")
        with self.assertRaises(ValueError): s.apply(dict(review, reviewer="worker"))
        self.assertEqual(s.read()["tasks"]["T1"]["status"], "built")
        s.apply(review)
        self.assertEqual(s.read()["tasks"]["T1"]["status"], "verified")
        (self.root/"app.py").write_text("assert False\n")
        self.assertFalse(s.audit()["complete"])

    def test_unknown_fields_and_permissions(self):
        s = state.Store(self.root)
        with self.assertRaises(ValueError):
            s.apply({"op":"init","budget":3,"permissions":["push"]})
        self.assertIsNone(s.read())
        with self.assertRaises(ValueError):
            s.apply({"op":"init","budget":3,"permissions":[],"execute":"bad"})
        with self.assertRaises(ValueError):
            s.apply({"op":"init","budget":True,"permissions":[]})

    def verified_fixture(self):
        s = self.running_fixture()
        s.check("T1", "worker", [sys.executable,"app.py"], {"C1":["scenario"]}, allow_execute=True)
        (self.root/"review.md").write_text("SYNTHETIC review fixture")
        s.apply({"op":"review","task":"T1","reviewer":"reviewer","provenance":"SYNTHETIC independent-context label", "report":"review.md", "spec":"pass","quality":"pass"})
        return s

    def test_stale_dependency_cannot_claim(self):
        s = self.verified_fixture()
        # Add a dependent using the supported new-spec route, then verify predecessor again.
        tasks = [{"id":"T1","criteria":["C1"],"deps":[],"files":["app.py"]}, {"id":"T2","criteria":["C2"],"deps":["T1"],"files":["next.py"]}]
        s.apply({"op":"spec","revision":2,"approval":"user-ref", "criteria":{"C1":"works","C2":"integrates"},"tasks":tasks})
        s.apply({"op":"claim","task":"T1","owner":"worker"})
        s.check("T1","worker",[sys.executable,"app.py"],{"C1":["scenario"]},allow_execute=True)
        s.apply({"op":"review","task":"T1","reviewer":"reviewer","provenance":"SYNTHETIC", "report":"review.md", "spec":"pass","quality":"pass"})
        (self.root/"app.py").write_text("changed")
        with self.assertRaises(ValueError): s.apply({"op":"claim","task":"T2","owner":"worker2"})

    def test_nested_unknown_fields_and_active_revision(self):
        s = self.ready()
        event = {"op":"spec","revision":2,"approval":"user-ref", "criteria":{"C1":"works"},"tasks":[{"id":"T1","criteria":["C1"],"deps":[],"files":["app.py"],"shell":"bad"}]}
        with self.assertRaises(ValueError): s.apply(event)
        event["tasks"][0].pop("shell")
        s.apply({"op":"claim","task":"T1","owner":"worker"})
        with self.assertRaises(ValueError): s.apply(event)

    def test_reconcile_stale_verified_preserves_attempts(self):
        s = self.verified_fixture()
        (self.root/"app.py").write_text("assert True")
        try: s.apply({"op":"reconcile","task":"T1","reason":"changed tracked source; recheck required"})
        except ValueError as ex: self.fail(str(ex))
        s.apply({"op":"claim","task":"T1","owner":"new-worker"})
        self.assertEqual(s.read()["tasks"]["T1"]["attempts"], 2)
        self.assertNotIn("review", s.read()["tasks"]["T1"])

    def test_cli_requires_optin(self):
        import subprocess
        s = self.running_fixture()
        cli = str(Path(state.__file__))
        r = subprocess.run([sys.executable,cli,"--root",str(self.root),"check","T1","worker","--coverage",'{"C1":["scenario"]}',"--",sys.executable,"app.py"],capture_output=True,text=True)
        self.assertNotEqual(r.returncode, 0, "CLI must reject default execution")
        self.assertEqual(s.read()["tasks"]["T1"]["status"], "running")

    def test_execute_mode_changes_invalidate_artifact_and_review(self):
        s = self.verified_fixture()
        for name in ("app.py", "review.md"):
            with self.subTest(file=name):
                p = self.root / name
                original = p.stat().st_mode
                p.chmod(original ^ 0o111)
                try:
                    self.assertFalse(state.Store(self.root).audit()["complete"])
                finally:
                    p.chmod(original)
                self.assertTrue(s.audit()["complete"])

    def test_executable_loss_rejects_review(self):
        s = self.running_fixture()
        app = self.root / "app.py"
        app.write_text("#!/usr/bin/env python3\nprint('works')\n")
        app.chmod(0o755)
        self.assertEqual(s.check("T1", "worker", ["./app.py"], {"C1":["launch"]}, True)["exit"], 0)
        app.chmod(0o644)
        (self.root / "review.md").write_text("SYNTHETIC review fixture")
        with self.assertRaisesRegex(ValueError, "stale evidence"):
            s.apply({"op":"review", "task":"T1", "reviewer":"reviewer", "provenance":"SYNTHETIC", "report":"review.md", "spec":"pass", "quality":"pass"})

    def test_execute_mode_change_during_check_is_blocked(self):
        s = self.running_fixture()
        (self.root / "app.py").chmod(0o644)
        result = s.check("T1", "worker", [sys.executable, "-c", "from pathlib import Path; Path('app.py').chmod(0o755)"], {"C1":["scenario"]}, True)
        self.assertEqual(result["exit"], 125)
        self.assertEqual(s.read()["tasks"]["T1"]["status"], "blocked")

    def test_deleted_artifact_invalidates(self):
        s=self.verified_fixture(); (self.root/"app.py").unlink()
        self.assertFalse(s.audit()["complete"])
    def test_edited_review_invalidates(self):
        s=self.verified_fixture(); (self.root/"review.md").write_text("changed")
        self.assertFalse(s.audit()["complete"])
    def test_failed_command_never_built(self):
        s=self.running_fixture(); (self.root/"app.py").write_text("raise SystemExit(7)")
        self.assertEqual(s.check("T1","worker",[sys.executable,"app.py"],{"C1":["scenario"]},True)["exit"],7)
        self.assertEqual(s.read()["tasks"]["T1"]["status"],"blocked")
    def test_wrong_owner_check(self):
        s=self.running_fixture()
        with self.assertRaises(ValueError): s.check("T1","other",[sys.executable,"app.py"],{"C1":["scenario"]},True)
    def test_empty_coverage_rejected(self):
        s=self.running_fixture()
        with self.assertRaises(ValueError): s.check("T1","worker",[sys.executable,"app.py"],{"C1":[]},True)
    def test_command_changes_tracked_source(self):
        s=self.running_fixture()
        r=s.check("T1","worker",[sys.executable,"-c","from pathlib import Path; Path('app.py').write_text('changed')"],{"C1":["scenario"]},True)
        self.assertEqual(r["exit"],125)
    def test_timeout_is_not_pass(self):
        s=self.running_fixture()
        r=s.check("T1","worker",[sys.executable,"-c","import time; time.sleep(2)"],{"C1":["scenario"]},True,0.01)
        self.assertEqual(r["exit"],124)
    def test_check_missing_binary(self):
        s=self.running_fixture()
        self.assertEqual(s.check("T1","worker",["./nonexistent-command"],{"C1":["scenario"]},True)["exit"],127)
    def test_review_without_evidence_rejected(self):
        s=self.running_fixture()
        with self.assertRaises(ValueError): s.apply({"op":"review","task":"T1","reviewer":"r","provenance":"p","report":"r.md","spec":"pass","quality":"pass"})
    def test_no_permission_claim(self):
        s=state.Store(self.root)
        s.apply({"op":"init","budget":1,"permissions":[]})
        s.apply({"op":"spec","revision":1,"approval":"a","criteria":{"C":"x"},"tasks":[{"id":"T","criteria":["C"],"deps":[],"files":["a"]}]})
        with self.assertRaises(ValueError): s.apply({"op":"claim","task":"T","owner":"w"})
    def test_missing_dependency_rejected(self):
        s=self.ready()
        with self.assertRaises(ValueError): s.apply({"op":"spec","revision":2,"approval":"a","criteria":{"C":"x"},"tasks":[{"id":"T","criteria":["C"],"deps":["missing"],"files":["a"]}]})
    def test_uncovered_criterion_rejected(self):
        s=self.ready()
        with self.assertRaises(ValueError): s.apply({"op":"spec","revision":2,"approval":"a","criteria":{"C":"x","D":"y"},"tasks":[{"id":"T","criteria":["C"],"deps":[],"files":["a"]}]})
    def test_path_escape_rejected(self):
        s=self.ready()
        with self.assertRaises(ValueError): s.apply({"op":"spec","revision":2,"approval":"a","criteria":{"C":"x"},"tasks":[{"id":"T","criteria":["C"],"deps":[],"files":["../a"]}]})
    def test_concurrent_claim_one_winner(self):
        from concurrent.futures import ThreadPoolExecutor
        s=self.ready()
        def claim(owner):
            try: state.Store(self.root).apply({"op":"claim","task":"T1","owner":owner}); return True
            except ValueError: return False
        with ThreadPoolExecutor(2) as pool: results=list(pool.map(claim,["a","b"]))
        self.assertEqual(results.count(True),1)
        self.assertEqual(s.read()["used"],1)
    def test_revision_does_not_reset_budget(self):
        s=self.verified_fixture()
        s.apply({"op":"spec","revision":2,"approval":"a","criteria":{"C":"x"},"tasks":[{"id":"New","criteria":["C"],"deps":[],"files":["app.py"]}]})
        self.assertEqual(s.read()["used"],1)
        self.assertFalse(s.audit()["complete"])
    def test_cli_check_and_audit(self):
        import subprocess
        s=self.running_fixture(); cli=str(Path(state.__file__))
        r=subprocess.run([sys.executable,cli,"--root",str(self.root),"check","T1","worker","--coverage",'{"C1":["scenario"]}',"--allow-execute","--",sys.executable,"app.py"],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertEqual(json.loads(r.stdout)["exit"],0)
        r=subprocess.run([sys.executable,cli,"--root",str(self.root),"audit"],capture_output=True,text=True)
        self.assertEqual(r.returncode,1)
    def test_cli_import_never_executes(self):
        import subprocess
        s=self.ready(); f=self.root/"event.json"
        f.write_text(json.dumps({"op":"check","argv":["bad"]}))
        r=subprocess.run([sys.executable,str(Path(state.__file__)),"--root",str(self.root),"apply",str(f)],capture_output=True,text=True)
        self.assertEqual(r.returncode,2)
        self.assertEqual(s.read()["used"],0)

    def test_connections_are_closed(self):
        import gc
        import warnings
        gc.collect()
        with warnings.catch_warnings(record=True) as seen:
            warnings.simplefilter("always", ResourceWarning)
            s=self.ready(); s.read(); gc.collect()
        self.assertFalse([w for w in seen if issubclass(w.category, ResourceWarning)])

    def test_offline_demo(self):
        import subprocess
        demo=Path(state.__file__).with_name("demo.py")
        self.assertTrue(demo.exists(), "offline lifecycle demo missing")
        r=subprocess.run([sys.executable,str(demo),"--output",str(self.root/"demo")],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        result=json.loads(r.stdout)
        self.assertTrue(result["synthetic_review"])
        self.assertTrue(result["complete_before_edit"])
        self.assertFalse(result["complete_after_edit"])
        self.assertEqual(result["test_exit"],0)
        self.assertEqual(result["attempts"],2)

    def test_previous_implementer_cannot_review(self):
        s=self.running_fixture()
        s.apply({"op":"block","task":"T1","owner":"worker","reason":"handoff"})
        s.apply({"op":"reconcile","task":"T1","reason":"worker stopped"})
        s.apply({"op":"claim","task":"T1","owner":"second"})
        s.check("T1","second",[sys.executable,"app.py"],{"C1":["scenario"]},True)
        (self.root/"review.md").write_text("SYNTHETIC")
        with self.assertRaises(ValueError): s.apply({"op":"review","task":"T1","reviewer":"worker","provenance":"different label is not independent","report":"review.md","spec":"pass","quality":"pass"})

if __name__ == "__main__":
    unittest.main()
