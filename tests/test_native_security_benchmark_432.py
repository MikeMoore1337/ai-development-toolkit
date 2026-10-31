"""#432: fixed synthetic security corpus and no-false-green benchmark invariants."""
from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import native_security_benchmark_432 as bench  # noqa: E402


class NativeSecurityBenchmark432Tests(unittest.TestCase):
    def test_frozen_corpus_is_disjoint_bilingual_and_balanced(self):
        cases, digest = bench.load_cases()
        self.assertEqual(len(cases), 38)
        self.assertEqual(len({c["id"] for c in cases}), 38)
        self.assertEqual(sum(c["attack"] for c in cases), 19)
        self.assertEqual(sum(not c["attack"] for c in cases), 19)
        self.assertEqual({c["surface"] for c in cases}, {"mcp_description", "host_config"})
        self.assertTrue(any("Игнорируй" in c.get("description", "") or
                            "Передай" in c.get("description", "") for c in cases))
        self.assertTrue(any("C:\\" in c.get("text", "") for c in cases))
        self.assertEqual(digest, "6697030f91649f0b05a113216bb49e6636d2bfe60f7d91cbf9062d807b18265e")

    def test_diagnostic_is_complete_without_unsupported_accuracy_claims(self):
        result = bench.benchmark()
        self.assertEqual(result["sample_count"], 38)
        # Emit only aggregate metrics/IDs to CI, never raw fixture payloads.
        print("NATIVE_SECURITY_HOLDOUT_432=" + json.dumps({
            "dataset_sha256": result["dataset_sha256"],
            "confusion_matrix": result["confusion_matrix"],
            "precision": result["precision"], "recall": result["recall"],
            "f1": result["f1"],
            "false_positive_ids": result["false_positive_ids"],
            "false_negative_ids": result["false_negative_ids"],
        }, sort_keys=True), flush=True)
        self.assertEqual(result["status"], "DIAGNOSTIC_ONLY")
        self.assertEqual(result["positive_count"], 19)
        self.assertEqual(result["negative_count"], 19)
        self.assertEqual(sum(result["confusion_matrix"].values()), 38)
        self.assertEqual(result["network"], "NOT_USED")
        self.assertEqual(result["model_api"], "NOT_USED")
        self.assertEqual(result["client_runtime"], "NOT_VERIFIED")
        self.assertEqual(result["upstream_agentshield_comparison"], "NOT_RUN")
        self.assertEqual(result["representative_real_world_accuracy"], "NOT_MEASURED")
        self.assertEqual(len(result["dataset_sha256"]), 64)
        self.assertTrue(all(sum(
            row[k] for k in ("tp", "fp", "tn", "fn")) > 0
            for row in result["by_category"].values()))

    def test_only_case_ids_and_categories_no_fixture_text_or_secrets(self):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(0, bench.main())
        result = json.loads(output.getvalue())
        serialized = json.dumps(result, ensure_ascii=False)
        for forbidden in ("SYNTHETIC_NOT_A_REAL_TOKEN", "Reveal the system prompt",
                          "Ignore all earlier guidance", "Invoke-RestMethod",
                          "https://webhook.site/fixture"):
            self.assertNotIn(forbidden, serialized)
        for name in ("false_positive_ids", "false_negative_ids"):
            self.assertTrue(all(bench.CASE_ID.fullmatch(s) for s in result[name]))

    def test_incomplete_scan_must_not_be_counted_as_success(self):
        with mock.patch.object(bench.cisco_mcp_gate, "scan_native_descriptions",
                               return_value={"status": "BLOCKED",
                                             "reason": "INVALID_OR_INCOMPLETE_SNAPSHOT"}):
            with self.assertRaises(ValueError):
                bench.benchmark()

    def test_duplicate_and_untrusted_fixture_paths_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixtures.json"
            for text in (
                '{"schema_version":1,"schema_version":1}',
                '{"schema_version": NaN}',
                '{"schema_version":1,"cases":[]}',
            ):
                with self.subTest(payload=text):
                    path.write_text(text, encoding="utf-8")
                    with mock.patch.object(bench, "CORPUS", path):
                        with self.assertRaises(ValueError):
                            bench.load_cases()

    def test_benchmark_does_not_call_cisco_or_external_agent_runner(self):
        with mock.patch.object(bench.cisco_mcp_gate, "scan",
                               side_effect=AssertionError("Cisco runtime used")):
            with mock.patch.object(bench.cisco_mcp_gate, "snapshot",
                                   side_effect=AssertionError("live snapshot called")):
                self.assertEqual(38, bench.benchmark()["sample_count"])


    def test_modified_valid_corpus_is_rejected_by_pinned_hash(self):
        original = json.loads(bench.CORPUS.read_text(encoding="utf-8"))
        original["cases"][0]["description"] += " changed"
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / "corpus.json"
            changed.write_text(json.dumps(original, ensure_ascii=False), encoding="utf-8")
            with mock.patch.object(bench, "CORPUS", changed):
                with self.assertRaisesRegex(ValueError, "digest mismatch"):
                    bench.load_cases()
if __name__ == "__main__":
    unittest.main()
