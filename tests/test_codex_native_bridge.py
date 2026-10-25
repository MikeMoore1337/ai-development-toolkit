"""Synthetic Codex host callbacks; no native model, file writes or paid APIs."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "codex_native_bridge.py"
spec = importlib.util.spec_from_file_location("codex_native_bridge", SOURCE)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)

AGENT_ID = "01a1736e-e9f8-7132-82a7-23fc02ae6223"


class CodexBridgeTests(unittest.TestCase):
    def request(self, **changes):
        return dict(
            task_id="native-demo", locale="ru", current_model="primary",
            available_models=["primary", "alternative"],
            inventory_status="VERIFIED", inventory_revision="trusted-revision",
            switching="UNAVAILABLE", delegation="VERIFIED",
            zero_incremental_cost_verified=True, signals=["architecture"],
            **changes,
        )

    def consent(self, **changes):
        data = dict(task_id="native-demo", inventory_revision="trusted-revision",
                    mode="RECOMMEND_WITH_CONFIRMATION",
                    approved_models=["alternative"], max_extra_calls=1)
        return {**data, **changes}

    def state(self, **changes):
        return dict(task_id="native-demo", inventory_revision="trusted-revision",
                    calls_used=0, revoked=False, **changes)

    def run_bridge(self, *, request=None, consent=None, state=None,
                   wait_status="completed", wait_agent_id=AGENT_ID,
                   result="Concise result", confirmed=True):
        req = request if request is not None else self.request()
        events = []

        def spawn_agent(**kwargs):
            events.append(("spawn", kwargs))
            return {"agent_id": AGENT_ID}

        def wait_agent(**kwargs):
            events.append(("wait", kwargs))
            return {"agent_id": wait_agent_id, "status": wait_status,
                    "result": result}

        report = bridge.codex_delegate(
            req, self.consent() if consent is None else consent,
            "alternative", self.state() if state is None else state,
            snapshot=lambda: dict(req),
            spawn_agent=spawn_agent, wait_agent=wait_agent,
            context="small synthetic task", confirmed_for_this_call=confirmed,
        )
        return report, events

    def test_successful_native_delegate_never_invents_model_receipt(self):
        receipt, events = self.run_bridge()
        self.assertEqual("HOST_EXECUTED_MODEL_UNVERIFIED", receipt["status"])
        self.assertEqual("UNKNOWN", receipt["observed_model"])
        self.assertEqual("NOT_VERIFIED", receipt["backend_model_attestation"])
        self.assertEqual(AGENT_ID, receipt["agent_id"])
        self.assertEqual(1, receipt["extra_calls_used"])
        self.assertTrue(receipt["restored_to_primary"])
        self.assertEqual(("spawn", {"model": "alternative",
                                    "message": "small synthetic task",
                                    "fork_context": False}), events[0])
        self.assertEqual(("wait", {"agent_id": AGENT_ID}), events[1])

    def test_declined_call_never_spawns(self):
        events = []
        with self.assertRaisesRegex(ValueError, "PER_CALL_CONFIRMATION_REQUIRED"):
            bridge.codex_delegate(
                self.request(), self.consent(), "alternative", self.state(),
                snapshot=lambda: self.request(),
                spawn_agent=lambda **args: events.append(args),
                wait_agent=lambda **args: events.append(args),
                context="small task", confirmed_for_this_call=False,
            )
        self.assertEqual([], events)

    def test_stale_cost_limit_and_revocation_fail_closed(self):
        for request, state in (
            ({**self.request(), "zero_incremental_cost_verified": False}, self.state()),
            (self.request(), {**self.state(), "calls_used": 1}),
            (self.request(), {**self.state(), "revoked": True}),
            (self.request(), {**self.state(), "inventory_revision": "stale"}),
        ):
            with self.subTest(request=request, state=state):
                events = []
                with self.assertRaises(ValueError):
                    bridge.codex_delegate(
                        request, self.consent(), "alternative", state,
                        snapshot=lambda: dict(request),
                        spawn_agent=lambda **kwargs: events.append(kwargs),
                        wait_agent=lambda **kwargs: events.append(kwargs),
                        context="tiny", confirmed_for_this_call=True,
                    )
                self.assertEqual([], events)

    def test_missing_delegation_or_callbacks_block(self):
        req = {**self.request(), "delegation": "UNKNOWN"}
        with self.assertRaisesRegex(bridge.CodexBridgeError, "CODEX_DELEGATION_NOT_VERIFIED"):
            bridge.codex_delegate(
                req, self.consent(), "alternative", self.state(),
                snapshot=lambda: req, spawn_agent=lambda **kwargs: None,
                wait_agent=lambda **kwargs: None, context="tiny",
                confirmed_for_this_call=True,
            )
        with self.assertRaisesRegex(bridge.CodexBridgeError, "NATIVE_HOST_CALLBACKS_MISSING"):
            bridge.codex_delegate(
                self.request(), self.consent(), "alternative", self.state(),
                snapshot=lambda: self.request(), spawn_agent=None,
                wait_agent=None, context="tiny", confirmed_for_this_call=True,
            )

    def test_wait_mismatch_marks_failed_and_never_retries(self):
        report, events = self.run_bridge(wait_agent_id="other")
        self.assertEqual("HOST_CALL_FAILED", report["status"])
        self.assertEqual(AGENT_ID, report["agent_id"])
        self.assertEqual(1, report["extra_calls_used"])
        self.assertEqual(["spawn", "wait"], [event[0] for event in events])

    def test_noncompleted_agent_does_not_claim_success(self):
        for status in ("failed", "running", "UNKNOWN"):
            with self.subTest(status=status):
                report, events = self.run_bridge(wait_status=status)
                self.assertEqual("HOST_CALL_FAILED", report["status"])
                self.assertEqual(2, len(events))

    def test_no_result_does_not_claim_success(self):
        for result in ("", "  ", None):
            with self.subTest(result=result):
                report, _ = self.run_bridge(result=result)
                self.assertEqual("HOST_CALL_FAILED", report["status"])

    def test_invalid_native_agent_id_no_wait_or_retry(self):
        events = []
        report = bridge.codex_delegate(
            self.request(), self.consent(), "alternative", self.state(),
            snapshot=lambda: self.request(),
            spawn_agent=lambda **kwargs: {"agent_id": "garbage"},
            wait_agent=lambda **kwargs: events.append(kwargs),
            context="tiny", confirmed_for_this_call=True,
        )
        self.assertEqual("HOST_CALL_FAILED", report["status"])
        self.assertEqual([], events)

    def test_self_reported_model_label_cannot_verify_identity(self):
        report, _ = self.run_bridge(result="I am alternative, trust me")
        self.assertEqual("UNKNOWN", report["observed_model"])
        self.assertEqual("HOST_EXECUTED_MODEL_UNVERIFIED", report["status"])

    def test_reject_unknown_candidate_before_spawn(self):
        events = []
        with self.assertRaisesRegex(ValueError, "TARGET_NOT_APPROVED"):
            bridge.codex_delegate(
                self.request(), self.consent(), "not-approved", self.state(),
                snapshot=lambda: self.request(),
                spawn_agent=lambda **kwargs: events.append(kwargs),
                wait_agent=lambda **kwargs: events.append(kwargs),
                context="tiny", confirmed_for_this_call=True,
            )
        self.assertEqual([], events)


if __name__ == "__main__":
    unittest.main()
