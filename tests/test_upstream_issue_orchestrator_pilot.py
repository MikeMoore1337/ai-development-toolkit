"""Read-only source contract for original Issue-Orchestrator pilot #570.

No model calls, installation, network access, GitHub mutation, or execution.
These checks do NOT verify a live issue allowlist or E2E runtime.
"""

import json
from pathlib import Path
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / "integrations" / "issue-orchestrator"


class OriginalIssueOrchestratorSourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = json.loads((PILOT / "pilot-scope.json").read_text(encoding="utf-8"))
        cls.config = yaml.safe_load(
            (PILOT / "pilot-0.10.0.yaml").read_text(encoding="utf-8")
        )
        cls.manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

    def test_pin_and_unique_two_issue_scope(self):
        self.assertEqual(
            self.scope["upstream"]["commit"],
            "d4a79824ccd806089cf3f70ec632d39b8ee255ea",
        )
        self.assertEqual(self.scope["upstream"]["version"], "0.10.0")
        target = self.scope["target"]
        self.assertEqual(target["repository"], "example/issue-orchestrator-pilot")
        self.assertEqual(target["branch"], "main")
        self.assertEqual(target["issue_numbers"], [7, 8])
        self.assertEqual(len(target["issue_numbers"]), len(set(target["issue_numbers"])))
        self.assertEqual(target["dependency"]["directive"], "Depends-on: #7")

    def test_original_config_scope_and_branch(self):
        target = self.scope["target"]
        self.assertEqual(self.config["repo"]["name"], target["repository"])
        self.assertEqual(self.config["worktrees"]["base_branch_override"], target["branch"])
        filtering = self.config["filtering"]
        self.assertEqual(filtering["label"], target["required_label"])
        self.assertEqual(filtering["max_to_start"], 2)
        self.assertNotIn("issue", filtering)  # Single-number filter cannot select [7, 8]
        self.assertEqual(self.config["execution"]["concurrency"]["max_concurrent_sessions"], 1)

    def test_no_second_controller_or_automatic_merge(self):
        self.assertFalse(self.config["tech_lead"]["enabled"])
        self.assertFalse(self.config["goal_pilot"]["enabled"])
        self.assertFalse(self.config["merge_queue"]["enabled"])
        self.assertFalse(self.config["e2e"]["enabled"])
        self.assertTrue(self.config["review"]["enabled"])
        self.assertEqual(self.config["review"]["max_rework_cycles"], 2)
        self.assertTrue(self.config["validation"]["quick"]["cmd"])
        self.assertTrue(self.config["validation"]["publish"]["cmd"])
        self.assertEqual(
            self.config["validation"]["quick"]["cmd"],
            "python -m unittest discover -s tests -v",
        )

    def test_cli_permission_does_not_activate_unverified_runtime(self):
        policy = self.scope["enforcement"]
        self.assertEqual(policy["provider_status"], "CODEX_CLI_OWNER_PERMITTED_HOST_NOT_VERIFIED")
        self.assertFalse(policy["live_execution_authorized"])
        self.assertTrue(policy["codex_cli_authorized"])
        self.assertFalse(policy["host_cli_authenticated"])
        self.assertFalse(policy["paid_api_authorized"])
        self.assertFalse(policy["actual_immutable_allowlist"])
        self.assertFalse(policy["e2e_verified"])
        self.assertTrue(policy["human_merge"])
        for agent in self.config["agents"].values():
            self.assertEqual(agent["provider"], "codex")
            self.assertTrue(agent["sandbox"])
            self.assertNotIn("command", agent)
            self.assertNotIn("api_key", agent)

    def test_manifest_declares_disabled_upstream_integration(self):
        integration = self.manifest["optional_integrations"]["upstream_issue_orchestrator"]
        self.assertEqual(integration["source_sha"], self.scope["upstream"]["commit"])
        self.assertEqual(integration["provider_status"], "CODEX_CLI_OWNER_PERMITTED_HOST_NOT_VERIFIED")
        self.assertTrue(integration["codex_cli_owner_permitted"])
        self.assertFalse(integration["paid_api_authorized"])
        self.assertFalse(integration["automatic_install"])
        self.assertFalse(integration["live_execution"])
        self.assertFalse(integration["automatic_background_execution"])
        self.assertEqual(
            integration["config"], "integrations/issue-orchestrator/pilot-0.10.0.yaml"
        )


if __name__ == "__main__":
    unittest.main()
