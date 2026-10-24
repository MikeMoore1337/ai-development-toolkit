"""Read-only deterministic policy tests; no clients, agent runtimes, or paid APIs."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "orchestration_decision.py"
spec = importlib.util.spec_from_file_location("orchestration_decision", SCRIPT)
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


class OrchestrationPolicyTests(unittest.TestCase):
    def request(self):
        return {
            "schema_version": 1, "scope": "MEDIUM",
            "independent_readonly_streams": 2,
            "writes_required": False,
            "parallel_capability": "NOT_VERIFIED",
            "owner_parallel_approval": False,
            "zero_incremental_cost_verified": False,
            "isolation_verified": False,
        }

    def test_default_is_sequential_not_fake_parallel(self):
        value = module.decide(self.request())
        self.assertEqual("SEQUENTIAL_REVIEW", value["recommended_route"])
        self.assertIn("PARALLEL_CAPABILITY_NOT_VERIFIED", value["parallel_gate_blockers"])
        self.assertEqual("NOT_RUN", value["execution"])
        self.assertEqual(0, value["workers_launched"])
        self.assertFalse(value["target_project_changed"])
        self.assertEqual("NOT_MEASURED", value["token_savings"])
        self.assertEqual("NOT_VERIFIED", value["client_activation"])

    def test_small_task_remains_single_agent(self):
        request = self.request()
        request["scope"] = "SMALL"
        request["parallel_capability"] = "VERIFIED"
        request["owner_parallel_approval"] = True
        request["zero_incremental_cost_verified"] = True
        request["isolation_verified"] = True
        self.assertEqual("SINGLE_AGENT", module.decide(request)["recommended_route"])

    def test_optional_parallel_requires_all_evidence(self):
        request = self.request()
        request.update(parallel_capability="VERIFIED", owner_parallel_approval=True,
                       zero_incremental_cost_verified=True, isolation_verified=True)
        actual = module.decide(request)
        self.assertEqual("OPTIONAL_PARALLEL_READONLY_REVIEW", actual["recommended_route"])
        self.assertEqual([], actual["parallel_gate_blockers"])
        self.assertEqual(0, actual["workers_launched"])
        self.assertEqual("NOT_RUN", actual["execution"])
        for field, value in (
            ("owner_parallel_approval", False),
            ("zero_incremental_cost_verified", False),
            ("isolation_verified", False),
            ("parallel_capability", "NOT_VERIFIED"),
            ("parallel_capability", "UNAVAILABLE"),
            ("independent_readonly_streams", 1),
            ("writes_required", True),
        ):
            with self.subTest(field=field, value=value):
                changed = dict(request)
                changed[field] = value
                self.assertNotEqual(
                    "OPTIONAL_PARALLEL_READONLY_REVIEW",
                    module.decide(changed)["recommended_route"],
                )

    def test_writes_always_sequential_for_nontrivial_task(self):
        request = self.request()
        request.update(scope="LARGE", writes_required=True,
                       parallel_capability="VERIFIED", owner_parallel_approval=True,
                       zero_incremental_cost_verified=True, isolation_verified=True)
        self.assertEqual("SEQUENTIAL_REVIEW", module.decide(request)["recommended_route"])
        self.assertIn("WRITES_REQUIRED", module.decide(request)["parallel_gate_blockers"])

    def test_invalid_or_malformed_input_fails_closed(self):
        original = self.request()
        cases = [None, [], "request", {"schema_version": 1},
                 {**original, "extra": "untrusted"},
                 {**original, "schema_version": True},
                 {**original, "scope": "UNKNOWN"},
                 {**original, "scope": ["MEDIUM"]},
                 {**original, "independent_readonly_streams": True},
                 {**original, "independent_readonly_streams": 4},
                 {**original, "parallel_capability": "MAYBE"},
                 {**original, "owner_parallel_approval": "yes"}]
        for case in cases:
            with self.subTest(case=repr(case)[:100]):
                with self.assertRaises(module.DecisionError):
                    module.decide(case)

    def test_cli_does_not_change_input_or_invoke_agent(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "request.json"
            source.write_text(json.dumps(self.request()), encoding="utf-8")
            before = source.read_bytes()
            cp = subprocess.run([sys.executable, str(SCRIPT), str(source)],
                                capture_output=True, text=True, timeout=10)
            self.assertEqual(0, cp.returncode, cp.stderr)
            self.assertEqual("SEQUENTIAL_REVIEW",
                             json.loads(cp.stdout)["recommended_route"])
            self.assertEqual(before, source.read_bytes())
            self.assertEqual([source.name], [p.name for p in Path(tmp).iterdir()])


if __name__ == "__main__":
    unittest.main()
