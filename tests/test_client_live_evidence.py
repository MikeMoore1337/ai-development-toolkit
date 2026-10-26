"""Issue #297: scoped client evidence, strict no-fabrication/offline checks."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_client_live_evidence as evidence


class ClientLiveEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(evidence.DEFAULT.read_text(encoding="utf-8"))

    def test_real_registry_has_distinct_current_historical_and_not_run(self):
        report = evidence.validate(self.registry)
        self.assertEqual(4, report["scenarios"])
        self.assertEqual(1, report["current_observed"])
        self.assertEqual(1, report["historical_owner_reported"])
        self.assertEqual(2, report["owner_reported"])
        self.assertEqual(1, report["not_run"])
        self.assertEqual("NOT_OBSERVED", report["native_activation"])
        self.assertEqual("NOT_MEASURED", report["benefit"])
        self.assertTrue(report["zero_spend"])
        self.assertTrue(report["read_only"])

    def test_codex_project_owner_report_is_exact_and_bounded(self):
        row = self.registry["scenarios"][2]
        self.assertEqual("Codex CLI", row["client"])
        self.assertEqual("Codex CLI 0.163.0; Desktop build 26.1021.31345 (not restarted)",
                         row["client_version"])
        self.assertEqual("5.5.6", row["toolkit_version"])
        self.assertEqual("71a5faaea542a4214b8fb9e0db0ae6909947a3b8", row["source_sha"])
        self.assertEqual("OWNER_REPORTED_PASS", row["l4"])
        self.assertEqual("OWNER_REPORTED_GUIDANCE_RETURNED", row["l5_guidance"])
        self.assertIn("Desktop Project MCP NOT_VERIFIED", row["limitations"])
        self.assertIn("Native activation NOT_OBSERVED", row["limitations"])
        self.assertIn("L6 NOT_MEASURED", row["limitations"])
        self.assertEqual("NOT_RUN", row["target_execution"])
        self.assertFalse(row["project_files_changed"])

    def test_project_owner_report_cannot_be_promoted_or_repointed(self):
        changes = (
            ("Independent L4", "l4", "OBSERVED_THIS_SESSION"),
            ("Independent L5", "l5_guidance", "READ_THIS_SESSION"),
            ("Wrong client", "client", "ChatGPT"),
            ("Wrong Toolkit", "toolkit_version", "5.5.5"),
            ("Wrong source", "source_sha", self.registry["current_source_sha"]),
            ("Missing Desktop boundary", "limitations", "owner report"),
        )
        for name, field, value in changes:
            with self.subTest(name=name):
                d = copy.deepcopy(self.registry)
                d["scenarios"][2][field] = value
                with self.assertRaises(evidence.EvidenceError):
                    evidence.validate(d)

    def test_forbidden_evidence_promotions_fail_closed(self):
        changes = (
            ("L4 fabrication", 2, "l4", "OBSERVED_THIS_SESSION"),
            ("L5 fabrication", 3, "l5_guidance", "READ_THIS_SESSION"),
            ("Native activation", 0, "l5_native_skill_activation", "PASS"),
            ("Benefit fabrication", 1, "l6_benefit", "VERIFIED"),
            ("Tool execution", 1, "target_execution", "PASS"),
            ("Workspace changes", 1, "project_files_changed", True),
            ("Old MCP version confusion", 1, "toolkit_version", "5.5.5"),
            ("Old MCP revision confusion", 1, "source_sha", "unverified"),
            ("Owner evidence missing", 1, "evidence", ["No evidence"]),
        )
        for name, index, field, value in changes:
            with self.subTest(name=name):
                d = copy.deepcopy(self.registry)
                d["scenarios"][index][field] = value
                with self.assertRaises(evidence.EvidenceError):
                    evidence.validate(d)

    def test_contract_schema_and_duplication_fail(self):
        for field, value in (
            ("schema_version", 2), ("zero_spend_gate", "DISABLED"),
            ("current_source_sha", "moving-main"),
            ("scenarios", [copy.deepcopy(self.registry["scenarios"][0])] * 4),
        ):
            with self.subTest(field=field):
                d = copy.deepcopy(self.registry)
                d[field] = value
                with self.assertRaises(evidence.EvidenceError):
                    evidence.validate(d)

    def test_cli_read_only_summary(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/verify_client_live_evidence.py")],
            capture_output=True, text=True, encoding="utf-8", timeout=15
        )
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual(4, json.loads(proc.stdout)["scenarios"])
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "evidence.json"
            d = copy.deepcopy(self.registry)
            d["scenarios"][0]["l6_benefit"] = "PASS"
            bad.write_text(json.dumps(d), encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/verify_client_live_evidence.py"),
                 "--file", str(bad)],
                capture_output=True, text=True, encoding="utf-8", timeout=15
            )
            self.assertNotEqual(0, proc.returncode)
            self.assertIn("FAIL:", proc.stderr)

    def test_existing_client_registries_remain_static_contracts(self):
        file_registry = json.loads((ROOT / "compatibility/clients.json").read_text())
        chat_registry = json.loads((ROOT / "compatibility/conversational_clients.json").read_text())
        self.assertEqual(1, file_registry["schema_version"])
        self.assertEqual(1, chat_registry["schema_version"])
        self.assertEqual({"codex", "claude-code", "hermes", "deepseek-harness"},
                         {c["client_id"] for c in file_registry["clients"]})
        self.assertEqual({"chatgpt", "claude-ai", "deepseek-chat"},
                         {c["client_id"] for c in chat_registry["clients"]})


if __name__ == "__main__":
    unittest.main()
