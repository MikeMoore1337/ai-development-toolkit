import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from budget import Budget
from workspace import initialize


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        req = self.root / "request.txt"
        req.write_text("SYNTHETIC fixture: add a feature")
        initialize(self.root, "example", req)
        self.budget = Budget(self.root, "example")

    def test_total_delegations_and_repairs_are_independent_and_durable(self):
        self.budget.initialize("quick")
        self.budget.reserve("delegation", "first")
        self.budget.reserve("repair", "repair-1")
        new = Budget(self.root, "example")
        new.reserve("delegation", "review-after-repair")
        with self.assertRaises(ValueError): new.reserve("delegation", "third")
        with self.assertRaises(ValueError): new.reserve("repair", "second-repair")
        status = new.summary(new.read())
        self.assertEqual(status["used"], {"delegation": 2, "repair": 1})
        self.assertIsNone(status["total_llm_tokens"])

    def test_resume_and_mode_change_cannot_reset_budget(self):
        self.budget.initialize("normal")
        self.budget.reserve("delegation", "attempt")
        before = self.budget.read()
        with self.assertRaises(ValueError): Budget(self.root, "example").initialize("deep")
        self.assertEqual(self.budget.read(), before)

    def test_duplicate_reservation_does_not_authorize_another_dispatch(self):
        self.budget.initialize("normal")
        self.budget.reserve("delegation", "unique")
        before = self.budget.read()
        for kind in ("delegation", "repair"):
            with self.assertRaises(ValueError): self.budget.reserve(kind, "unique")
        self.assertEqual(self.budget.read(), before)

    def test_expiry_refuses_new_calls_without_mutation(self):
        with patch("budget.time.time", return_value=100): self.budget.initialize("quick")
        before = self.budget.read()
        with patch("budget.time.time", return_value=701), self.assertRaises(ValueError):
            self.budget.reserve("delegation", "late")
        self.assertEqual(self.budget.read(), before)

    def test_concurrent_reservations_cannot_overdraw_last_slot(self):
        self.budget.initialize("quick", delegations=1)
        def reserve(key):
            try:
                Budget(self.root, "example").reserve("delegation", key)
                return True
            except ValueError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, ("one", "two")))
        self.assertEqual(sum(results), 1)
        self.assertEqual(self.budget.summary(self.budget.read())["remaining"]["delegation"], 0)

    def test_zero_allowance_and_invalid_limits(self):
        self.budget.initialize("quick", delegations=0, repairs=0, minutes=1)
        with self.assertRaises(ValueError): self.budget.reserve("delegation", "none")
        with self.assertRaises(ValueError): self.budget.reserve("repair", "none")
        for value in (-1, True, 1.5):
            with self.assertRaises(ValueError): self.budget.initialize("quick", delegations=value)

    def test_invalid_keys_and_uninitialized_status(self):
        with self.assertRaises(ValueError): self.budget.read()
        self.budget.initialize("quick")
        for kind,key in (("money", "x"), ("delegation", ""), ("repair", 2)):
            with self.assertRaises(ValueError): self.budget.reserve(kind,key)
        self.assertEqual(self.budget.summary(self.budget.read())["used"]["delegation"], 0)

    def test_context_and_budget_symlink_cannot_escape(self):
        with self.assertRaises(ValueError): Budget(self.root, "../outside")
        outside = self.root / "untouched.sqlite3"
        outside.write_bytes(b"preserve")
        self.budget.db.unlink()
        self.budget.db.symlink_to(outside)
        with self.assertRaises(ValueError): Budget(self.root, "example")
        self.assertEqual(outside.read_bytes(), b"preserve")

    def test_cli_rejection_keeps_used_count(self):
        self.budget.initialize("quick", delegations=0)
        command = [sys.executable, str(SCRIPTS/"budget.py"), "--project", str(self.root), "--slug", "example"]
        failed = subprocess.run(command + ["reserve", "--kind", "delegation", "--key", "extra"], capture_output=True,text=True)
        self.assertEqual(failed.returncode, 2)
        status = subprocess.run(command + ["status"],capture_output=True,text=True)
        self.assertEqual(status.returncode, 0)
        self.assertEqual(json.loads(status.stdout)["used"]["delegation"], 0)


if __name__ == "__main__":
    unittest.main()
