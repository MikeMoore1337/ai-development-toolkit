"""Synthetic host callbacks only; zero provider calls and no filesystem writes."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "scripts" / "model_switching_adapters.py"
spec = importlib.util.spec_from_file_location("adapter", source)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)

class AdapterTests(unittest.TestCase):
    def req(self):
        return dict(task_id="task", locale="ru", current_model="client/default",
                    available_models=["client/default", "client/expert"],
                    inventory_status="VERIFIED", inventory_revision="v1",
                    switching="UNKNOWN", delegation="VERIFIED",
                    zero_incremental_cost_verified=True, signals=["architecture"])

    def consent(self, mode="AUTO_OPT_IN"):
        return dict(task_id="task", inventory_revision="v1",
                    mode=mode, approved_models=["client/expert"], max_extra_calls=1)

    def state(self):
        return dict(task_id="task", inventory_revision="v1", calls_used=0, revoked=False)

    def harness(self, req=None, receipt=None):
        req = req or self.req()
        calls = []
        def invoke(model, context, method):
            calls.append((model, context, method))
            return receipt if receipt is not None else dict(
                execution="VERIFIED", observed_model=model)
        return calls, lambda: dict(req), invoke

    def test_automatic_delegation_uses_only_approved_model(self):
        req = self.req()
        calls, snap, invoke = self.harness(req)
        value = adapter.dispatch(req, self.consent(), "client/expert", self.state(),
                                 snapshot=snap, invoke=invoke, context="minimal")
        self.assertEqual([("client/expert", "minimal", "delegate")], calls)
        self.assertEqual("EXECUTED_VERIFIED_BY_HOST", value["status"])
        self.assertTrue(value["restored_to_primary"])
        self.assertEqual(1, value["next_state"]["calls_used"])
        self.assertEqual("NOT_MEASURED", value["quality_benefit"])

    def test_manual_mode_requires_per_call_confirmation(self):
        req = self.req()
        calls, snap, invoke = self.harness(req)
        with self.assertRaisesRegex(adapter.AdapterError, "PER_CALL_CONFIRMATION_REQUIRED"):
            adapter.dispatch(req, self.consent("RECOMMEND_WITH_CONFIRMATION"), "client/expert",
                             self.state(), snapshot=snap, invoke=invoke)
        self.assertEqual([], calls)
        value = adapter.dispatch(req, self.consent("RECOMMEND_WITH_CONFIRMATION"), "client/expert",
                                 self.state(), snapshot=snap, invoke=invoke,
                                 confirmed_for_this_call=True)
        self.assertEqual("EXECUTED_VERIFIED_BY_HOST", value["status"])

    def test_no_extra_call_without_consent(self):
        req = self.req()
        calls, snap, invoke = self.harness(req)
        for consent in (None, {**self.consent(), "task_id": "different"},
                        {**self.consent(), "approved_models": ["other"]}):
            with self.subTest(consent=consent), self.assertRaises(adapter.AdapterError):
                adapter.dispatch(req, consent, "client/expert", self.state(),
                                 snapshot=snap, invoke=invoke)
        self.assertEqual([], calls)

    def test_call_cap_revocation_and_stale_state(self):
        req = self.req()
        calls, snap, invoke = self.harness(req)
        for state in ({**self.state(), "calls_used": 1},
                      {**self.state(), "revoked": True},
                      {**self.state(), "inventory_revision": "old"}):
            with self.subTest(state=state), self.assertRaises(adapter.AdapterError):
                adapter.dispatch(req, self.consent(), "client/expert", state,
                                 snapshot=snap, invoke=invoke)
        self.assertEqual([], calls)

    def test_capability_changes_abort(self):
        req = self.req()
        calls, snap, invoke = self.harness(req)
        for changed in ({"inventory_revision": "v2"}, {"available_models": ["client/default"]},
                        {"delegation": "UNAVAILABLE"}, {"zero_incremental_cost_verified": False}):
            with self.subTest(changed=changed), self.assertRaises(adapter.AdapterError):
                adapter.dispatch(req, self.consent(), "client/expert", self.state(),
                                 snapshot=lambda: {**req, **changed}, invoke=invoke)
        self.assertEqual([], calls)

    def test_switch_requires_restoration(self):
        req = {**self.req(), "delegation": "UNAVAILABLE", "switching": "VERIFIED"}
        calls, snap, invoke = self.harness(req)
        with self.assertRaisesRegex(adapter.AdapterError, "RESTORE_HOOK_REQUIRED"):
            adapter.dispatch(req, self.consent(), "client/expert", self.state(),
                             snapshot=snap, invoke=invoke)
        self.assertEqual([], calls)
        restore_calls = []
        def restore(model):
            restore_calls.append(model)
            return True
        value = adapter.dispatch(req, self.consent(), "client/expert", self.state(),
                                 snapshot=snap, invoke=invoke, restore=restore)
        self.assertTrue(value["restored_to_primary"])
        self.assertEqual(["client/default"], restore_calls)
        self.assertEqual("switch", calls[0][2])

    def test_unverified_restore_never_claims_return_to_primary(self):
        req = {**self.req(), "delegation": "UNAVAILABLE", "switching": "VERIFIED"}
        calls, snap, invoke = self.harness(req)
        value = adapter.dispatch(req, self.consent(), "client/expert", self.state(),
                                 snapshot=snap, invoke=invoke, restore=lambda _: False)
        self.assertFalse(value["restored_to_primary"])
        self.assertEqual("PRIMARY_RESTORE_NOT_VERIFIED", value["status"])

    def test_host_error_consumes_attempt_no_retry(self):
        req = self.req()
        calls = []
        def broken(model, context, method):
            calls.append(model)
            raise RuntimeError("private host diagnostic")
        value = adapter.dispatch(req, self.consent(), "client/expert", self.state(),
                                 snapshot=lambda: dict(req), invoke=broken)
        self.assertEqual(["client/expert"], calls)
        self.assertEqual("HOST_CALL_FAILED", value["status"])
        self.assertEqual(1, value["next_state"]["calls_used"])
        self.assertNotIn("private", str(value))

    def test_unverified_model_identity_is_not_credited(self):
        req = self.req()
        calls, snap, invoke = self.harness(req, {"execution": "VERIFIED", "observed_model": "wrong"})
        value = adapter.dispatch(req, self.consent(), "client/expert", self.state(),
                                 snapshot=snap, invoke=invoke)
        self.assertEqual("EXECUTION_NOT_VERIFIED", value["status"])
        self.assertEqual("UNKNOWN", value["observed_model"])

    def test_unsupported_client_and_unverified_cost_block(self):
        for change in ({"switching": "UNAVAILABLE", "delegation": "UNAVAILABLE"},
                       {"zero_incremental_cost_verified": False},
                       {"inventory_status": "UNKNOWN"}):
            req = {**self.req(), **change}
            calls, snap, invoke = self.harness(req)
            with self.subTest(change=change), self.assertRaises(adapter.AdapterError):
                adapter.dispatch(req, self.consent(), "client/expert", self.state(),
                                 snapshot=snap, invoke=invoke)
            self.assertEqual([], calls)

if __name__ == "__main__":
    unittest.main()
