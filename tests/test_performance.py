"""Issue #59: independent arithmetic, safety and known-bad performance oracles."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import skill_sources
from skill_manager import operate, read_state
from validate_performance import (
    MAX_CONCURRENCY, MAX_OPS, MAX_RPS, MAX_SECONDS, UnsafeWorkload, Workload,
    aggregate, compare, percentile, run, validate_report,
)


def record(value: float, status: str = "SUCCESS", i: int = 0) -> dict:
    return {
        "id": i, "operation": "known-fixture", "start_ms": float(i * 10),
        "end_ms": float(i * 10 + value), "latency_ms": float(value),
        "status": status, "functional_ok": status == "SUCCESS",
    }


class PerformanceContracts(unittest.TestCase):
    def test_versioned_positive_negative_fixture_catalog(self):
        fixture = json.loads(
            (ROOT / "fixtures/performance/cases.json").read_text(encoding="utf-8")
        )
        self.assertEqual("1.0.0", fixture["fixture_version"])
        self.assertEqual("SYNTHETIC_ASSUMPTION", fixture["nature"])
        self.assertEqual("FORBIDDEN", fixture["external_targets"])
        self.assertEqual(3, len(fixture["positive"]))
        self.assertEqual(16, len(fixture["negative"]))
        for case in fixture["positive"]:
            with self.subTest(positive=case["id"]):
                config = {k: case[k] for k in
                          ("profile", "operations", "rps", "duration", "concurrency")}
                self.assertEqual("PASS", compare(run(Workload(**config)),
                                                run(Workload(**config), "candidate"))["status"])
        for case in fixture["negative"]:
            if "input" in case:
                with self.subTest(negative=case["id"]):
                    with self.assertRaises((UnsafeWorkload, TypeError)):
                        Workload(**case["input"]).slots()

    def test_percentile_known_type7_data(self):
        points = [1., 2., 3., 4., 5.]
        self.assertEqual(3, percentile(points, .5))
        self.assertAlmostEqual(4.8, percentile(points, .95))
        self.assertAlmostEqual(4.96, percentile(points, .99))
        with self.assertRaises(ValueError):
            percentile([], .95)

    def test_aggregate_known_arithmetic(self):
        samples = [record(v, i=i) for i, v in enumerate((1, 2, 3, 4, 5))]
        m = aggregate(samples, 2.0)
        self.assertEqual(5, m["attempted"])
        self.assertEqual(5, m["successful"])
        self.assertEqual(2.5, m["attempted_ops_s"])
        self.assertEqual(2.5, m["completed_ops_s"])
        self.assertEqual(2.5, m["successful_ops_s"])
        self.assertEqual(3, m["latency_ms"]["mean"])
        self.assertEqual(3, m["latency_ms"]["median"])
        self.assertEqual(1, m["latency_ms"]["min"])
        self.assertEqual(5, m["latency_ms"]["max"])
        self.assertEqual(4, m["latency_ms"]["range"])
        self.assertIsNone(m["latency_ms"]["p95"])
        self.assertIsNone(m["latency_ms"]["p99"])

    def test_percentile_sample_thresholds(self):
        m = aggregate([record(i + 1, i=i) for i in range(20)], 2)
        self.assertAlmostEqual(19.05, m["latency_ms"]["p95"])
        self.assertIsNone(m["latency_ms"]["p99"])
        m = aggregate([record(i + 1, i=i) for i in range(100)], 2)
        self.assertAlmostEqual(99.01, m["latency_ms"]["p99"])

    def test_error_numerator_denominator_and_timeouts(self):
        samples = [
            record(1, "SUCCESS", 0), record(10, "TIMEOUT", 1),
            record(3, "APPLICATION_ERROR", 2),
            record(2, "TEST_HARNESS_ERROR", 3),
        ]
        m = aggregate(samples, 2)
        self.assertEqual(4, m["attempted"])
        self.assertEqual(4, m["completed"])
        self.assertEqual(1, m["successful"])
        self.assertEqual(3, m["errors"])
        self.assertEqual(1, m["timeouts"])
        self.assertEqual((3, 4), (m["error_numerator"], m["error_denominator"]))
        self.assertEqual(.75, m["error_fraction"])
        self.assertEqual(.5, m["successful_ops_s"])

    def test_profiles_are_bounded_and_have_mixed_operations(self):
        for profile in ("constant", "step", "mixed"):
            with self.subTest(profile=profile):
                w = Workload(profile=profile)
                slots = w.slots()
                self.assertEqual(12, len(slots))
                self.assertEqual(slots, sorted(slots))
                report = run(w, virtual=True)
                validate_report(report)
                self.assertEqual("VIRTUAL_FIXTURE", report["conditions"]["mode"])
                self.assertEqual("NOT_MEASURED", report["resource_usage"])
                self.assertEqual(12, report["metrics"]["successful"])
                if profile == "mixed":
                    self.assertEqual(2, len({s["operation"] for s in report["samples"]}))

    def test_baseline_candidate_oracle_and_comparison(self):
        w = Workload()
        baseline = run(w, "baseline")
        candidate = run(w, "candidate")
        self.assertTrue(baseline["functional_correctness"])
        self.assertTrue(candidate["functional_correctness"])
        comparison = compare(baseline, candidate)
        self.assertEqual("PASS", comparison["status"])
        self.assertLess(comparison["candidate_median_ms"], comparison["baseline_median_ms"])

    def test_known_bad_faster_but_incorrect(self):
        w = Workload()
        base = run(w)
        mutant = run(w, "broken-fast")
        self.assertLess(mutant["metrics"]["latency_ms"]["median"],
                        base["metrics"]["latency_ms"]["median"])
        self.assertEqual("BLOCKED", compare(base, mutant)["status"])
        self.assertGreater(mutant["metrics"]["errors"], 0)

    def test_environment_cache_dataset_method_mismatches(self):
        base = run(Workload())
        for key, wrong in {
            "environment": "other-host", "cache_state": "warm",
            "dataset": "small", "method": "other-clock",
            "rps": 4.0, "warmup": 0, "profile": "mixed",
        }.items():
            with self.subTest(key=key):
                candidate = copy.deepcopy(run(Workload(), "candidate"))
                candidate["conditions"][key] = wrong
                self.assertEqual("COMPARISON_INVALID", compare(base, candidate)["status"])

    def test_missing_baseline(self):
        self.assertEqual("NOT_MEASURED", compare(None, run(Workload()))["status"])

    def test_small_sample_is_inconclusive(self):
        b = run(Workload(operations=4))
        c = run(Workload(operations=4), "candidate")
        self.assertEqual("INCONCLUSIVE", compare(b, c)["status"])

    def test_high_error_rate_overrides_throughput(self):
        base = run(Workload())
        candidate = copy.deepcopy(run(Workload(), "candidate"))
        for s in candidate["samples"][:4]:
            s["status"] = "TIMEOUT"
            s["functional_ok"] = True
        candidate["metrics"] = aggregate(candidate["samples"],
                                         candidate["measurement_interval_s"])
        self.assertEqual("REGRESSION", compare(base, candidate)["status"])

    def test_hidden_timeout_is_not_an_acceptable_aggregate(self):
        base = run(Workload())
        corrupted = copy.deepcopy(run(Workload(), "candidate"))
        corrupted["samples"][0]["status"] = "TIMEOUT"
        self.assertEqual("COMPARISON_INVALID", compare(base, corrupted)["status"])

    def test_unexplained_dropped_outlier_is_detected(self):
        base = run(Workload())
        corrupted = copy.deepcopy(run(Workload(), "candidate"))
        corrupted["samples"].pop()
        self.assertEqual("COMPARISON_INVALID", compare(base, corrupted)["status"])

    def test_budget_cannot_change_after_measurement(self):
        w = Workload()
        a = run(w, budget_ms=10, budget_approved=True)
        b = run(w, "candidate", budget_ms=1, budget_approved=True)
        self.assertEqual("COMPARISON_INVALID", compare(a, b)["status"])

    def test_approved_budget_is_enforced(self):
        w = Workload()
        a = run(w, budget_ms=3.5, budget_approved=True)
        b = run(w, "candidate", budget_ms=3.5, budget_approved=True)
        self.assertEqual("REGRESSION", compare(a, b)["status"])
        proposal = run(w, "candidate", budget_ms=3.5)
        self.assertEqual("PROPOSED", proposal["budget"]["approval"])

    def test_resources_missing_are_explicit(self):
        result = run(Workload())
        self.assertEqual("NOT_MEASURED", result["resource_usage"])
        self.assertNotIn("cpu_percent", result)
        self.assertNotIn("rss_bytes", result)

    def test_empty_and_corrupt_reports_fail_closed(self):
        base = run(Workload())
        for broken in ({}, {"samples": []}, [], "no report"):
            with self.subTest(case=broken):
                self.assertEqual("COMPARISON_INVALID", compare(base, broken)["status"])

    def test_mutated_counts_are_rejected(self):
        base = run(Workload())
        bad = copy.deepcopy(run(Workload(), "candidate"))
        bad["metrics"]["successful"] += 1
        self.assertEqual("COMPARISON_INVALID", compare(base, bad)["status"])

    def test_large_rps_concurrency_duration_operations_rejected(self):
        variations = [
            {"rps": 5.01}, {"rps": -1}, {"rps": float("inf")},
            {"rps": float("nan")}, {"rps": True}, {"rps": "5"},
            {"concurrency": 3}, {"concurrency": 0}, {"concurrency": True},
            {"duration": 10.01}, {"duration": float("inf")},
            {"duration": 0}, {"operations": 51}, {"operations": -1},
            {"operations": True}, {"warmup": 5}, {"operations": 50, "warmup": 2},
            {"profile": "unbounded"}, {"operations": 30, "duration": 1},
        ]
        for overrides in variations:
            with self.subTest(overrides=overrides):
                with self.assertRaises(UnsafeWorkload):
                    Workload(**overrides).slots()
        self.assertEqual((MAX_OPS, MAX_RPS, MAX_SECONDS, MAX_CONCURRENCY),
                         (50, 5., 10., 2))

    def test_public_or_production_urls_cannot_be_configured(self):
        for url in ("https://example.org", "https://production.example.org",
                    "http://127.0.0.1:1234"):
            with self.subTest(url=url):
                with self.assertRaises(TypeError):
                    Workload(url=url)
        with self.assertRaises(UnsafeWorkload):
            run(Workload(), variant="http://example.org")

    def test_no_network_or_subprocess_imports(self):
        script = (ROOT / "scripts/validate_performance.py").read_text(encoding="utf-8")
        syntax = ast.parse(script)
        modules = {a.name.split(".")[0] for n in ast.walk(syntax)
                   if isinstance(n, ast.Import) for a in n.names}
        modules |= {n.module.split(".")[0] for n in ast.walk(syntax)
                    if isinstance(n, ast.ImportFrom) and n.module}
        self.assertFalse(modules & {"socket", "urllib", "requests", "http",
                                    "subprocess", "asyncio", "aiohttp"})

    def test_bounded_real_smoke_is_not_virtual_proof(self):
        result = run(Workload(operations=5, rps=5, duration=2,
                              concurrency=2), virtual=False)
        self.assertEqual("LOCAL_SMOKE", result["conditions"]["mode"])
        self.assertEqual(5, result["metrics"]["successful"])
        self.assertTrue(result["functional_correctness"])
        self.assertEqual("NOT_MEASURED", result["resource_usage"])

    def test_profile_preview_apply_and_unmanaged_integrity(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        chosen = manifest["profiles"]["performance-load-testing"]
        self.assertEqual(["performance-load-testing", "test-strategy",
                          "failure-triage"], chosen)
        self.assertNotIn("performance-load-testing", manifest["profiles"]["general"])
        self.assertEqual(ROOT / "extensions/performance/skills/performance-load-testing",
                         skill_sources(manifest)["performance-load-testing"])
        with tempfile.TemporaryDirectory() as folder:
            for layout in ("codex", "claude"):
                dest = Path(folder) / layout
                dest.mkdir()
                old = sorted(dest.iterdir())
                preview = operate("install", dest, names=chosen, layout=layout)
                self.assertFalse(preview["applied"])
                self.assertEqual(old, sorted(dest.iterdir()))
                installed = operate("install", dest, names=chosen,
                                    layout=layout, apply=True)
                self.assertTrue(installed["applied"])
                self.assertIn("performance-load-testing", read_state(dest, layout)["skills"])


if __name__ == "__main__":
    unittest.main()
