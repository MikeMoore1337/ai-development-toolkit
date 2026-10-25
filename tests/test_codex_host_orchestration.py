"""Offline Codex Desktop host orchestration tests: no agent/tool execution."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
AGENT_ID = "01a1736e-e9f8-7132-82a7-23fc02ae6223"
spec = importlib.util.spec_from_file_location(
    "codex_host_orchestration", ROOT / "scripts" / "codex_host_orchestration.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)


class HostOrchestrationTests(unittest.TestCase):
    def request(self):
        return dict(task_id="task", locale="ru", current_model="main",
                    available_models=["main", "gpt-6.1-sol"],
                    inventory_status="VERIFIED", inventory_revision="v1",
                    switching="UNAVAILABLE", delegation="VERIFIED",
                    zero_incremental_cost_verified=True, signals=["architecture"])

    def consent(self):
        return dict(task_id="task", inventory_revision="v1",
                    mode="RECOMMEND_WITH_CONFIRMATION",
                    approved_models=["gpt-6.1-sol"], max_extra_calls=1)

    def state(self):
        return dict(task_id="task", inventory_revision="v1",
                    calls_used=0, revoked=False)

    def plan(self):
        req = self.request()
        return contract.prepare(req, self.consent(), "gpt-6.1-sol",
                                self.state(), dict(req),
                                "Compare SQL concurrency options",
                                confirmed_for_this_call=True)

    def completed(self):
        return {"status": {AGENT_ID: {"completed": "SQL comparison"}},
                "timed_out": False}

    def test_preflight_is_read_only_unexecuted_and_exact_native_shape(self):
        plan = self.plan()
        self.assertEqual("PREFLIGHT_ONLY_NOT_EXECUTED", plan["status"])
        self.assertEqual("multi_agent_v1__spawn_agent", plan["native_spawn_tool"])
        self.assertEqual({"model": "gpt-6.1-sol",
                          "message": "Compare SQL concurrency options",
                          "fork_context": False},
                         plan["native_spawn_arguments"])
        self.assertEqual("multi_agent_v1__wait_agent", plan["native_wait_tool"])
        self.assertTrue(plan["host_atomic_lease_required"])
        self.assertFalse(plan["host_lease_observed"])
        self.assertFalse(plan["host_executed"])
        self.assertEqual("UNKNOWN", plan["observed_model"])

    def test_real_native_wait_shape_preserves_unknown_identity(self):
        record = contract.review(self.plan(), {"agent_id": AGENT_ID, "nickname": "Erdos"},
                                 self.completed(), host_claimed_one_shot_lease=True)
        self.assertEqual("HOST_COMPLETED_MODEL_UNVERIFIED", record["status"])
        self.assertEqual("UNKNOWN", record["observed_model"])
        self.assertEqual("NOT_VERIFIED", record["backend_model_attestation"])
        self.assertEqual("CLAIMED_NOT_ATTESTED", record["host_lease_evidence"])
        self.assertEqual("HOST_MUST_RECONCILE", record["extra_calls_used"])

    def test_no_extra_cost_proof_never_prepares(self):
        req = {**self.request(), "zero_incremental_cost_verified": False}
        with self.assertRaisesRegex(ValueError, "ZERO_INCREMENTAL_COST_NOT_VERIFIED"):
            contract.prepare(req, self.consent(), "gpt-6.1-sol",
                             self.state(), dict(req), "small",
                             confirmed_for_this_call=True)

    def test_no_consent_or_changed_snapshot_never_prepares(self):
        req = self.request()
        for consent, snapshot, confirmed in [
            (None, req, True),
            (self.consent(), req, False),
            (self.consent(), {**req, "inventory_revision": "v2"}, True),
            (self.consent(), {**req, "delegation": "UNKNOWN"}, True),
        ]:
            with self.subTest(consent=consent, snapshot=snapshot, confirmed=confirmed):
                with self.assertRaises(ValueError):
                    contract.prepare(req, consent, "gpt-6.1-sol",
                                     self.state(), snapshot, "small",
                                     confirmed_for_this_call=confirmed)

    def test_cap_and_revoked_state_never_prepares(self):
        for state in ({**self.state(), "calls_used": 1},
                      {**self.state(), "revoked": True},
                      {**self.state(), "inventory_revision": "v2"}):
            with self.subTest(state=state), self.assertRaises(ValueError):
                req = self.request()
                contract.prepare(req, self.consent(), "gpt-6.1-sol",
                                 state, dict(req), "tiny", confirmed_for_this_call=True)

    def test_native_pending_timeout_and_error_never_report_completion(self):
        entries = ["pending_init", "running", "interrupted", "shutdown",
                   "not_found", {"errored": "nope"}, {"completed": None},
                   {"completed": "  "}]
        for entry in entries:
            with self.subTest(entry=entry):
                result = contract.review(
                    self.plan(), {"agent_id": AGENT_ID},
                    {"status": {AGENT_ID: entry}, "timed_out": False})
                self.assertEqual("HOST_RESULT_NOT_CONFIRMED", result["status"])
        timed = contract.review(self.plan(), {"agent_id": AGENT_ID},
                                {"status": {AGENT_ID: {"completed": "ok"}},
                                 "timed_out": True})
        self.assertEqual("HOST_RESULT_NOT_CONFIRMED", timed["status"])

    def test_native_wait_target_mismatch_or_multiple_targets_rejected(self):
        for statuses in ({"other": {"completed": "ok"}},
                         {AGENT_ID: {"completed": "ok"}, "other": {"completed": "ok"}},
                         {}):
            with self.subTest(statuses=statuses), self.assertRaisesRegex(
                    ValueError, "MISMATCHED_WAIT_TARGET"):
                contract.review(self.plan(), {"agent_id": AGENT_ID},
                                {"status": statuses, "timed_out": False})

    def test_malformed_spawn_or_wait_payload_rejected(self):
        for spawn, wait in [
            ({"agent_id": "not-an-uuid"}, self.completed()),
            ({"agent_id": AGENT_ID, "model": "gpt-6.1-sol"}, self.completed()),
            ({"agent_id": AGENT_ID}, {"status": {AGENT_ID: "running"}}),
            ({"agent_id": AGENT_ID}, {"status": {AGENT_ID: {"completed": "ok"}},
                                      "timed_out": "false"}),
        ]:
            with self.subTest(spawn=spawn, wait=wait), self.assertRaises(ValueError):
                contract.review(self.plan(), spawn, wait)

    def test_plan_modification_and_forged_model_result_rejected(self):
        original = self.plan()
        for tamper in ({"requested_model": "forbidden"},
                       {"native_spawn_arguments": {"model": "forbidden",
                                                   "message": "bad", "fork_context": True}},
                       {"status": "ALREADY_EXECUTED"}):
            with self.subTest(tamper=tamper), self.assertRaises(ValueError):
                contract.review({**original, **tamper}, {"agent_id": AGENT_ID}, self.completed())
        # Text reporting a model is not attestation.
        result = contract.review(original, {"agent_id": AGENT_ID},
                                 {"status": {AGENT_ID: {"completed": "I used gpt-6.1-sol"}},
                                  "timed_out": False})
        self.assertEqual("UNKNOWN", result["observed_model"])

    def test_preview_is_not_lease_and_replay_not_prevented(self):
        a, b = self.plan(), self.plan()
        self.assertEqual(a, b)
        self.assertFalse(a["host_lease_observed"])
        self.assertFalse(a["host_executed"])
        result = contract.review(a, {"agent_id": AGENT_ID}, self.completed())
        self.assertEqual("NOT_OBSERVED", result["host_lease_evidence"])

    def test_mcp_exposes_read_only_prepare_review_without_agent_calls(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import toolkit_mcp
        names = {x["name"]: x for x in toolkit_mcp._tool_defs()}
        for name in ("toolkit_codex_prepare_delegation",
                     "toolkit_codex_review_delegation"):
            self.assertTrue(names[name]["annotations"]["readOnlyHint"])
        req = self.request()
        response = toolkit_mcp.handle({
            "jsonrpc": "2.0", "id": 7, "method": "tools/call",
            "params": {"name": "toolkit_codex_prepare_delegation",
                       "arguments": {
                           "request": req, "consent": self.consent(),
                           "target_model": "gpt-6.1-sol", "state": self.state(),
                           "client_snapshot": dict(req), "context": "small",
                           "confirmed_for_this_call": True}}})
        self.assertFalse(response["result"].get("isError", False), response)
        plan = response["result"]["structuredContent"]
        self.assertEqual("PREFLIGHT_ONLY_NOT_EXECUTED", plan["status"])
        response = toolkit_mcp.handle({
            "jsonrpc": "2.0", "id": 8, "method": "tools/call",
            "params": {"name": "toolkit_codex_review_delegation",
                       "arguments": {"plan": plan, "spawn_response": {"agent_id": AGENT_ID},
                                     "wait_response": self.completed()}}})
        self.assertFalse(response["result"].get("isError", False), response)
        self.assertEqual("HOST_COMPLETED_MODEL_UNVERIFIED",
                         response["result"]["structuredContent"]["status"])


if __name__ == "__main__":
    unittest.main()
