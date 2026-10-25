"""Offline policy tests; no actual client, agent or paid API calls."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "adaptive_execution_advisor.py"
spec = importlib.util.spec_from_file_location("advisor", SOURCE)
advisor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(advisor)

class AdvisorTests(unittest.TestCase):
    def req(self):
        return dict(task_id="task-1", locale="ru", current_model="primary",
                    available_models=["primary", "expert"], inventory_status="VERIFIED",
                    inventory_revision="v1", switching="VERIFIED", delegation="UNKNOWN",
                    zero_incremental_cost_verified=True, signals=["architecture"])

    def consent(self, mode="AUTO_OPT_IN"):
        return dict(task_id="task-1", inventory_revision="v1", mode=mode,
                    approved_models=["expert"], max_extra_calls=2)

    def test_all_modes_explain_benefits_and_risks_without_executing(self):
        outcome = advisor.advise(self.req())
        self.assertTrue(outcome["user_selection_required"])
        self.assertIsNone(outcome["selected_mode"])
        self.assertEqual("NOT_RUN", outcome["execution"])
        self.assertEqual(0, outcome["extra_model_calls"])
        self.assertEqual("RECOMMEND_WITH_CONFIRMATION", outcome["recommended_mode"])
        self.assertEqual(["expert"], outcome["candidate_models"])
        self.assertEqual(3, len(outcome["options"]))
        for item in outcome["options"]:
            self.assertTrue(item["benefit"] and item["risk"])

    def test_one_model_only(self):
        req = self.req()
        req["available_models"] = ["primary"]
        d = advisor.advise(req)
        self.assertEqual("SINGLE_MODEL", d["recommended_mode"])
        self.assertEqual([True, False, False], [o["enabled"] for o in d["options"]])

    def test_unknown_inventory_cannot_authorize_other_model(self):
        for status in ("UNKNOWN", "UNAVAILABLE"):
            req = self.req()
            req.update(inventory_status=status, switching="UNAVAILABLE")
            self.assertEqual([True, False, False], [o["enabled"] for o in advisor.advise(req)["options"]])
            with self.assertRaises(advisor.AdvisorError):
                advisor.authorize(req, self.consent())

    def test_unsupported_or_cost_unknown_blocks_automatic_switch(self):
        req = self.req()
        req.update(switching="UNKNOWN", zero_incremental_cost_verified=False)
        self.assertFalse(advisor.advise(req)["options"][2]["enabled"])
        with self.assertRaises(advisor.AdvisorError):
            advisor.authorize(req, self.consent())
        self.assertFalse(advisor.authorize(req, self.consent("RECOMMEND_WITH_CONFIRMATION"))["extra_calls_authorized"])

    def test_auto_is_bounded_but_never_executes_in_advisor(self):
        result = advisor.authorize(self.req(), self.consent())
        self.assertEqual(["expert"], result["approved_models"])
        self.assertEqual(2, result["max_extra_calls"])
        self.assertTrue(result["extra_calls_authorized"])
        self.assertEqual("NOT_RUN", result["execution"])

    def test_single_model_requires_explicit_consent(self):
        choice = self.consent("SINGLE_MODEL")
        choice.update(approved_models=[], max_extra_calls=0)
        self.assertFalse(advisor.authorize(self.req(), choice)["extra_calls_authorized"])
        with self.assertRaises(advisor.AdvisorError):
            advisor.authorize(self.req(), None)

    def test_cross_task_stale_and_excluded_models_rejected(self):
        base = self.consent()
        cases = [
            {**base, "task_id": "another-task"},
            {**base, "inventory_revision": "old"},
            {**base, "approved_models": ["missing"]},
            {**base, "approved_models": ["primary"]},
            {**base, "approved_models": ["expert", "expert"]},
            {**base, "approved_models": []},
            {**base, "max_extra_calls": True},
            {**base, "max_extra_calls": 11},
        ]
        for consent in cases:
            with self.subTest(consent=consent), self.assertRaises(advisor.AdvisorError):
                advisor.authorize(self.req(), consent)

    def test_arbitrary_provider_ids_and_localizations(self):
        for locale in ("ru", "en"):
            req = self.req()
            req.update(locale=locale, current_model="any/a",
                       available_models=["any/a", "any/b"])
            d = advisor.advise(req)
            self.assertEqual(["any/b"], d["candidate_models"])
            self.assertTrue(d["options"][2]["enabled"])

    def test_invalid_data_fail_closed(self):
        invalid = [
            None, [], {**self.req(), "extra": 1},
            {**self.req(), "available_models": ["x", "x"]},
            {**self.req(), "signals": ["bad"]},
            {**self.req(), "signals": [42]},
            {**self.req(), "locale": []},
            {**self.req(), "switching": []},
            {**self.req(), "switching": "MAYBE"},
            {**self.req(), "zero_incremental_cost_verified": "true"},
        ]
        for req in invalid:
            with self.subTest(req=req), self.assertRaises(advisor.AdvisorError):
                advisor.advise(req)

    def test_cli_no_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            file = Path(temp) / "request.json"
            file.write_text(json.dumps(self.req()), encoding="utf-8")
            before = file.read_bytes()
            with subprocess.Popen([sys.executable, str(SOURCE), str(file)],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, encoding="utf-8") as process:
                stdout, stderr = process.communicate(timeout=10)
                self.assertEqual(0, process.returncode, stderr)
            self.assertEqual("NOT_RUN", json.loads(stdout)["execution"])
            self.assertEqual(before, file.read_bytes())
            self.assertEqual(["request.json"], [p.name for p in Path(temp).iterdir()])

if __name__ == "__main__":
    unittest.main()
