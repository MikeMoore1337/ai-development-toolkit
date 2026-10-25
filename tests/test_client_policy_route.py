"""Cross-client decision support is not client execution or authorization."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import client_policy_route as route
import client_capabilities as cap
import toolkit_preferences as prefs


class ClientPolicyRoutes(unittest.TestCase):
    def doc(self, **keys):
        return {"schema_version": 1, **keys}

    def preview(self, **user):
        return prefs.resolve(self.doc(**user))

    def test_all_client_routes_are_known_and_guidance_is_read_only(self):
        for client in sorted(prefs.CLIENTS):
            with self.subTest(client=client):
                report = route.assess(self.preview(), client)
                self.assertFalse(report["execution_authorized"])
                self.assertEqual("NOT_EXECUTED", report["execution"])
                self.assertEqual(0, report["paid_api_calls"])
                self.assertEqual(0, report["model_calls"])
                self.assertEqual("NOT_VERIFIED", report["L4_skill_discovery"])
                self.assertEqual("NOT_VERIFIED", report["L5_skill_invocation"])
                self.assertEqual("NOT_MEASURED", report["L6_effectiveness"])
                self.assertFalse(report["project_files_changed"])
                if client in ("codex-cli", "claude-code", "api"):
                    self.assertEqual("BLOCKED_BY_POLICY", report["status"])
                else:
                    self.assertEqual("GUIDANCE_ONLY", report["status"])

    def test_owner_desktop_without_cli_credits_policy(self):
        policy = self.preview(clients={"allowed": ["codex-desktop", "chatgpt", "chatgpt-plugin"],
                                       "preferred": "codex-desktop"})
        self.assertEqual("GUIDANCE_ONLY",
                         route.assess(policy, "codex-desktop")["status"])
        self.assertEqual("BLOCKED_BY_POLICY",
                         route.assess(policy, "codex-cli")["status"])
        self.assertEqual("BLOCKED_BY_POLICY", route.assess(policy, "api")["status"])

    def test_explicit_user_cli_opt_in_does_not_run_anything(self):
        policy = self.preview(execution={"allow_cli_agents": True})
        for client in ("codex-cli", "claude-code"):
            report = route.assess(policy, client, operation="cli-agent")
            self.assertEqual("REVIEW_REQUIRED", report["status"])
            self.assertFalse(report["execution_authorized"])

    def test_explicit_paid_opt_in_requires_all_three_guards(self):
        for attrs in (
            {"allow_paid_api": True, "additional_spend_allowed": True},
            {"additional_spend_allowed": True, "allow_network": True},
        ):
            with self.subTest(attrs=attrs):
                settings = self.preview(execution=attrs)
                self.assertEqual("BLOCKED_BY_POLICY", route.assess(
                    settings, "api", "paid-api")["status"])
        policy = self.preview(execution={"allow_paid_api": True,
                                         "additional_spend_allowed": True,
                                         "allow_network": True})
        permitted = route.assess(policy, "api", "paid-api")
        self.assertEqual("REVIEW_REQUIRED", permitted["status"])
        self.assertEqual(0, permitted["paid_api_calls"])
        self.assertEqual("NOT_VERIFIED", permitted["live_installation"])

    def test_no_project_override_can_loosen_user(self):
        with self.assertRaises(prefs.PreferencesError):
            prefs.resolve(self.doc(execution={"allow_cli_agents": False}),
                          self.doc(execution={"allow_cli_agents": True}))
        with self.assertRaises(prefs.PreferencesError):
            prefs.resolve(self.doc(clients={"allowed": ["chatgpt"]}),
                          self.doc(clients={"allowed": ["chatgpt", "codex-cli"]}))

    def test_cross_route_operations_are_denied(self):
        p = self.preview(execution={"allow_cli_agents": True, "allow_network": True,
                                    "allow_paid_api": True, "additional_spend_allowed": True,
                                    "real_agent_pilots": True})
        self.assertEqual("BLOCKED_BY_POLICY", route.assess(p, "chatgpt",
                             "cli-agent")["status"])
        self.assertEqual("BLOCKED_BY_POLICY", route.assess(p, "claude-code",
                             "paid-api")["status"])
        self.assertEqual("BLOCKED_BY_POLICY", route.assess(p, "chatgpt",
                             "agent-pilot")["status"])

    def test_session_claims_are_never_promoted_to_verified(self):
        caps = {name: "UNKNOWN" for name in cap.CAPABILITIES}
        caps.update(toolkit_access="AVAILABLE", file_read="AVAILABLE")
        report = route.assess(self.preview(), "chatgpt",
                              session_capabilities=caps)
        self.assertEqual("TOOLKIT_REFERENCE", report["capability_route_candidate"])
        self.assertEqual("USER_DECLARED_NOT_VERIFIED", report["capability_basis"])
        self.assertEqual("NOT_VERIFIED", report["L5_skill_invocation"])
        caps["skill_discovery"] = "ENABLE"
        with self.assertRaises(route.RoutingError):
            route.assess(self.preview(), "chatgpt", session_capabilities=caps)
        with self.assertRaises(route.RoutingError):
            route.assess(self.preview(), "api", session_capabilities={})

    def test_empty_or_corrupt_policy_denied(self):
        for report in ({}, {"classification": "READ_ONLY_PREFERENCES_PREVIEW",
                             "execution_authorized": True},):
            with self.assertRaises(route.RoutingError):
                route.assess(report, "chatgpt")
        with self.assertRaises(route.RoutingError):
            route.assess(self.preview(), "invalid-client")
        with self.assertRaises(route.RoutingError):
            route.assess(self.preview(), "chatgpt", "shell")

    def test_cli_readonly_no_file_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            user = root / "preferences.json"
            user.write_text(json.dumps(self.doc(clients={
                "allowed": ["chatgpt"], "preferred": "chatgpt"
            })), encoding="utf-8")
            original = user.read_bytes()
            out, err = StringIO(), StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                rc = route.main(["--user-config", str(user), "--client", "chatgpt"])
            self.assertEqual(0, rc, err.getvalue())
            self.assertEqual(original, user.read_bytes())
            self.assertFalse(json.loads(out.getvalue())["execution_authorized"])


if __name__ == "__main__":
    unittest.main()
