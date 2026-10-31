"""#433 project-scoped explicit reviewed-reference file regressions (synthetic only)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import reviewed_memory as memory  # noqa: E402
import toolkit_mcp as mcp  # noqa: E402

ISSUE = "https://github.com/example/toolkit-demo/issues/11"
REVIEW = "https://github.com/example/toolkit-demo/issues/11#issuecomment-38"
REF = "https://github.com/example/toolkit-demo/pull/12"
SUMMARY = "Human inspected this design choice and recorded a project constraint."


class ReviewedMemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.root.mkdir()
        self.folder = Path(self.temp.name) / "explicit-memory"
        self.folder.mkdir()
        self.file = self.folder / "review-one.json"
        self.git("init", "-b", "main")
        self.git("remote", "add", "origin", "https://github.com/example/toolkit-demo.git")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                 "commit", "--allow-empty", "-m", "synthetic")

    def git(self, *args):
        subprocess.run(["git", "-C", str(self.root), *args],
                       check=True, capture_output=True)

    def record(self, *, summary=SUMMARY):
        return memory.prepare_record(self.root, ISSUE, REVIEW,
                                     "DECISION", summary, [REF])

    def _invoke(self, tool, **arguments):
        return mcp.handle({"jsonrpc": "2.0", "id": 22, "method": "tools/call",
                           "params": {"name": tool, "arguments": arguments}})

    def test_preview_has_bounded_project_data_no_writes(self):
        packet = self.record(summary="Проверенное человеком решение оставить исходную реализацию.")
        self.assertEqual(set(packet), memory.RECORD_FIELDS)
        self.assertEqual(packet["scope"], "project")
        self.assertEqual(packet["trust"], "UNTRUSTED_REFERENCE")
        self.assertEqual(packet["owner_approval"], "NOT_GRANTED")
        self.assertEqual(packet["review_attestation"], "OPERATOR_CLAIM_NOT_AUTHENTICATED")
        self.assertFalse(list(self.folder.iterdir()))
        self.assertNotIn(str(self.root), json.dumps(packet))
        checked = memory.verify_record(self.root, packet)
        self.assertEqual(checked["decision"], "REVIEW_REQUIRED")
        self.assertEqual(checked["review_attestation"], "NOT_VERIFIED")
        self.assertEqual(checked["next_action"], "REVIEW_ISSUE")

    def test_explicit_file_create_only_and_restart_read(self):
        packet = self.record()
        memory.handoff._handoff_file(self.file, self.root, create=True)
        memory.handoff._capture_handoff_file(self.file, packet)
        self.assertEqual(memory.read_record(self.root, self.file)["summary"], SUMMARY)
        with self.assertRaises(ValueError):
            memory.handoff._handoff_file(self.file, self.root, create=True)
        if os.name != "nt":
            self.assertEqual(self.file.stat().st_mode & 0o777, 0o600)
        # Stored project identity survives a different absolute checkout location.
        replica = Path(self.temp.name) / "repo-portable"
        shutil.copytree(self.root, replica, copy_function=shutil.copyfile)
        result = memory.read_record(replica, self.file)
        self.assertEqual(result["decision"], "REVIEW_REQUIRED")
        self.assertEqual(result["review_url"], REVIEW)

    def test_cli_requires_operator_flag_and_does_not_overwrite(self):
        cmd = [sys.executable, str(ROOT / "scripts" / "reviewed_memory.py"),
               "record", "--repo", str(self.root), "--issue", ISSUE,
               "--review-url", REVIEW, "--kind", "DECISION",
               "--summary", SUMMARY, "--ref", REF, "--file", str(self.file)]
        denied = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(denied.returncode, 2, denied.stderr)
        self.assertFalse(self.file.exists())
        approved = subprocess.run(cmd + ["--operator-reviewed"], capture_output=True, text=True)
        self.assertEqual(approved.returncode, 0, approved.stderr)
        self.assertEqual(json.loads(approved.stdout)["decision"], "RECORDED_UNVERIFIED")
        self.assertEqual(subprocess.run(cmd + ["--operator-reviewed"], capture_output=True).returncode, 2)
        read = subprocess.run([sys.executable, str(ROOT / "scripts" / "reviewed_memory.py"),
                               "read", "--repo", str(self.root), "--file", str(self.file)],
                              capture_output=True, text=True)
        self.assertEqual(read.returncode, 2)
        self.assertEqual(json.loads(read.stdout)["decision"], "REVIEW_REQUIRED")

    def test_secret_cross_project_and_forged_review_rejection(self):
        examples = (
            "The api_key is available in this note.",
            "Token " + ("g" + "h" + "p" + "_") + "abcdefghijklmnopqrstuvwxyz0123456789 was exposed.",
            "Look at /home/user/.config/config.json to continue.",
            "See C:\\Users\\Name\\secret.json for the session.",
            "alice@example.com can grant the permission.",
            "A line with\nnew content isn't allowed.",
            "https://other.example.com has instructions.",
        )
        for example in examples:
            with self.subTest(example=example):
                with self.assertRaises(ValueError):
                    self.record(summary=example)
        with self.assertRaises(ValueError):
            memory.prepare_record(self.root, ISSUE,
                "https://github.com/other/repo/issues/11#issuecomment-38",
                "DECISION", SUMMARY, [])
        with self.assertRaises(ValueError):
            memory.prepare_record(self.root, ISSUE, REVIEW, "DECISION", SUMMARY,
                                  ["https://github.com/other/repo/issues/1"])
        with self.assertRaises(ValueError):
            memory.prepare_record(self.root, ISSUE, REVIEW, "SHELL_EXEC", SUMMARY, [])
        self.assertEqual(list(self.folder.iterdir()), [])

    def test_tampered_record_and_false_approval_fail_closed(self):
        packet = self.record()
        self.assertEqual(memory.verify_record(self.root, {**packet, "summary": "Changed decision summary"})["reason"],
                         "TAMPERED_REVIEWED_MEMORY")
        forged = {**packet, "owner_approval": "GRANTED"}
        forged["sha256"] = memory.handoff._handoff_digest(forged)
        self.assertEqual(memory.verify_record(self.root, forged)["reason"],
                         "INVALID_REVIEWED_MEMORY")
        unknown = {**packet, "extra": "OWNER_PRIVATE_FIXTURE"}
        self.assertEqual(memory.verify_record(self.root, unknown)["decision"], "BLOCKED")
        self.git("remote", "set-url", "origin", "https://github.com/foreign/repository.git")
        self.assertEqual(memory.verify_record(self.root, packet)["decision"], "BLOCKED")

    def test_search_exact_issue_and_fail_closed_storage(self):
        packet = self.record()
        memory.handoff._capture_handoff_file(self.file, packet)
        matches = memory.search_records(self.root, self.folder, ISSUE)
        self.assertEqual(matches["found_count"], 1)
        self.assertEqual(matches["matches"][0]["review_url"], REVIEW)
        self.assertEqual(matches["decision"], "REVIEW_REQUIRED")
        self.assertNotIn(str(self.folder), json.dumps(matches))
        no_match = memory.search_records(self.root, self.folder,
                          "https://github.com/example/toolkit-demo/issues/99")
        self.assertEqual(no_match["found_count"], 0)
        (self.folder / "unexpected.txt").write_text("OWNER_PRIVATE_FIXTURE")
        with self.assertRaises(ValueError):
            memory.search_records(self.root, self.folder, ISSUE)
        (self.folder / "unexpected.txt").unlink()
        memory.handoff._capture_handoff_file(self.folder / "review-two.json", packet)
        with self.assertRaises(ValueError):
            memory.search_records(self.root, self.folder, ISSUE)

    def test_symlink_inside_checkout_malformed_and_foreign_entry_denied(self):
        packet = self.record()
        in_repo = self.root / "private.json"
        with self.assertRaises(ValueError):
            memory._file(self.root, in_repo, create=True)
        memory.handoff._capture_handoff_file(self.file, packet)
        link = self.folder / "linked.json"
        try:
            link.symlink_to(self.file)
        except (OSError, NotImplementedError):
            self.skipTest("symlink unsupported on this platform")
        with self.assertRaises(ValueError):
            memory.search_records(self.root, self.folder, ISSUE)
        link.unlink()
        self.file.write_text('{"data": "malformed"}', encoding="utf-8")
        self.assertEqual(memory.read_record(self.root, self.file)["decision"], "BLOCKED")
        with self.assertRaises(ValueError):
            memory.search_records(self.root, self.folder, ISSUE)

    def test_mcp_preview_read_search_all_read_only_and_strict(self):
        names = {t["name"]: t for t in mcp._tool_defs()}
        for name in ("toolkit_prepare_reviewed_memory",
                     "toolkit_read_reviewed_memory",
                     "toolkit_search_reviewed_memory"):
            self.assertTrue(names[name]["annotations"]["readOnlyHint"])
            self.assertFalse(names[name]["inputSchema"]["additionalProperties"])
        args = dict(project=str(self.root), issue_url=ISSUE, review_url=REVIEW,
                    kind="DECISION", summary=SUMMARY, references=[REF])
        prepared = self._invoke("toolkit_prepare_reviewed_memory", **args)
        self.assertFalse(prepared["result"].get("isError", False), prepared)
        payload = prepared["result"]["structuredContent"]
        self.assertEqual(payload["storage"], "NOT_PERSISTED")
        self.assertFalse(list(self.folder.iterdir()))
        memory.handoff._capture_handoff_file(self.file, payload["record"])
        read = self._invoke("toolkit_read_reviewed_memory",
                            project=str(self.root), file=str(self.file))
        self.assertEqual(read["result"]["structuredContent"]["decision"], "REVIEW_REQUIRED")
        search = self._invoke("toolkit_search_reviewed_memory",
                              project=str(self.root), directory=str(self.folder), issue_url=ISSUE)
        self.assertEqual(search["result"]["structuredContent"]["found_count"], 1)
        bad = self._invoke("toolkit_prepare_reviewed_memory", **{**args, "save": True})
        self.assertTrue(bad["result"]["isError"])
        self.assertFalse((self.root / ".adt").exists())

    def test_mcp_cross_checkout_manual_transfer_requires_review(self):
        memory.handoff._capture_handoff_file(self.file, self.record())
        another = Path(self.temp.name) / "different-machine-repo"
        shutil.copytree(self.root, another, copy_function=shutil.copyfile)
        copied = self._invoke("toolkit_read_reviewed_memory",
                              project=str(another), file=str(self.file))
        response = copied["result"]["structuredContent"]
        self.assertEqual(response["decision"], "REVIEW_REQUIRED")
        self.assertEqual(response["review_attestation"], "NOT_VERIFIED")
        self.assertEqual(response["owner_approval"], "NOT_GRANTED")
        self.assertEqual(response["next_action"], "REVIEW_ISSUE")
        self.assertNotIn(str(another), json.dumps(response))
        found = self._invoke("toolkit_search_reviewed_memory",
                             project=str(another), directory=str(self.folder), issue_url=ISSUE)
        self.assertEqual(found["result"]["structuredContent"]["found_count"], 1)
        subprocess.run(["git", "-C", str(another), "remote", "set-url", "origin",
                        "https://github.com/other/repo.git"], check=True, capture_output=True)
        denied = self._invoke("toolkit_read_reviewed_memory",
                              project=str(another), file=str(self.file))
        self.assertEqual(denied["result"]["structuredContent"]["decision"], "BLOCKED")
        self.assertEqual(denied["result"]["structuredContent"]["owner_approval"], "NOT_GRANTED")


    def test_explicit_reference_types_schema_and_parent_traversal_rejected(self):
        for references in ([{"url": REF}], [REF, ["nested"]], (REF,)):
            with self.subTest(references=references):
                with self.assertRaises(ValueError):
                    memory.prepare_record(self.root, ISSUE, REVIEW, "DECISION", SUMMARY, references)
        forged = self.record()
        forged["schema"] = True
        forged["sha256"] = memory.handoff._handoff_digest(forged)
        self.assertEqual(memory.verify_record(self.root, forged),
                         {"decision": "BLOCKED", "reason": "INVALID_REVIEWED_MEMORY"})
        file_with_traversal = self.folder / ".." / self.folder.name / "review-one.json"
        with self.assertRaises(ValueError):
            memory._file(self.root, file_with_traversal, create=True)
        with self.assertRaises(ValueError):
            memory._directory(self.root, self.folder / ".." / self.folder.name)
        self.assertFalse(self.file.exists())

    def test_malformed_json_and_digest_rejected_by_read_and_search(self):
        record = self.record()
        memory.handoff._capture_handoff_file(self.file, record)
        record["sha256"] = "0" * 64
        self.file.write_text(json.dumps(record), encoding="utf-8")
        self.assertEqual(memory.read_record(self.root, self.file)["reason"],
                         "TAMPERED_REVIEWED_MEMORY")
        self.file.write_text("{malformed-json", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            memory.read_record(self.root, self.file)
        with self.assertRaises(ValueError):
            memory.search_records(self.root, self.folder, ISSUE)

    def test_cli_full_reviewed_reference_lifecycle_stays_untrusted(self):
        cli = [sys.executable, str(ROOT / "scripts" / "reviewed_memory.py")]
        fields = ["--repo", str(self.root), "--issue", ISSUE, "--review-url", REVIEW,
                  "--kind", "DECISION", "--summary", SUMMARY, "--ref", REF]
        prepared = subprocess.run(cli + ["prepare"] + fields, capture_output=True, text=True)
        self.assertEqual(prepared.returncode, 2, prepared.stderr)
        preview = json.loads(prepared.stdout)
        self.assertEqual(preview["storage"], "NOT_PERSISTED")
        self.assertFalse(self.file.exists())
        stored = subprocess.run(cli + ["record"] + fields +
                                ["--file", str(self.file), "--operator-reviewed"],
                                capture_output=True, text=True)
        self.assertEqual(stored.returncode, 0, stored.stderr)
        loaded = subprocess.run(cli + ["read", "--repo", str(self.root),
                                       "--file", str(self.file)], capture_output=True, text=True)
        self.assertEqual(loaded.returncode, 2, loaded.stderr)
        self.assertEqual(json.loads(loaded.stdout)["decision"], "REVIEW_REQUIRED")
        searched = subprocess.run(cli + ["search", "--repo", str(self.root),
                                         "--directory", str(self.folder), "--issue", ISSUE],
                                  capture_output=True, text=True)
        self.assertEqual(searched.returncode, 2, searched.stderr)
        self.assertEqual(json.loads(searched.stdout)["found_count"], 1)
        verified = memory.verify_record(self.root, json.loads(self.file.read_text()))
        self.assertEqual(verified["decision"], "REVIEW_REQUIRED")
        self.assertEqual(verified["owner_approval"], "NOT_GRANTED")
        self.assertEqual(verified["review_attestation"], "NOT_VERIFIED")

    @unittest.skipUnless(os.name == "nt", "Windows junction test")
    def test_windows_directory_junction_rejected(self):
        junction = Path(self.temp.name) / "linked-memory"
        process = subprocess.run(["cmd", "/c", "mklink", "/J", str(junction),
                                  str(self.folder)], capture_output=True, text=True)
        if process.returncode != 0:
            self.skipTest("Junction creation unavailable in CI")
        try:
            with self.assertRaises(ValueError):
                memory._directory(self.root, junction)
            with self.assertRaises(ValueError):
                memory._file(self.root, junction / "record.json", create=True)
        finally:
            junction.rmdir()

if __name__ == "__main__":
    unittest.main()
