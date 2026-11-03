"""Offline Codex V2 host delegation tests. No native tools or models are invoked."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contract = load("codex_host_orchestration")
ledger = load("codex_host_one_shot")


class CodexV2Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.private = Path(self.temp.name).resolve() / "claims"
        self.private.mkdir(mode=0o700)
        self.req = {
            "task_id": "v2 task with private title",
            "locale": "ru",
            "current_model": "main",
            "available_models": ["main", "other"],
            "inventory_status": "VERIFIED",
            "inventory_revision": "live-1",
            "switching": "UNAVAILABLE",
            "delegation": "VERIFIED",
            "zero_incremental_cost_verified": True,
            "signals": ["architecture"],
        }
        self.consent = {
            "task_id": self.req["task_id"],
            "inventory_revision": "live-1",
            "mode": "AUTO_OPT_IN",
            "approved_models": ["other"],
            "max_extra_calls": 1,
        }
        self.state = {
            "task_id": self.req["task_id"],
            "inventory_revision": "live-1",
            "calls_used": 0,
            "revoked": False,
        }
        self.snapshot = {**self.req, "native_runtime": "V2",
                         "native_model_override": "VERIFIED"}
        self.context = "Review SQL locking without editing the workspace"

    def plan(self):
        return contract.prepare(self.req, self.consent, "other", self.state,
                                self.snapshot, self.context,
                                confirmed_for_this_call=False, native_runtime="V2")

    def complete(self, plan, status=None):
        return {"agents": [{"agent_name": plan["native_spawn_arguments"]["task_name"],
                            "agent_status": status if status is not None else
                            {"completed": "Found an independent race condition"}}]}

    def test_preflight_v2_uses_actual_native_schema_and_opaque_task_name(self):
        p = self.plan()
        self.assertEqual(p["schema_version"], 2)
        self.assertEqual(p["native_runtime"], "V2")
        self.assertEqual(p["native_spawn_tool"], "spawn_agent")
        self.assertEqual(p["native_wait_tool"], "list_agents")
        self.assertEqual(p["native_wait_timeout_ms"], 300000)
        self.assertEqual(set(p["native_spawn_arguments"]),
                         {"task_name", "model", "message", "fork_turns"})
        self.assertEqual(p["native_spawn_arguments"]["fork_turns"], "none")
        self.assertEqual(p["native_spawn_arguments"]["model"], "other")
        self.assertNotIn(self.req["task_id"], p["native_spawn_arguments"]["task_name"])
        self.assertEqual(p["status"], "PREFLIGHT_ONLY_NOT_EXECUTED")

    def test_completion_still_does_not_attest_backend_model(self):
        p = self.plan()
        ref = p["native_spawn_arguments"]["task_name"]
        for returned in (ref, "/root/" + ref):
            agents = {"agents": [{"agent_name": returned,
                                  "agent_status": {"completed": "Synthetic review"}}]}
            result = contract.review(p, {"task_name": returned}, agents,
                                     host_claimed_one_shot_lease=True)
            self.assertEqual(result["status"], "HOST_COMPLETED_MODEL_UNVERIFIED")
            self.assertEqual(result["native_reference_kind"], "TASK_NAME")
            self.assertEqual(result["observed_model"], "UNKNOWN")
            self.assertEqual(result["backend_model_attestation"], "NOT_VERIFIED")

    def test_nested_canonical_task_ref_is_accepted_without_cross_tree_alias(self):
        p = self.plan()
        ref = p["native_spawn_arguments"]["task_name"]
        canonical = "/root/security_review/" + ref
        actual = {"agents": [{"agent_name": canonical,
                              "agent_status": {"completed": "Done"}}]}
        result = contract.review(p, {"task_name": canonical}, actual)
        self.assertEqual(result["status"], "HOST_COMPLETED_MODEL_UNVERIFIED")
        unrelated = {"agents": [{"agent_name": "/root/other/" + ref,
                                 "agent_status": {"completed": "Unrelated"}}]}
        report = contract.review(p, {"task_name": canonical}, unrelated)
        self.assertEqual(report["status"], "HOST_RESULT_NOT_CONFIRMED")
        for forged in ("/root/../" + ref, "/different_parent/" + ref,
                       "/root//" + ref):
            with self.subTest(forged=forged), self.assertRaises(ValueError):
                contract.review(p, {"task_name": forged}, actual)

    def test_missing_proof_and_unknown_runtime_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_NATIVE_RUNTIME"):
            contract.prepare(self.req, self.consent, "other", self.state,
                             self.snapshot, self.context,
                             confirmed_for_this_call=False, native_runtime="V3")
        for snapshot in (self.req, {**self.snapshot, "native_model_override": "UNKNOWN"},
                         {**self.snapshot, "inventory_revision": "stale"}):
            with self.subTest(snapshot=snapshot), self.assertRaises(ValueError):
                contract.prepare(self.req, self.consent, "other", self.state,
                                 snapshot, self.context,
                                 confirmed_for_this_call=False, native_runtime="V2")
        for consent, state, req in [
            ({**self.consent, "approved_models": ["unapproved"]}, self.state, self.req),
            (self.consent, {**self.state, "revoked": True}, self.req),
            (self.consent, self.state, {**self.req, "zero_incremental_cost_verified": False}),
        ]:
            with self.assertRaises(ValueError):
                contract.prepare(req, consent, "other", state,
                                 {**self.snapshot, "zero_incremental_cost_verified":
                                  req["zero_incremental_cost_verified"]},
                                 self.context, confirmed_for_this_call=False,
                                 native_runtime="V2")

    def test_invalid_and_unrelated_v2_receipts_never_report_success(self):
        p = self.plan()
        ref = p["native_spawn_arguments"]["task_name"]
        for spawn, agents in [
            ({"agent_id": "fake"}, self.complete(p)),
            ({"task_name": "wrong"}, self.complete(p)),
            ({"task_name": ref, "observed_model": "other"}, self.complete(p)),
            ({"task_name": ref}, {"status": {ref: {"completed": "bad"}}}),
            ({"task_name": ref}, {"agents": [
                {"agent_name": ref, "agent_status": {"completed": "ok"}},
                {"agent_name": ref, "agent_status": {"completed": "ok"}}]}),
        ]:
            with self.subTest(spawn=spawn, agents=agents), self.assertRaises(ValueError):
                contract.review(p, spawn, agents)
        for status in ({"errored": "failure"}, "running",
                       {"completed": None}, {"completed": " "}):
            with self.subTest(status=status):
                result = contract.review(p, {"task_name": ref}, self.complete(p, status))
                self.assertEqual(result["status"], "HOST_RESULT_NOT_CONFIRMED")
        missing = contract.review(p, {"task_name": ref}, {"agents": []})
        self.assertEqual(missing["status"], "HOST_RESULT_NOT_CONFIRMED")

    def test_ledger_init_is_explicit_idempotent_and_rejects_links(self):
        nested = self.private / "fresh"
        first = ledger.init(str(nested))
        second = ledger.init(str(nested))
        self.assertEqual(first["status"], "LEDGER_READY")
        self.assertEqual(first["action"], "CREATED")
        self.assertEqual(second["action"], "ALREADY_EXISTS")
        self.assertEqual(list(nested.iterdir()), [])
        with self.assertRaises(ValueError):
            ledger.init("relative/path")
        with self.assertRaises(ValueError):
            ledger.init(str(self.private / "not-created" / "deep"))

    def test_one_shot_claim_and_record_are_consumed_without_retries(self):
        p = self.plan()
        params = [str(self.private), p, self.req, self.consent, self.state,
                  self.snapshot, self.context]
        receipt = ledger.claim(*params, confirmed_for_this_call=False)
        self.assertEqual(receipt["status"], "HOST_ONE_SHOT_RESERVED")
        with self.assertRaisesRegex(ValueError, "TASK_ALREADY_RESERVED"):
            ledger.claim(*params, confirmed_for_this_call=False)
        outcome = ledger.record_outcome(str(self.private), p,
                                       {"task_name": p["native_spawn_arguments"]["task_name"]},
                                       self.complete(p))
        self.assertIn("native_task_name", outcome)
        self.assertNotIn("native_agent_id", outcome)
        self.assertEqual(outcome["repeat_allowed"], False)
        with self.assertRaisesRegex(ValueError, "TASK_ALREADY_RESERVED"):
            ledger.record_outcome(str(self.private), p,
                                  {"task_name": p["native_spawn_arguments"]["task_name"]},
                                  self.complete(p))
        joined = "\n".join(f.read_text() for f in self.private.iterdir())
        self.assertNotIn(self.context, joined)
        self.assertNotIn(self.req["task_id"], joined)
        self.assertNotIn("other", joined)

    def test_toolkit_mcp_v2_prepare_review_are_read_only(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        self.addCleanup(sys.path.remove, str(ROOT / "scripts"))
        import toolkit_mcp
        prepare_schema = next(t for t in toolkit_mcp._tool_defs()
                              if t["name"] == "toolkit_codex_prepare_delegation")
        self.assertEqual(prepare_schema["inputSchema"]["properties"]["native_runtime"]["enum"],
                         ["V1", "V2"])
        self.assertTrue(prepare_schema["annotations"]["readOnlyHint"])
        a = toolkit_mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                                "params": {"name": "toolkit_codex_prepare_delegation",
                                           "arguments": {
                                               "request": self.req, "consent": self.consent,
                                               "state": self.state, "target_model": "other",
                                               "client_snapshot": self.snapshot,
                                               "context": self.context,
                                               "confirmed_for_this_call": False,
                                               "native_runtime": "V2"}}})
        self.assertFalse(a["result"].get("isError", False), a)
        p = a["result"]["structuredContent"]
        b = toolkit_mcp.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                                "params": {"name": "toolkit_codex_review_delegation",
                                           "arguments": {
                                               "plan": p,
                                               "spawn_response": {"task_name":
                                                   p["native_spawn_arguments"]["task_name"]},
                                               "wait_response": self.complete(p)}}})
        self.assertFalse(b["result"].get("isError", False), b)
        self.assertEqual(b["result"]["structuredContent"]["status"],
                         "HOST_COMPLETED_MODEL_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
