"""End-to-end reference-oracle smoke with NO model calls, net, or outputs."""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from agent_eval_fixtures import FIXTURES
from agent_eval_offline_smoke import perform_smoke, oracle_exit, REFERENCE_FIXES


class OfflineSmokeTests(unittest.TestCase):
    def test_python_paired_hidden_oracle_discriminates(self):
        result = perform_smoke(["python-api"], strict_runtimes=True)
        self.assertTrue(result["all_requested_cases_exercised"])
        self.assertEqual("SYNTHETIC_OFFLINE_HARNESS_SMOKE_NOT_MODEL_EVAL",
                         result["classification"])
        self.assertEqual(0, result["real_agent_trials"])
        self.assertEqual("NOT_MEASURED", result["real_agent_outcomes"])
        self.assertEqual("NOT_PERFORMED", result["independent_review"])
        case = result["cases"][0]
        self.assertTrue(case["baseline_oracle_failed"])
        self.assertTrue(case["reference_oracle_passed"])
        self.assertEqual(40, len(case["initial_git_sha"]))
        self.assertEqual(64, len(case["initial_snapshot_sha256"]))
        self.assertEqual(0, case["provider_calls"])

    def test_every_available_language_has_discriminative_oracle(self):
        for case_id in sorted(FIXTURES):
            if case_id == "python-api":
                continue
            command = {"javascript": "node", "go": "go"}[FIXTURES[case_id]["language"]]
            if not shutil.which(command):
                continue
            with self.subTest(case=case_id):
                outcome = perform_smoke([case_id], strict_runtimes=True)
                self.assertTrue(outcome["all_requested_cases_exercised"])
                self.assertEqual("OFFLINE_ORACLE_DISCRIMINATES",
                                 outcome["cases"][0]["state"])

    def test_missing_runtime_cannot_be_advertised_as_complete(self):
        with patch("agent_eval_offline_smoke.allowed_runtime", return_value=False):
            with self.assertRaisesRegex(ValueError, "runtime unavailable"):
                perform_smoke(["go-cli"], strict_runtimes=True)
            report = perform_smoke(["go-cli"])
        self.assertFalse(report["all_requested_cases_exercised"])
        self.assertEqual("SKIPPED_RUNTIME_MISSING", report["cases"][0]["state"])

    def test_broken_reference_is_rejected(self):
        with patch.dict(REFERENCE_FIXES["python-api"], {
            "retry.py": FIXTURES["python-api"]["files"]["retry.py"]
        }):
            with self.assertRaisesRegex(ValueError, "not discriminative"):
                perform_smoke(["python-api"], strict_runtimes=True)

    def test_no_executing_provider_cli_or_network_client(self):
        allowed = {"git", "go", "node", Path(sys.executable).name.lower()}
        launched = []
        original = subprocess.run

        def checked(argv, *args, **kwargs):
            name = Path(argv[0]).name.lower()
            self.assertIn(name, allowed)
            self.assertNotIn(name, {"codex", "claude", "curl", "ssh", "npm", "pip"})
            self.assertFalse(kwargs.get("shell", False))
            launched.append(name)
            return original(argv, *args, **kwargs)

        with patch("agent_eval_fixtures.subprocess.run", side_effect=checked), \
             patch("agent_eval_offline_smoke.subprocess.run", side_effect=checked):
            result = perform_smoke(["python-api"], strict_runtimes=True)
        self.assertTrue(result["all_requested_cases_exercised"])
        self.assertIn("git", launched)
        self.assertIn(Path(sys.executable).name.lower(), launched)

    def test_oracle_process_environment_never_inherits_secrets_or_hooks(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            original = subprocess.run
            observed = []
            def probe(argv, *args, **kwargs):
                observed.append(kwargs["env"])
                return subprocess.CompletedProcess(argv, 1, b"", b"")
            with patch.dict("os.environ", {
                "OPENAI_API_KEY": "fake-openai-secret",
                "ANTHROPIC_API_KEY": "fake-anthropic-secret",
                "NODE_OPTIONS": "--require=/tmp/evil.js",
                "PYTHONINSPECT": "1",
                "GIT_CONFIG_COUNT": "1",
                "GOFLAGS": "-mod=mod",
            }), patch("agent_eval_offline_smoke.subprocess.run", side_effect=probe):
                verdict = oracle_exit("python-api", workspace)
        self.assertEqual(1, verdict["returncode"])
        self.assertEqual(len(observed), 1)
        env = observed[0]
        for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "NODE_OPTIONS",
                    "PYTHONINSPECT", "GIT_CONFIG_COUNT", "GOFLAGS"):
            self.assertNotIn(key, env)
        self.assertEqual("off", env["GOPROXY"])
        self.assertEqual("off", env["GOTOOLCHAIN"])
        self.assertEqual(str(workspace), env["PYTHONPATH"])

    def test_unknown_cases_and_invalid_timeouts_fail_closed(self):
        for inputs in ([], ["unknown"], ["python-api", "python-api"]):
            with self.assertRaises(ValueError):
                perform_smoke(inputs)
        with tempfile.TemporaryDirectory() as directory:
            for timeout in (0, 121):
                with self.assertRaises(ValueError):
                    oracle_exit("python-api", Path(directory), timeout=timeout)

    def test_failure_or_skips_do_not_invent_real_model_verdicts(self):
        report = perform_smoke(["python-api"], strict_runtimes=True)
        payload = json.dumps(report)
        self.assertNotIn("acceptance_delta_percentage_points", payload)
        self.assertNotIn("reviewer_attested", payload)
        self.assertNotIn('"executed": true', payload)
        self.assertNotIn("skill_activation_observed", payload)
        self.assertEqual(0, report["real_agent_trials"])


if __name__ == "__main__":
    unittest.main()
