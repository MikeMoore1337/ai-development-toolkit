"""Durable host ledger tests. No Codex or model processes are invoked."""
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / "scripts" / "codex_host_one_shot.py"
spec = importlib.util.spec_from_file_location("codex_host_one_shot", SCRIPT)
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)

contract_spec = importlib.util.spec_from_file_location(
    "codex_host_orchestration", BASE / "scripts" / "codex_host_orchestration.py")
contract = importlib.util.module_from_spec(contract_spec)
contract_spec.loader.exec_module(contract)


class OneShotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "private"
        self.root.mkdir(mode=0o700)

    def request(self, task="test-task", revision="v1", cost=True):
        return {
            "task_id": task, "locale": "ru", "current_model": "primary",
            "available_models": ["primary", "candidate"],
            "inventory_status": "VERIFIED", "inventory_revision": revision,
            "switching": "UNAVAILABLE", "delegation": "VERIFIED",
            "zero_incremental_cost_verified": cost, "signals": ["architecture"],
        }

    def data(self, task="test-task", revision="v1", cost=True):
        request = self.request(task, revision, cost)
        consent = {
            "task_id": task, "inventory_revision": revision,
            "mode": "RECOMMEND_WITH_CONFIRMATION",
            "approved_models": ["candidate"], "max_extra_calls": 1,
        }
        state = {
            "task_id": task, "inventory_revision": revision,
            "calls_used": 0, "revoked": False,
        }
        params = {
            "request": request, "consent": consent, "state": state,
            "client_snapshot": dict(request),
            "context": "synthetic task; PRIVATE CONTENT MUST NEVER BE STORED",
            "confirmed_for_this_call": True,
        }
        params["plan"] = contract.prepare(
            request, consent, "candidate", state,
            params["client_snapshot"], params["context"],
            confirmed_for_this_call=True,
        )
        return params

    def reserve(self, data):
        return ledger.claim(
            str(self.root), data["plan"], data["request"],
            data["consent"], data["state"], data["client_snapshot"],
            data["context"],
            confirmed_for_this_call=data["confirmed_for_this_call"],
        )

    def test_successful_claim_is_durable_and_redacts_input(self):
        data = self.data()
        result = self.reserve(data)
        self.assertEqual(result["status"], "HOST_ONE_SHOT_RESERVED")
        self.assertEqual(result["native_calls_executed"], 0)
        self.assertEqual(result["host_billing_provenance"], "NOT_ATTESTED")
        self.assertEqual(result["backend_model"], "UNKNOWN")
        self.assertEqual(1, len(list(self.root.iterdir())))
        file = list(self.root.iterdir())[0]
        self.assertTrue(file.name.endswith(".claim.json"))
        self.assertNotIn(data["context"], file.read_text())
        self.assertNotIn("candidate", file.read_text())
        self.assertNotIn("test-task", file.read_text())
        self.assertEqual(ledger.inspect(str(self.root), "test-task")["attempts_reserved"], 1)
        if os.name != "nt":
            self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)

    def test_second_claim_always_refused_even_on_new_revision(self):
        self.reserve(self.data())
        for data in (self.data(), self.data(revision="v2")):
            with self.subTest(revision=data["request"]["inventory_revision"]):
                with self.assertRaisesRegex(ledger.LeaseDenied, "TASK_ALREADY_RESERVED"):
                    self.reserve(data)
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_revocation_and_stale_snapshot_refuse_before_reservation(self):
        for field in ("revoked", "snapshot", "consent", "confirmation"):
            params = self.data()
            if field == "revoked":
                params["state"]["revoked"] = True
            elif field == "snapshot":
                params["client_snapshot"]["inventory_revision"] = "stale"
            elif field == "consent":
                params["consent"]["approved_models"] = ["unapproved"]
            else:
                params["confirmed_for_this_call"] = False
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.reserve(params)
            self.assertEqual(list(self.root.iterdir()), [])

    def test_cost_unknown_refuses_before_reservation(self):
        params = self.data()
        params["request"]["zero_incremental_cost_verified"] = False
        params["client_snapshot"]["zero_incremental_cost_verified"] = False
        with self.assertRaisesRegex(ValueError, "ZERO_INCREMENTAL_COST_NOT_VERIFIED"):
            self.reserve(params)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_forged_plan_fingerprint_or_context_refuse(self):
        params = self.data()
        params["plan"]["native_spawn_arguments"]["model"] = "attacker"
        with self.assertRaisesRegex(ledger.LeaseDenied, "PLAN_DOES_NOT_MATCH_CURRENT_PREFLIGHT"):
            self.reserve(params)
        self.assertEqual(list(self.root.iterdir()), [])
        params = self.data()
        params["context"] += " mutated after preflight"
        with self.assertRaisesRegex(ledger.LeaseDenied, "PLAN_DOES_NOT_MATCH_CURRENT_PREFLIGHT"):
            self.reserve(params)
        self.assertEqual(list(self.root.iterdir()), [])

    def test_missing_or_public_root_refuses(self):
        params = self.data()
        with self.assertRaisesRegex(ledger.LeaseDenied, "LEDGER_ROOT_NOT_PREPARED"):
            ledger.claim(str(self.root / "missing"), params["plan"],
                         params["request"], params["consent"], params["state"],
                         params["client_snapshot"], params["context"],
                         confirmed_for_this_call=True)
        if os.name != "nt":
            self.root.chmod(0o755)
            with self.assertRaisesRegex(ledger.LeaseDenied, "LEDGER_DIRECTORY_NOT_PRIVATE"):
                self.reserve(params)
            self.root.chmod(0o700)

    def test_symlink_root_rejected(self):
        link = Path(self.temp.name) / "link"
        try:
            link.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Host does not permit test symlinks")
        data = self.data()
        with self.assertRaisesRegex(ledger.LeaseDenied, "LINKED_LEDGER_ROOT_REFUSED"):
            ledger.claim(str(link), data["plan"], data["request"], data["consent"],
                         data["state"], data["client_snapshot"], data["context"],
                         confirmed_for_this_call=True)

    def test_partial_or_corrupt_existing_reservation_fails_closed(self):
        data = self.data()
        target = self.root / (ledger._key("test-task") + ".claim.json")
        target.write_bytes(b"{partial reservation")
        with self.assertRaisesRegex(ledger.LeaseDenied, "TASK_ALREADY_RESERVED"):
            self.reserve(data)
        with self.assertRaisesRegex(ledger.LeaseDenied, "LEDGER_RECORD_NOT_READABLE"):
            ledger.inspect(str(self.root), "test-task")

    def test_eight_concurrent_claims_exactly_one_wins(self):
        params = self.data()
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(self.reserve, params) for _ in range(8)]
        good = 0
        rejected = 0
        for future in futures:
            try:
                receipt = future.result()
                self.assertEqual(receipt["attempts_reserved"], 1)
                good += 1
            except ledger.LeaseDenied as exc:
                self.assertIn("TASK_ALREADY_RESERVED", str(exc))
                rejected += 1
        self.assertEqual((good, rejected), (1, 7))
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_multiple_processes_exactly_one_wins(self):
        data = self.data()
        payload = json.dumps(data, ensure_ascii=False).encode()
        children = [
            subprocess.Popen([sys.executable, str(SCRIPT), "claim",
                              "--root", str(self.root)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
            for _ in range(4)
        ]
        results = [child.communicate(input=payload, timeout=10) for child in children]
        statuses = [json.loads(out)["status"] for out, err in results]
        self.assertEqual(statuses.count("HOST_ONE_SHOT_RESERVED"), 1)
        self.assertEqual(statuses.count("REFUSED"), 3)
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def completed(self):
        return {"status": {"01a1736e-e9f8-7132-82a7-23fc02ae6223":
                           {"completed": "MODEL IS NOT ATTESTED"}},
                "timed_out": False}

    def test_record_once_after_claim_excludes_native_result_text(self):
        params = self.data()
        self.reserve(params)
        agent = {"agent_id": "01a1736e-e9f8-7132-82a7-23fc02ae6223"}
        result = ledger.record_outcome(str(self.root), params["plan"],
                                       agent, self.completed())
        self.assertEqual(result["review_status"], "HOST_COMPLETED_MODEL_UNVERIFIED")
        self.assertEqual(result["cost_incurred"], "UNKNOWN")
        self.assertFalse(result["repeat_allowed"])
        output = (self.root / (ledger._key("test-task") + ".outcome.json")).read_text()
        self.assertNotIn("MODEL IS NOT ATTESTED", output)
        self.assertEqual(len(list(self.root.iterdir())), 2)
        with self.assertRaisesRegex(ledger.LeaseDenied, "TASK_ALREADY_RESERVED"):
            ledger.record_outcome(str(self.root), params["plan"], agent, self.completed())
        with self.assertRaisesRegex(ledger.LeaseDenied, "TASK_ALREADY_RESERVED"):
            self.reserve(params)

    def test_cannot_record_without_claim_or_with_different_preflight(self):
        params = self.data()
        agent = {"agent_id": "01a1736e-e9f8-7132-82a7-23fc02ae6223"}
        with self.assertRaisesRegex(ledger.LeaseDenied, "LEDGER_RECORD_NOT_READABLE"):
            ledger.record_outcome(str(self.root), params["plan"], agent, self.completed())
        self.reserve(params)
        forged = dict(params["plan"], plan_fingerprint="0"*64)
        with self.assertRaises(ValueError):
            ledger.record_outcome(str(self.root), forged, agent, self.completed())
        other = self.data(revision="v2")
        with self.assertRaisesRegex(ledger.LeaseDenied, "OUTCOME_NOT_BOUND_TO_RESERVED_PLAN"):
            ledger.record_outcome(str(self.root), other["plan"], agent, self.completed())
        self.assertEqual(len(list(self.root.iterdir())), 1)

    def test_error_response_can_be_recorded_but_never_resumed(self):
        params = self.data()
        self.reserve(params)
        agent = {"agent_id": "01a1736e-e9f8-7132-82a7-23fc02ae6223"}
        bad = {"status": {agent["agent_id"]: {"errored": "synthetic"}},
               "timed_out": False}
        record = ledger.record_outcome(str(self.root), params["plan"], agent, bad)
        self.assertEqual(record["review_status"], "HOST_RESULT_NOT_CONFIRMED")
        with self.assertRaises(ledger.LeaseDenied):
            self.reserve(params)

    def test_cli_read_only_inspect_reports_no_model_attestation(self):
        data = self.data()
        self.reserve(data)
        output = subprocess.run([sys.executable, str(SCRIPT), "inspect",
                                 "--root", str(self.root), "--task-id", "test-task"],
                                capture_output=True, timeout=5, check=True)
        report = json.loads(output.stdout)
        self.assertEqual(report["host_cost_attestation"], "NOT_OBSERVED_BY_LEDGER")
        self.assertEqual(report["attempts_reserved"], 1)


if __name__ == "__main__":
    unittest.main()
