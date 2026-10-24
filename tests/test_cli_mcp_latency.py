"""Read-only latency sampling should never claim AI execution or quality benefit."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import cli_mcp_latency as latency


class CLIMCPLatencyTests(unittest.TestCase):
    def test_nearest_rank_p95_and_invalid_samples(self):
        data = latency.summarize([float(x) for x in range(1, 21)])
        self.assertEqual(20, data["n"])
        self.assertEqual(19.0, data["p95_ms"])
        self.assertEqual(10.5, data["median_ms"])
        with self.assertRaises(ValueError):
            latency.summarize([1.0] * 9)
        for n in (0, 9, 101, True):
            with self.subTest(samples=n), self.assertRaises(ValueError):
                latency.measure(ROOT, n)

    def test_offline_real_commands_have_measured_nonzero_duration(self):
        result = latency.measure(ROOT, samples=10)
        expected = {
            "cli_profile_list_process",
            "cli_skill_manager_status_process",
            "project_mcp_catalog_inprocess",
            "project_mcp_skill_read_inprocess",
            "personal_mcp_info_inprocess",
            "personal_mcp_prepare_task_inprocess",
        }
        self.assertEqual(expected, set(result["observations"]))
        self.assertEqual("NOT_RUN", result["user_project_execution"])
        self.assertEqual("NOT_OBSERVED", result["native_skill_activation"])
        self.assertEqual("NOT_MEASURED", result["model_effectiveness"])
        self.assertEqual(0, result["model_or_paid_api_calls"])
        self.assertEqual(10, result["samples_per_operation"])
        self.assertEqual(40, len(result["source_sha"]))
        for case in result["observations"].values():
            self.assertEqual(10, case["n"])
            self.assertGreater(case["median_ms"], 0)
            self.assertGreaterEqual(case["p95_ms"], case["median_ms"])
            self.assertGreaterEqual(case["max_ms"], case["p95_ms"])
        print("OFFLINE_LATENCY_BASELINE=" + json.dumps(
            {"sha": result["source_sha"], "platform": result["platform"],
             "python": result["python"], "measurements": result["observations"]},
            sort_keys=True,
        ), flush=True)

    def test_cli_invalid_sample_count_is_rejected(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/cli_mcp_latency.py"),
             "--samples", "2"],
            capture_output=True, text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(2, proc.returncode)
        self.assertIn("samples must be", proc.stderr)


if __name__ == "__main__":
    unittest.main()
