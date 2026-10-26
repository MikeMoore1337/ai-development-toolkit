"""Personal MCP 0.1.12 routes only read-only Codex #357 contracts.

All native tool data here are synthetic. No Codex agents, APIs, local project
writes, or spend. The dedicated Toolkit checkout must match SHA256SUMS.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "mcp"))
from adt_mcp import Toolkit, TOOLS, dispatch, process, VERSION  # noqa: E402

AGENT_ID = "01a1736e-e9f8-7132-82a7-23fc02ae6223"


class PersonalCodexOrchestrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tk = Toolkit(ROOT)

    def req(self):
        return dict(task_id="personal-test", locale="ru",
                    current_model="actual-client-primary",
                    available_models=["actual-client-primary", "declared-expert"],
                    inventory_status="VERIFIED", inventory_revision="v1",
                    switching="UNAVAILABLE", delegation="VERIFIED",
                    zero_incremental_cost_verified=True, signals=["architecture"])

    def consent(self):
        return dict(task_id="personal-test", inventory_revision="v1",
                    mode="RECOMMEND_WITH_CONFIRMATION",
                    approved_models=["declared-expert"], max_extra_calls=1)

    def state(self):
        return dict(task_id="personal-test", inventory_revision="v1",
                    calls_used=0, revoked=False)

    def args(self):
        req = self.req()
        return dict(request=req, consent=self.consent(),
                    target_model="declared-expert", state=self.state(),
                    client_snapshot=dict(req), context="Synthetic SQL question",
                    confirmed_for_this_call=True)

    def call(self, name, args):
        result = process(self.tk, {"jsonrpc": "2.0", "id": 73,
                                   "method": "tools/call",
                                   "params": {"name": name, "arguments": args}})
        self.assertEqual(result["id"], 73)
        return result

    def test_version_and_tools_registered_read_only(self):
        self.assertEqual(VERSION, "0.1.12")
        tools = {tool["name"]: tool for tool in TOOLS}
        for name in ("toolkit_codex_prepare_delegation",
                     "toolkit_codex_review_delegation"):
            self.assertIn(name, tools)
            self.assertTrue(tools[name]["annotations"]["readOnlyHint"])
            self.assertFalse(tools[name]["annotations"]["destructiveHint"])
        self.assertEqual(self.tk.info()["mcp_server_version"], "0.1.12")

    def test_prepare_denied_without_zero_cost_verified(self):
        args = self.args()
        args["request"]["zero_incremental_cost_verified"] = False
        args["client_snapshot"]["zero_incremental_cost_verified"] = False
        outcome = self.call("toolkit_codex_prepare_delegation", args)
        self.assertTrue(outcome["result"].get("isError", False))
        self.assertIn("ZERO_INCREMENTAL_COST_NOT_VERIFIED",
                      outcome["result"]["content"][0]["text"])

    def test_prepare_uses_real_source_contract_without_native_execution(self):
        response = self.call("toolkit_codex_prepare_delegation", self.args())
        self.assertFalse(response["result"].get("isError", False), response)
        plan = response["result"]["structuredContent"]
        self.assertEqual(plan["status"], "PREFLIGHT_ONLY_NOT_EXECUTED")
        self.assertEqual(plan["observed_model"], "UNKNOWN")
        self.assertFalse(plan["host_executed"])
        self.assertFalse(plan["host_lease_observed"])
        self.assertEqual(plan["native_spawn_arguments"],
                         {"model": "declared-expert",
                          "message": "Synthetic SQL question",
                          "fork_context": False})
        self.assertEqual(plan["native_wait_tool"], "multi_agent_v1__wait_agent")

    def test_review_native_wait_shape_and_unknown_backend_model(self):
        plan = dispatch(self.tk, "toolkit_codex_prepare_delegation", self.args())
        args = dict(plan=plan, spawn_response={"agent_id": AGENT_ID, "nickname": "Synthetic"},
                    wait_response={"status": {AGENT_ID: {"completed": "SQL answer"}},
                                   "timed_out": False})
        response = self.call("toolkit_codex_review_delegation", args)
        self.assertFalse(response["result"].get("isError", False), response)
        result = response["result"]["structuredContent"]
        self.assertEqual(result["status"], "HOST_COMPLETED_MODEL_UNVERIFIED")
        self.assertEqual(result["observed_model"], "UNKNOWN")
        self.assertEqual(result["host_lease_evidence"], "NOT_OBSERVED")

    def test_invalid_consent_and_native_response_fail_closed(self):
        args = self.args()
        args["consent"] = {**self.consent(), "inventory_revision": "different"}
        result = self.call("toolkit_codex_prepare_delegation", args)
        self.assertTrue(result["result"].get("isError", False))
        plan = dispatch(self.tk, "toolkit_codex_prepare_delegation", self.args())
        bad = dict(plan=plan, spawn_response={"agent_id": AGENT_ID},
                   wait_response={"status": {"other": {"completed": "spoof"}},
                                  "timed_out": False})
        outcome = self.call("toolkit_codex_review_delegation", bad)
        self.assertTrue(outcome["result"].get("isError", False))
        self.assertIn("MISMATCHED_WAIT_TARGET",
                      outcome["result"]["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
