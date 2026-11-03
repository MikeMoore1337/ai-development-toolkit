"""Guarded owner-approved included-quota consultation tests; no provider calls."""
from __future__ import annotations

import importlib.util
import json
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
AGENT = "01a1736e-e9f8-7132-82a7-23fc02ae6223"


class IncludedOnlyManualConsultationTests(unittest.TestCase):
    def setUp(self):
        self.req = {
            "task_id": "one-off-user-approved-review",
            "locale": "ru", "current_model": "primary",
            "available_models": ["primary", "approved"],
            "inventory_status": "VERIFIED", "inventory_revision": "rev-2",
            "switching": "UNAVAILABLE", "delegation": "VERIFIED",
            "zero_incremental_cost_verified": False,
            "signals": ["security"],
        }
        self.consent = {
            "task_id": self.req["task_id"],
            "inventory_revision": "rev-2",
            "mode": "RECOMMEND_WITH_CONFIRMATION",
            "approved_models": ["approved"], "max_extra_calls": 1,
        }
        self.state = {
            "task_id": self.req["task_id"], "inventory_revision": "rev-2",
            "calls_used": 0, "revoked": False,
        }
        self.guard = {
            "task_id": self.req["task_id"],
            "inventory_revision": "rev-2",
            "requested_model": "approved",
            "route": "CODEX_CHATGPT_SUBSCRIPTION",
            "owner_confirmed_this_call": True,
            "paid_api_route_disabled": True,
            "credit_balance_zero_observed": True,
            "automatic_topup_disabled_observed": True,
            "included_allowance_remaining_observed": True,
            "unknown_per_call_usage_acknowledged": True,
        }
        self.context = "Review database locking, read-only"

    def plan(self, *, req=None, consent=None, guard=None, native_runtime="V1"):
        request = req if req is not None else self.req
        snapshot = dict(request)
        if native_runtime == "V2":
            snapshot.update(native_runtime="V2", native_model_override="VERIFIED")
        return contract.prepare(
            request, consent if consent is not None else self.consent,
            "approved", self.state, snapshot, self.context,
            confirmed_for_this_call=True, native_runtime=native_runtime,
            subscription_guard=guard if guard is not None else self.guard,
        )

    def test_unknown_cost_requires_explicit_owner_guard(self):
        with self.assertRaisesRegex(ValueError, "ZERO_INCREMENTAL_COST_NOT_VERIFIED"):
            contract.prepare(self.req, self.consent, "approved", self.state,
                             dict(self.req), self.context,
                             confirmed_for_this_call=True)
        for guard in ({}, {"route": "CODEX_CHATGPT_SUBSCRIPTION"}):
            with self.subTest(guard=guard), self.assertRaisesRegex(
                    ValueError, "OWNER_INCLUDED_QUOTA_GUARD_REQUIRED"):
                self.plan(guard=guard)

    def test_manual_owner_scope_never_converts_into_billing_proof(self):
        for runtime in ("V1", "V2"):
            p = self.plan(native_runtime=runtime)
            self.assertEqual(p["billing_attestation"],
                             "OWNER_DECLARED_INCLUDED_USAGE_NOT_ATTESTED")
            self.assertFalse(p["host_executed"])
            self.assertFalse(p["host_lease_observed"])
            self.assertEqual(p["observed_model"], "UNKNOWN")
            if runtime == "V1":
                spawn = {"agent_id": AGENT}
                waited = {"status": {AGENT: {"completed": "done"}}, "timed_out": False}
            else:
                name = p["native_spawn_arguments"]["task_name"]
                spawn = {"task_name": name}
                waited = {"agents": [{"agent_name": name,
                                       "agent_status": {"completed": "done"}}]}
            res = contract.review(p, spawn, waited)
            self.assertEqual(res["status"], "HOST_COMPLETED_MODEL_UNVERIFIED")
            self.assertEqual(res["backend_model_attestation"], "NOT_VERIFIED")

    def test_no_auto_or_single_or_unconfirmed_use_of_unknown_cost(self):
        for mode in ("AUTO_OPT_IN", "SINGLE_MODEL"):
            c = {**self.consent, "mode": mode}
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                self.plan(consent=c)
        with self.assertRaises(ValueError):
            contract.prepare(self.req, self.consent, "approved", self.state,
                             dict(self.req), self.context,
                             confirmed_for_this_call=False, subscription_guard=self.guard)

    def test_guard_safety_flags_stale_context_and_credit_spend_fail_closed(self):
        for key, invalid in [
            ("task_id", "other"), ("inventory_revision", "old"),
            ("requested_model", "unapproved"), ("route", "PAID_API"),
            ("credit_balance_zero_observed", False),
            ("automatic_topup_disabled_observed", False),
            ("included_allowance_remaining_observed", False),
            ("paid_api_route_disabled", False),
            ("owner_confirmed_this_call", False),
            ("unknown_per_call_usage_acknowledged", False),
            ("owner_confirmed_this_call", 1),
        ]:
            with self.subTest(key=key, invalid=invalid), self.assertRaises(ValueError):
                self.plan(guard={**self.guard, key: invalid})
        with self.assertRaises(ValueError):
            self.plan(guard={**self.guard, "unauthorized_extra": True})
        with self.assertRaises(ValueError):
            self.plan(req={**self.req, "zero_incremental_cost_verified": True})
        with self.assertRaises(ValueError):
            self.plan(consent={**self.consent, "max_extra_calls": 2})

    def test_durable_one_shot_cannot_be_reused_and_is_redacted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "private"
            root.mkdir(mode=0o700)
            p = self.plan()
            def reserve(guard):
                return ledger.claim(
                    str(root), p, self.req, self.consent, self.state,
                    dict(self.req), self.context, confirmed_for_this_call=True,
                    subscription_guard=guard,
                )
            for invalid in (None, {**self.guard, "credit_balance_zero_observed": False}):
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    reserve(invalid)
                self.assertEqual(list(root.iterdir()), [])
            first = reserve(self.guard)
            self.assertEqual(first["status"], "HOST_ONE_SHOT_RESERVED")
            self.assertEqual(first["host_billing_provenance"], "NOT_ATTESTED")
            with self.assertRaisesRegex(ValueError, "TASK_ALREADY_RESERVED"):
                reserve(self.guard)
            record = ledger.inspect(str(root), self.req["task_id"])
            self.assertEqual(record["host_cost_attestation"], "NOT_OBSERVED_BY_LEDGER")
            stored = "\n".join(x.read_text() for x in root.iterdir())
            self.assertNotIn(self.context, stored)
            self.assertNotIn("approved", stored)
            self.assertNotIn(self.req["task_id"], stored)

    def test_portable_mcp_exposes_read_only_scope(self):
        import sys
        scripts = str(ROOT / "scripts")
        sys.path.insert(0, scripts)
        self.addCleanup(sys.path.remove, scripts)
        import toolkit_mcp
        definition = next(x for x in toolkit_mcp._tool_defs()
                          if x["name"] == "toolkit_codex_prepare_delegation")
        self.assertTrue(definition["annotations"]["readOnlyHint"])
        self.assertIn("subscription_guard", definition["inputSchema"]["properties"])
        reply = toolkit_mcp.handle({
            "jsonrpc": "2.0", "id": 23, "method": "tools/call",
            "params": {"name": "toolkit_codex_prepare_delegation",
                       "arguments": {
                           "request": self.req, "consent": self.consent,
                           "target_model": "approved", "state": self.state,
                           "client_snapshot": dict(self.req),
                           "context": self.context,
                           "confirmed_for_this_call": True,
                           "subscription_guard": self.guard,
                       }},
        })
        self.assertFalse(reply["result"].get("isError", False), reply)
        self.assertEqual(reply["result"]["structuredContent"]["billing_attestation"],
                         "OWNER_DECLARED_INCLUDED_USAGE_NOT_ATTESTED")


if __name__ == "__main__":
    unittest.main()
