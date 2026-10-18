import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("workspace", SCRIPTS / "workspace.py")
workspace = importlib.util.module_from_spec(spec)
spec.loader.exec_module(workspace)
spec = importlib.util.spec_from_file_location("ledger", SCRIPTS / "state.py")
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class ContextTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.request = self.root / "request.txt"
        self.raw = "Сделай функцию.  Исходные слова\nбез редактуры.\n".encode()
        self.request.write_bytes(self.raw)

    def init(self):
        return Path(workspace.initialize(self.root, "import-csv", self.request)["workspace"])

    def test_exact_request_and_initial_links(self):
        folder = self.init()
        self.assertEqual((folder / "01-request.md").read_bytes(), self.raw)
        self.assertTrue(workspace.check(self.root, "import-csv")["structurally_valid"])
        self.assertFalse(workspace.check(self.root, "import-csv")["content_accepted"])

    def test_second_init_preserves_all_existing_documents(self):
        folder = self.init()
        index = folder / "00-index.md"
        index.write_text("accepted work")
        with self.assertRaises(FileExistsError):
            self.init()
        self.assertEqual(index.read_text(), "accepted work")

    def test_source_edit_is_detected(self):
        folder = self.init()
        (folder / "01-request.md").write_text("переписанный запрос")
        result = workspace.check(self.root, "import-csv")
        self.assertFalse(result["structurally_valid"])
        self.assertIn("source request changed", result["errors"])

    def test_broken_link_and_real_project_link(self):
        folder = self.init()
        doc = folder / "02-brief.md"
        doc.write_text("[contract](../../contracts.md)\n[decision](05-decision.md)\n")
        (self.root / "contracts.md").write_text("actual contract")
        result = workspace.check(self.root, "import-csv")
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("05-decision.md", result["errors"][0])
        (folder / "05-decision.md").write_text("accepted")
        self.assertTrue(workspace.check(self.root, "import-csv")["structurally_valid"])

    def test_archive_and_code_examples_are_not_live_dependencies(self):
        folder = self.init()
        (folder / "archive").mkdir()
        (folder / "archive" / "old.md").write_text("[old](gone.md)")
        (folder / "02-brief.md").write_text("```text\n[sample](not-a-file.md)\n```\n[web](https://example.com/x)\n")
        self.assertTrue(workspace.check(self.root, "import-csv")["structurally_valid"])

    def test_inline_code_is_not_a_link_and_parenthesized_file_is_valid(self):
        folder = self.init()
        (folder / "contract(v1).md").write_text("actual contract")
        (folder / "02-solution.md").write_text('`[example](absent.md)`\n[contract](contract(v1).md "title")\n')
        self.assertTrue(workspace.check(self.root, "import-csv")["structurally_valid"])
        (folder / "contract(v1).md").unlink()
        errors = workspace.check(self.root, "import-csv")["errors"]
        self.assertEqual(len(errors),1)
        self.assertIn("contract(v1).md",errors[0])

    def test_missing_image_asset_is_detected(self):
        folder = self.init()
        (folder / "06-architecture.md").write_text("![diagram](flow.png)")
        self.assertFalse(workspace.check(self.root, "import-csv")["structurally_valid"])
        (folder / "flow.png").write_bytes(b"example image artifact")
        self.assertTrue(workspace.check(self.root, "import-csv")["structurally_valid"])

    def test_reference_link_and_encoded_space_are_checked(self):
        folder = self.init()
        doc = folder / "04-research.md"
        doc.write_text("[source][S1]\n\n[S1]: absent.md\n[contract](with%20space.md)\n")
        (folder / "with space.md").write_text("actual contract")
        errors = workspace.check(self.root, "import-csv")["errors"]
        self.assertEqual(len(errors), 1)
        self.assertIn("absent.md", errors[0])
        (folder / "absent.md").write_text("source retained")
        self.assertTrue(workspace.check(self.root, "import-csv")["structurally_valid"])

    def test_undefined_full_and_collapsed_references_fail(self):
        folder = self.init()
        doc = folder / "04-research.md"
        doc.write_text("[source][missing]\n[contract][]\n")
        self.assertFalse(workspace.check(self.root, "import-csv")["structurally_valid"])
        (folder / "source.md").write_text("actual evidence")
        doc.write_text("[source][MISSING]\n[contract][]\n\n[missing]: source.md\n[contract]: source.md\n")
        self.assertTrue(workspace.check(self.root, "import-csv")["structurally_valid"])

    def test_path_escape_and_source_symlink_rejected(self):
        for slug in ("../outside", "x/y", "UPPER", "", "a--b"):
            with self.subTest(slug=slug), self.assertRaises(ValueError):
                workspace.initialize(self.root, slug, self.request)
        folder = self.init()
        (folder / "02-brief.md").write_text("[outside](../../../outside.md)\n")
        self.assertFalse(workspace.check(self.root, "import-csv")["structurally_valid"])
        source = folder / "01-request.md"
        source.unlink()
        source.symlink_to(self.request)
        self.assertIn("source request must be a regular preserved file", workspace.check(self.root, "import-csv")["errors"])

    def test_cli_broken_link_returns_nonzero(self):
        folder = self.init()
        (folder / "02-brief.md").write_text("[lost](missing.md)")
        result = subprocess.run([sys.executable, str(SCRIPTS / "workspace.py"), "check", "--project", str(self.root), "--slug", "import-csv"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertFalse(json.loads(result.stdout)["structurally_valid"])

    def test_context_symlink_cannot_write_outside_project(self):
        with tempfile.TemporaryDirectory() as outside:
            (self.root / ".make-feature").symlink_to(outside)
            with self.assertRaises(ValueError):
                self.init()
            self.assertEqual(list(Path(outside).iterdir()), [])


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_isolated_ledgers_track_project_files(self):
        (self.root / "app.py").write_text("print('working')\n")
        a = ledger.Store(self.root, ".make-feature/a")
        b = ledger.Store(self.root, ".make-feature/b")
        a.apply({"op": "init", "budget": 2, "permissions": ["local_write", "test"]})
        self.assertIsNone(b.read())
        self.assertEqual(a.digest("app.py")["sha256"], b.digest("app.py")["sha256"])
        with self.assertRaises(ValueError):
            a.digest(".make-feature/a/state.sqlite3")
        self.assertFalse((self.root / "state.sqlite3").exists())

    def test_metadata_cannot_escape_project(self):
        for name in ("../outside", "/tmp/outside", "a/../b", "a\\b"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                ledger.Store(self.root, name)
        with tempfile.TemporaryDirectory() as outside:
            (self.root / "link").symlink_to(outside)
            with self.assertRaises(ValueError):
                ledger.Store(self.root, "link")

    def test_state_db_symlink_does_not_create_or_modify_outside_database(self):
        with tempfile.TemporaryDirectory() as outside:
            target = Path(outside) / "outside.sqlite3"
            (self.root / "state.sqlite3").symlink_to(target)
            with self.assertRaises(ValueError): ledger.Store(self.root)
            self.assertFalse(target.exists())

    def test_cli_metadata_option_creates_only_scoped_db(self):
        event = self.root / "init.json"
        event.write_text(json.dumps({"op": "init", "budget": 2, "permissions": ["test"]}))
        result = subprocess.run([sys.executable, str(SCRIPTS / "state.py"), "--root", str(self.root), "--state-dir", ".make-feature/a", "apply", str(event)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(ledger.Store(self.root, ".make-feature/a").read()["budget"], 2)
        self.assertFalse((self.root / "state.sqlite3").exists())

    def test_compact_cli_keeps_complete_evidence_and_full_output_available(self):
        s = self.running_assignment()
        cli = [sys.executable, str(SCRIPTS / "state.py"), "--root", str(self.root), "--state-dir", ".make-feature/a"]
        command = cli + ["check", "T1", "T1-attempt-1", "--coverage", '{"C1":["SYNTHETIC receipt-size fixture"]}', "--allow-execute", "--", sys.executable, "-c", "print('diagnostic row\\n'*5000)"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["exit"], 0)
        compact = subprocess.run(cli+["show"],capture_output=True,text=True)
        full = subprocess.run(cli+["--full", "show"],capture_output=True,text=True)
        data = json.loads(full.stdout)
        self.assertEqual(data["tasks"]["T1"]["evidence"]["stdout"].count("diagnostic row"), 5000)
        self.assertLess(len(compact.stdout), len(full.stdout)/10)
        self.assertNotIn("diagnostic row", compact.stdout)
        self.assertEqual(s.read()["tasks"]["T1"]["status"], "built")

    def test_compact_failed_check_preserves_true_exit_and_report(self):
        s = self.running_assignment()
        cli = [sys.executable, str(SCRIPTS / "state.py"), "--root", str(self.root), "--state-dir", ".make-feature/a", "check", "T1", "T1-attempt-1", "--coverage", '{"C1":["SYNTHETIC failure fixture"]}', "--allow-execute", "--", sys.executable, "-c", "import sys; print('specific failure',file=sys.stderr); raise SystemExit(7)"]
        result = subprocess.run(cli,capture_output=True,text=True)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)["exit"], 7)
        self.assertIn("specific failure",json.loads(result.stdout)["error_tail"])
        self.assertEqual(s.read()["tasks"]["T1"]["evidence"]["exit"],7)
        self.assertEqual(s.read()["tasks"]["T1"]["status"],"blocked")

    def test_long_argv_is_only_previewed_but_preserved_in_receipt(self):
        s = self.running_assignment()
        source = "#" + "x" * 40000 + "\nprint('actual result')"
        cli = [sys.executable,str(SCRIPTS/"state.py"),"--root",str(self.root),"--state-dir",".make-feature/a","check","T1","T1-attempt-1","--coverage",'{"C1":["SYNTHETIC argv size fixture"]}',"--allow-execute","--",sys.executable,"-c",source]
        result = subprocess.run(cli,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertLess(len(result.stdout),8000)
        self.assertEqual(s.read()["tasks"]["T1"]["evidence"]["argv"][-1],source)
        self.assertIn("actual result",s.read()["tasks"]["T1"]["evidence"]["stdout"])

    def test_symlink_retarget_invalidates_same_bytes_and_mode(self):
        a, b = self.root / "a", self.root / "b"
        a.mkdir(); b.mkdir()
        source = "from pathlib import Path\nprint((Path(__file__).resolve().parent/'value.txt').read_text())\n"
        for folder, value in ((a, "good"), (b, "bad")):
            (folder / "app.py").write_text(source)
            (folder / "value.txt").write_text(value)
        link = self.root / "app.py"
        link.symlink_to(a / "app.py")
        s = ledger.Store(self.root)
        s.apply({"op": "init", "budget": 3, "permissions": ["local_write", "test"]})
        s.apply({"op": "spec", "revision": 1, "approval": "SYNTHETIC test fixture", "criteria": {"C1": "reads correct data"}, "tasks": [{"id": "T1", "criteria": ["C1"], "deps": [], "files": ["app.py", "a/value.txt", "b/value.txt"]}]})
        s.apply({"op": "claim", "task": "T1", "owner": "worker"})
        result = s.check("T1", "worker", [sys.executable, "app.py"], {"C1": ["fixture"]}, allow_execute=True)
        self.assertIn("good", result["stdout"])
        (self.root / "review.md").write_text("SYNTHETIC test fixture review")
        s.apply({"op": "review", "task": "T1", "reviewer": "reviewer", "provenance": "SYNTHETIC fixture", "report": "review.md", "spec": "pass", "quality": "pass"})
        self.assertTrue(s.audit()["complete"])
        link.unlink(); link.symlink_to(b / "app.py")
        actual = subprocess.run([sys.executable, "app.py"], cwd=self.root, capture_output=True, text=True)
        self.assertIn("bad", actual.stdout)
        self.assertFalse(s.audit()["complete"])

    def running_assignment(self):
        (self.root / "app.py").write_text("print('ok')")
        s = ledger.Store(self.root, ".make-feature/a")
        s.apply({"op": "init", "budget": 3, "permissions": ["local_write", "test"]})
        s.apply({"op": "spec", "revision": 1, "approval": "SYNTHETIC fixture", "criteria": {"C1": "works"}, "tasks": [{"id": "T1", "criteria": ["C1"], "deps": [], "files": ["app.py"]}]})
        s.apply({"op": "claim", "task": "T1", "owner": "T1-attempt-1"})
        return s

    def test_dispatch_binding_prevents_actual_worker_self_review(self):
        s = self.running_assignment()
        s.apply({"op": "bind", "task": "T1", "owner": "T1-attempt-1", "worker": "actual-worker-session", "provenance": "SYNTHETIC dispatch fixture"})
        s.check("T1", "T1-attempt-1", [sys.executable, "app.py"], {"C1": ["fixture"]}, allow_execute=True)
        (self.root / "review.md").write_text("SYNTHETIC fixture")
        review = {"op": "review", "task": "T1", "reviewer": "actual-worker-session", "provenance": "SYNTHETIC fixture", "report": "review.md", "spec": "pass", "quality": "pass"}
        with self.assertRaises(ValueError):
            s.apply(review)
        s.apply(dict(review, reviewer="independent-session"))
        self.assertTrue(s.audit()["complete"])
        self.assertEqual(s.read()["tasks"]["T1"]["worker_id"], "actual-worker-session")

    def test_binding_rejects_wrong_owner_and_reassignment(self):
        s = self.running_assignment()
        event = {"op": "bind", "task": "T1", "owner": "wrong", "worker": "actual-worker", "provenance": "SYNTHETIC fixture"}
        with self.assertRaises(ValueError): s.apply(event)
        event["owner"] = "T1-attempt-1"
        s.apply(event)
        with self.assertRaises(ValueError): s.apply(dict(event, worker="other-worker"))
        s.apply({"op": "block", "task": "T1", "owner": "T1-attempt-1", "reason": "fixture retry"})
        s.apply({"op": "reconcile", "task": "T1", "reason": "new attempt required"})
        s.apply({"op": "claim", "task": "T1", "owner": "T1-attempt-2"})
        s.apply(dict(event, owner="T1-attempt-2", worker="other-worker"))
        self.assertEqual(s.read()["used"], 2)
        self.assertIn("actual-worker", s.read()["implementers"])

    def test_late_bind_after_recover_preserves_original_worker_and_lock(self):
        s = self.running_assignment()
        s.apply({"op": "recover", "reason": "SYNTHETIC crash after dispatch before bind"})
        s.apply({"op": "bind", "task": "T1", "owner": "T1-attempt-1", "worker": "first-worker", "provenance": "SYNTHETIC recovered dispatch receipt"})
        self.assertEqual(s.read()["tasks"]["T1"]["status"], "interrupted")
        with self.assertRaises(ValueError):
            s.apply({"op": "claim", "task": "T1", "owner": "T1-attempt-2"})
        s.apply({"op": "reconcile", "task": "T1", "reason": "original worker stopped; effects inspected"})
        s.apply({"op": "claim", "task": "T1", "owner": "T1-attempt-2"})
        s.apply({"op": "bind", "task": "T1", "owner": "T1-attempt-2", "worker": "second-worker", "provenance": "SYNTHETIC new dispatch receipt"})
        s.check("T1", "T1-attempt-2", [sys.executable, "app.py"], {"C1": ["fixture"]}, allow_execute=True)
        (self.root / "review.md").write_text("SYNTHETIC fixture")
        event = {"op": "review", "task": "T1", "reviewer": "first-worker", "provenance": "SYNTHETIC fixture", "report": "review.md", "spec": "pass", "quality": "pass"}
        with self.assertRaises(ValueError):
            s.apply(event)
        s.apply(dict(event, reviewer="independent-worker"))
        self.assertTrue(s.audit()["complete"])
        self.assertEqual(s.read()["used"], 2)


if __name__ == "__main__":
    unittest.main()
