"""#533 - deterministic synthetic contract tests; never attest a ChatGPT client."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_chatgpt_route_receipt as verifier

FIXTURE = ROOT / "fixtures" / "chatgpt_route_receipt_synthetic.json"
ARTIFACT = ROOT / "fixtures" / "route_receipt_artifact.txt"


class RouteReceiptTests(unittest.TestCase):
    def setUp(self):
        self.good = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def check(self, data, expected="FAIL"):
        return verifier.validate(data, ROOT)["evidence_sequence"] == expected

    def test_01_full_synthetic_sequence(self):
        result = verifier.validate(self.good, ROOT)
        self.assertEqual("PASS", result["evidence_sequence"])
        self.assertEqual("SYNTHETIC_ONLY", result["client_attestation"])
        self.assertEqual("NOT_VERIFIED", result["live_client_trace"])
        self.assertEqual([], result["errors"])

    def test_02_missing_preference_read(self):
        d = copy.deepcopy(self.good)
        d["events"].pop(0)
        self.assertTrue(self.check(d))

    def test_03_backend_preference_not_client_read(self):
        d = copy.deepcopy(self.good)
        d["events"][0]["data"]["read_source"] = "backend_stored_value"
        self.assertTrue(self.check(d))

    def test_04_no_orchestra_source_read(self):
        d = copy.deepcopy(self.good)
        d["events"][1]["data"]["loaded_sources"] = []
        self.assertTrue(self.check(d))

    def test_05_missing_original(self):
        d = copy.deepcopy(self.good)
        d["events"] = [e for e in d["events"] if e["data"].get("name") != "ui-ux-pro-max"]
        self.assertTrue(self.check(d))

    def test_06_help_only_does_not_prove_native_process(self):
        d = copy.deepcopy(self.good)
        d["events"][2]["data"].update(stage="help", command="impeccable --help")
        self.assertTrue(self.check(d))

    def test_07_nonzero_exit(self):
        d = copy.deepcopy(self.good)
        d["events"][3]["data"]["exit_code"] = 1
        self.assertTrue(self.check(d))

    def test_08_duplicate_and_backdated_events(self):
        d = copy.deepcopy(self.good)
        d["events"][4]["event_id"] = d["events"][3]["event_id"]
        self.assertTrue(self.check(d))
        d = copy.deepcopy(self.good)
        d["events"][4]["observed_at"] = "2026-11-06T00:00:00Z"
        self.assertTrue(self.check(d))
        d = copy.deepcopy(self.good)
        d["events"][4]["task_id"] = "task_" + "f" * 32
        self.assertTrue(self.check(d))

    def test_09_unknown_active_mount_must_not_be_forged(self):
        d = copy.deepcopy(self.good)
        d["run_kind"] = "LIVE"
        d["versions"]["active_mount"]["version"] = "NOT_VERIFIED"
        result = verifier.validate(d, ROOT)
        self.assertEqual("BLOCKED_HOST_TRACE_API", result["live_client_trace"])
        self.assertEqual("NOT_VERIFIED", result["active_mount_version"])
        self.assertNotEqual("PASS", result["client_attestation"])

    def test_10_reviewer_fix_is_not_ship(self):
        d = copy.deepcopy(self.good)
        d["events"][6]["data"]["disposition"] = "fix"
        self.assertTrue(self.check(d))

    def test_11_artifact_missing_or_hash_wrong(self):
        d = copy.deepcopy(self.good)
        d["events"][2]["data"]["artifact"]["path"] = "fixtures/no-such-file.txt"
        self.assertTrue(self.check(d))
        d = copy.deepcopy(self.good)
        d["events"][2]["data"]["artifact"]["sha256"] = "0" * 64
        self.assertTrue(self.check(d))

    def test_12_secrets_personal_paths_and_prompts(self):
        for text in ("ghp_TEST_MOCK_SECRET_0123456", "C:\\Users\\private\\file.txt", "/home/realuser/key", "Bearer a-secret", "user@example.com"):
            with self.subTest(text=text):
                d = copy.deepcopy(self.good)
                d["events"][2]["data"]["command"] = text
                with self.assertRaises(verifier.ReceiptRejected):
                    verifier.validate(d, ROOT)
        d = copy.deepcopy(self.good)
        d["raw_prompt"] = "Hello world"
        with self.assertRaises(verifier.ReceiptRejected):
            verifier.validate(d, ROOT)

    def test_13_source_runtime_conflict(self):
        d = copy.deepcopy(self.good)
        d["events"][3]["data"]["runtime_toolkit_sha"] = "e" * 40
        self.assertTrue(self.check(d))

    def test_14_inline_degraded_reported_separately(self):
        d = copy.deepcopy(self.good)
        d["events"][6]["data"]["mode"] = "INLINE_DEGRADED"
        d["events"][6]["status"] = "DEGRADED"
        result = verifier.validate(d, ROOT)
        self.assertEqual("PASS", result["evidence_sequence"])
        self.assertEqual("DEGRADED", result["reviewer_status"])
        self.assertNotEqual("PASS", result["client_attestation"])

    def test_15_nonapplicable_original_not_spoofed_as_run(self):
        d = copy.deepcopy(self.good)
        event = d["events"][2]
        event["status"] = "BLOCKED"
        event["data"]["applicability"] = "NOT_APPLICABLE_NATIVE_SCOPE"
        event["data"]["applicability_source"] = "SKILL.md"
        event["data"]["applicability_reason"] = "Synthetic scope exclusion"
        self.assertTrue(self.check(d))

    def test_16_untrusted_live_payload_never_attests_host(self):
        d = copy.deepcopy(self.good)
        d["run_kind"] = "LIVE"
        d["versions"]["active_mount"].update(version="0.1.19", source="self_reported")
        result = verifier.validate(d, ROOT)
        self.assertEqual("BLOCKED_HOST_TRACE_API", result["live_client_trace"])
        self.assertNotEqual("PASS", result["client_attestation"])

    def test_17_directory_traversal_and_symlink_rejected(self):
        d = copy.deepcopy(self.good)
        d["events"][2]["data"]["artifact"]["path"] = "../outside.txt"
        with self.assertRaises(verifier.ReceiptRejected):
            verifier.validate(d, ROOT)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "fixtures").mkdir()
            (root / "fixtures" / "route_receipt_artifact.txt").symlink_to(ARTIFACT)
            self.assertEqual("FAIL", verifier.validate(self.good, root)["evidence_sequence"])

    def test_18_template_is_private_safe_empty(self):
        d = verifier.empty_receipt()
        self.assertTrue(d["task_id"].startswith("task_"))
        self.assertEqual([], d["events"])
        self.assertNotIn("prompt", json.dumps(d).lower())
        self.assertEqual("NOT_VERIFIED", d["versions"]["active_mount"]["version"])
        self.assertEqual("FAIL", verifier.validate(d, ROOT)["evidence_sequence"])

    def test_19_untrusted_malformed_nested_values_do_not_crash(self):
        for value in ([], {}, None, 12):
            with self.subTest(value=value):
                d = copy.deepcopy(self.good)
                d["events"][2]["data"]["name"] = value
                self.assertTrue(self.check(d))

    def test_20_duplicate_primary_ref(self):
        d = copy.deepcopy(self.good)
        d["events"][2]["proof_ref"] = d["events"][1]["proof_ref"]
        self.assertTrue(self.check(d))

    def test_22_unix_unc_and_tilde_personal_paths_rejected(self):
        for value in ("/workspace/projects/private", "/tmp/file", "/var/log/secret", "~/private/file", r"\\server\share\data"):
            with self.subTest(value=value):
                d = copy.deepcopy(self.good)
                d["events"][3]["data"]["command"] = value
                with self.assertRaises(verifier.ReceiptRejected):
                    verifier.validate(d, ROOT)

    def test_23_excessive_nesting_is_rejected_without_trace(self):
        d = copy.deepcopy(self.good)
        nested = "value"
        for _ in range(24):
            nested = {"next": nested}
        d["events"][2]["data"]["unexpected"] = nested
        with self.assertRaises(verifier.ReceiptRejected):
            verifier.validate(d, ROOT)

    def test_24_boolean_browser_failure_count_is_not_zero(self):
        d = copy.deepcopy(self.good)
        d["events"][7]["data"]["tests_failed"] = False
        self.assertTrue(self.check(d))

    def test_25_symlinked_artifact_root_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            link = Path(td) / "link"
            link.symlink_to(ROOT, target_is_directory=True)
            self.assertEqual("FAIL", verifier.validate(self.good, link)["evidence_sequence"])

    def test_26_native_substage_not_applicable_but_original_invoked(self):
        d = copy.deepcopy(self.good)
        event = d["events"][2]
        event["data"].update(applicability="NATIVE_SUBSTAGE_NOT_APPLICABLE",
                             applicability_source="Upstream skill reference", applicability_reason="No concept-stage for an audited existing UI",
                             stage="native-inspection", command="impeccable inspect-native --scope test")
        result = verifier.validate(d, ROOT)
        self.assertEqual("PASS", result["evidence_sequence"])
        self.assertEqual("SYNTHETIC_ONLY", result["client_attestation"])

    def test_27_scope_skip_cannot_replace_original_invocation(self):
        d = copy.deepcopy(self.good)
        event = d["events"][2]
        event["data"].update(applicability="NOT_APPLICABLE_NATIVE_SCOPE",
                             applicability_source="Upstream skill reference", applicability_reason="Scope excludes seed",
                             stage="help", command="impeccable --help", exit_code=0)
        self.assertTrue(self.check(d))
        d = copy.deepcopy(self.good)
        event = d["events"][2]
        event["data"].update(applicability="NOT_APPLICABLE_NATIVE_SCOPE",
                             applicability_source="Upstream skill reference", applicability_reason="Scope excludes seed",
                             stage="native-inspection", artifact=None)
        self.assertTrue(self.check(d))

    def test_29_raw_fixture_digest_has_cross_platform_checkout_policy(self):
        attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("fixtures/route_receipt_artifact.txt -text", attributes.splitlines())
        digest = self.good["events"][2]["data"]["artifact"]["sha256"]
        self.assertEqual(digest, hashlib.sha256(ARTIFACT.read_bytes()).hexdigest())
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixture = root / "fixtures" / "route_receipt_artifact.txt"
            fixture.parent.mkdir(parents=True)
            fixture.write_bytes(ARTIFACT.read_bytes().replace(b"\n", b"\r\n"))
            changed = verifier.validate(self.good, root)
            self.assertIn("ARTIFACT_SHA256_MISMATCH", changed["errors"])

    def test_30_windows_drive_relative_paths_cannot_escape_artifact_root(self):
        for path in ("C:secrets.txt", "C:secret/contents.txt", "D:/secrets.txt",
                     "fixtures/./route_receipt_artifact.txt",
                     "fixtures//route_receipt_artifact.txt"):
            with self.subTest(path=path):
                d = copy.deepcopy(self.good)
                d["events"][2]["data"]["artifact"]["path"] = path
                if path in ("D:/secrets.txt", "fixtures/./route_receipt_artifact.txt"):
                    with self.assertRaises(verifier.ReceiptRejected):
                        verifier.validate(d, ROOT)
                else:
                    result = verifier.validate(d, ROOT)
                    self.assertIn("ARTIFACT_PATH_INVALID", result["errors"])

    def test_31_duplicate_json_fields_are_rejected_before_validation(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "duplicated.json"
            raw = FIXTURE.read_text(encoding="utf-8")
            self.assertIn('"schema_version": 1,', raw)
            raw = raw.replace('"schema_version": 1,',
                              '"schema_version": 1, "schema_version": 1,', 1)
            src.write_text(raw, encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(ROOT / "scripts/verify_chatgpt_route_receipt.py"),
                 "--receipt", str(src), "--artifact-root", str(ROOT)],
                capture_output=True, text=True, encoding="utf-8", timeout=15)
            self.assertEqual(2, proc.returncode)
            self.assertEqual("RECEIPT_REJECTED", proc.stderr.strip())
            self.assertNotIn("schema_version", proc.stdout)

    def test_32_self_reported_active_mount_version_never_promoted(self):
        d = copy.deepcopy(self.good)
        d["run_kind"] = "LIVE"
        d["versions"]["active_mount"] = {"version": "9.9.9", "source": "self_reported"}
        for event in d["events"]:
            event["evidence_origin"] = ("OWNER_MESSAGE" if event["stage"] == "OWNER_APPROVAL"
                                        else "HOST_TOOL_RESULT")
        result = verifier.validate(d, ROOT)
        self.assertEqual("FAIL", result["evidence_sequence"])
        self.assertEqual("NOT_VERIFIED", result["active_mount_version"])
        self.assertIn("ACTIVE_MOUNT_CLAIM_UNATTESTED", result["errors"])
        self.assertEqual("BLOCKED_HOST_TRACE_API", result["client_attestation"])

    def test_33_delayed_capture_or_backdated_first_event_rejected(self):
        d = copy.deepcopy(self.good)
        d["events"][0]["observed_at"] = "2026-11-05T00:00:00Z"
        result = verifier.validate(d, ROOT)
        self.assertEqual("FAIL", result["evidence_sequence"])
        self.assertIn("DELAYED_OR_BACKDATED_CAPTURE", result["errors"])
        self.assertEqual("SYNTHETIC_ONLY", result["client_attestation"])

    def test_28_entire_native_scope_exclusion_never_counts_all_three(self):
        d = copy.deepcopy(self.good)
        event = d["events"][2]
        event["data"].update(applicability="NOT_APPLICABLE_NATIVE_SCOPE",
                             applicability_source="Pinned upstream skill", applicability_reason="Surface excluded",
                             stage="native-inspection", command="impeccable inspect-native --scope test")
        self.assertTrue(self.check(d))

    def test_35_native_main_command_can_accept_context_flag(self):
        d = copy.deepcopy(self.good)
        d["events"][2]["data"]["command"] = "impeccable concept-seed --context synthetic-brief.json"
        self.assertEqual("PASS", verifier.validate(d, ROOT)["evidence_sequence"])
        for command in ("impeccable context", "impeccable --help", "echo impeccable concept-seed"):
            with self.subTest(command=command):
                bad = copy.deepcopy(self.good)
                bad["events"][2]["data"]["command"] = command
                result = verifier.validate(bad, ROOT)
                self.assertIn("NATIVE_STAGE_NOT_RUN", result["errors"])
                self.assertEqual("FAIL", result["evidence_sequence"])

    def test_34_owner_approval_must_bind_a_verified_visual_artifact(self):
        d = copy.deepcopy(self.good)
        d["events"][5]["data"]["approved_sha256"] = "0" * 64
        result = verifier.validate(d, ROOT)
        self.assertEqual("FAIL", result["evidence_sequence"])
        self.assertIn("OWNER_APPROVAL_ARTIFACT_MISMATCH", result["errors"])

        d = copy.deepcopy(self.good)
        d["events"][5]["data"]["approved_artifact"]["sha256"] = "f" * 64
        result = verifier.validate(d, ROOT)
        self.assertEqual("FAIL", result["evidence_sequence"])
        self.assertIn("ARTIFACT_SHA256_MISMATCH", result["errors"])
        self.assertIn("OWNER_APPROVAL_ARTIFACT_MISMATCH", result["errors"])

        d = copy.deepcopy(self.good)
        d["events"][5]["data"].pop("approved_artifact")
        self.assertTrue(self.check(d))

        d = copy.deepcopy(self.good)
        d["events"][5]["data"]["approved_artifact"]["path"] = "fixtures/not-exists.png"
        result = verifier.validate(d, ROOT)
        self.assertIn("ARTIFACT_MISSING", result["errors"])
        self.assertEqual("FAIL", result["evidence_sequence"])

    def test_21_cli_never_exports_raw_event_payload(self):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts/verify_chatgpt_route_receipt.py"),
                               "--receipt", str(FIXTURE), "--artifact-root", str(ROOT)],
                              capture_output=True, text=True, timeout=10)
        self.assertEqual(0, proc.returncode, proc.stderr)
        self.assertEqual("SYNTHETIC_ONLY", json.loads(proc.stdout)["client_attestation"])
        self.assertNotIn("impeccable concept", proc.stdout)


if __name__ == "__main__":
    unittest.main()
