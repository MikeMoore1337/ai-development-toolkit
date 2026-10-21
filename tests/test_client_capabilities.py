"""Offline Issue #68 contract checks - no model sessions or external operations."""
from __future__ import annotations

import copy
import json
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import client_capabilities as cap


class ClientCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def registry(self, change=None):
        data = json.loads(cap.REGISTRY.read_text(encoding="utf-8"))
        if change:
            change(data)
        path = self.folder / "registry.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_two_conversational_clients_and_no_fake_layout(self):
        registry = cap.load_conversations()
        self.assertEqual({"chatgpt", "claude-ai"}, {
            x["client_id"] for x in registry["clients"]})
        for row in registry["clients"]:
            self.assertNotIn("supported_skill_layouts", row)
            self.assertEqual("CONVERSATIONAL_REFERENCE_CLIENT", row["client_type"])
            self.assertEqual("OWNER_REPORTED_PASS",
                             row["scenarios"]["zip_plus_toolkit_url"])
            self.assertEqual("NOT_TESTED", row["evidence"]["L5"])
            self.assertEqual("NOT_MEASURED", row["evidence"]["L6"])

    def test_bad_registry_fails_closed(self):
        corruptions = (
            ("schema", lambda d: d.update(schema_version=2)),
            ("duplicated", lambda d: d["clients"][1].update(client_id="chatgpt")),
            ("Unknown", lambda d: d["clients"][0].update(client_id="new-ai")),
            ("filesystem", lambda d: d["clients"][0].update(
                client_type="FILESYSTEM_SKILL_CLIENT")),
            ("fields", lambda d: d["clients"][0].update(
                supported_skill_layouts=[".agents/skills"])),
            ("official", lambda d: d["clients"][0].update(
                documentation_url="https://example.org/skills")),
            ("capability", lambda d: d["clients"][0]["capabilities"].update(
                terminal="ENABLED")),
            ("session", lambda d: d["clients"][0]["capabilities"].update(
                terminal="AVAILABLE")),
            ("L4-L6", lambda d: d["clients"][0]["evidence"].update(
                L4="VERIFIED")),
            ("L4-L6", lambda d: d["clients"][0]["evidence"].update(
                L5="VERIFIED")),
            ("L4-L6", lambda d: d["clients"][0]["evidence"].update(
                L6="VERIFIED")),
            ("owner-reported", lambda d: d["clients"][0]["scenarios"].update(
                zip_plus_toolkit_url="VERIFIED")),
        )
        for name, mutation in corruptions:
            with self.subTest(name=name), self.assertRaisesRegex(
                    cap.CapabilityError, name):
                cap.load_conversations(self.registry(mutation))

    def caps(self, **changes):
        values = dict.fromkeys(cap.CAPABILITIES, "UNKNOWN")
        values.update(changes)
        return values

    def test_route_capabilities_and_no_automatic_install(self):
        cases = [
            ("FILESYSTEM_SKILL_CLIENT", self.caps(
                file_read="AVAILABLE", skill_discovery="AVAILABLE"),
             {"installed_skill": True}, "NATIVE_FILESYSTEM_SKILL"),
            (cap.CLIENT_TYPE, self.caps(
                toolkit_access="AVAILABLE", file_read="AVAILABLE"),
             {"toolkit_url": True}, "TOOLKIT_REFERENCE"),
            (cap.CLIENT_TYPE, self.caps(
                attachments="AVAILABLE", file_read="AVAILABLE"),
             {"toolkit_attachment": True}, "ATTACHMENT_GUIDANCE"),
            (cap.CLIENT_TYPE, self.caps(),
             {"toolkit_url": True}, "MANUAL_FALLBACK"),
            (cap.CLIENT_TYPE, self.caps(
                file_read="AVAILABLE", skill_discovery="AVAILABLE"),
             {"installed_skill": True}, "MANUAL_FALLBACK"),
            ("FILESYSTEM_SKILL_CLIENT", self.caps(
                skill_discovery="AVAILABLE"),
             {"installed_skill": True}, "MANUAL_FALLBACK"),
        ]
        for client_type, capabilities, options, expected in cases:
            with self.subTest(expected=expected, client_type=client_type):
                result = cap.select_route(client_type, capabilities, **options)
                self.assertEqual(expected, result["route"])
                self.assertFalse(result["skill_invoked"])
                self.assertFalse(result["tests_executed"])
        self.assertEqual("ATTACHMENT_UNAVAILABLE",
                         cap.select_route(cap.CLIENT_TYPE, self.caps(),
                                          project_archive=True)["project_archive_status"])
        with self.assertRaisesRegex(cap.CapabilityError, "Unknown client"):
            cap.select_route("UNKNOWN", self.caps())

    def claim(self, **changes):
        base = {
            "route": "MANUAL_FALLBACK",
            "read_source": False, "attachment_read": False,
            "files_written": False, "write_access": False,
            "tests_run": False, "test_evidence": "",
            "skill_discovered": False, "discovery_evidence": "",
            "skill_invoked": False, "invocation_evidence": "",
            "measured_effectiveness": False, "baseline_evidence": "",
            "model_called": False, "model_evidence": "",
            "separate_agent": False, "separate_agent_evidence": "",
            "paid_api_calls": 0, "approved_install": False,
            "installed": False, "owner_report_only": False,
        }
        base.update(changes)
        return base

    def test_valid_claims_pass_and_false_claims_fail(self):
        cap.validate_execution_claim(self.claim())
        cap.validate_execution_claim(self.claim(
            route="TOOLKIT_REFERENCE", read_source=True))
        cap.validate_execution_claim(self.claim(
            route="ATTACHMENT_GUIDANCE", attachment_read=True))
        cap.validate_execution_claim(self.claim(
            route="NATIVE_FILESYSTEM_SKILL", installed=True,
            approved_install=True, skill_discovered=True,
            discovery_evidence="Actual client log supplied"))
        bad = [
            ("False native discovery", {"route": "NATIVE_FILESYSTEM_SKILL"}),
            ("Toolkit source", {"route": "TOOLKIT_REFERENCE"}),
            ("Attachment", {"route": "ATTACHMENT_GUIDANCE"}),
            ("False write", {"files_written": True}),
            ("Tests not run", {"tests_run": True}),
            ("False skill discovery", {"skill_discovered": True}),
            ("False skill invocation", {"skill_invoked": True}),
            ("False model effectiveness", {"measured_effectiveness": True}),
            ("False model call", {"model_called": True}),
            ("Fake subagent", {"separate_agent": True}),
            ("Paid API", {"paid_api_calls": 1}),
            ("Installation", {"installed": True}),
            ("Owner report", {"owner_report_only": True,
                              "skill_discovered": True,
                              "discovery_evidence": "Test",
                              "skill_invoked": True,
                              "invocation_evidence": "Test"}),
        ]
        for message, mutation in bad:
            with self.subTest(message=message), self.assertRaisesRegex(
                    cap.CapabilityError, message):
                cap.validate_execution_claim(self.claim(**mutation))

    def zip(self, entries, name="project.zip"):
        path = self.folder / name
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for entry, content in entries:
                z.writestr(entry, content)
        return path

    def test_safe_zip_preflight_read_only(self):
        project = self.zip([("src/main.py", "print(1)\n"),
                            ("README.md", "offline fixture\n")])
        before = project.read_bytes()
        report = cap.inspect_zip(project)
        self.assertEqual("ZIP_PREFLIGHT_PASS", report["status"])
        self.assertEqual(2, report["entries"])
        self.assertFalse(report["extracted"])
        self.assertEqual(before, project.read_bytes())
        self.assertEqual({"project.zip"}, {x.name for x in self.folder.iterdir()})

    def test_zip_negative_oracle(self):
        link = zipfile.ZipInfo("src/link")
        link.create_system = 3
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        cases = [
            ("path traversal", [("../escape.py", "bad")]),
            ("path traversal", [("/absolute.py", "bad")]),
            ("path traversal", [("C:/windows/x", "bad")]),
            ("Duplicate", [("File.py", "1"), ("file.py", "2")]),
            ("Linked", [(link, "target")]),
            ("secrets", [(".env", "private")]),
            ("secrets", [("id_rsa", "private")]),
            ("Nested", [("nested.zip", "archive")]),
        ]
        for i, (message, entries) in enumerate(cases):
            with self.subTest(i=i), self.assertRaisesRegex(
                    cap.CapabilityError, message):
                cap.inspect_zip(self.zip(entries, f"bad-{i}.zip"))
        # Inject a literal backslash into both ZIP headers. On Windows,
        # zipfile.writestr normalizes names, making a naive fixture a false negative.
        malformed = self.zip([("a/b.txt", "bad")], "backslash.zip")
        archive_bytes = malformed.read_bytes()
        self.assertEqual(2, archive_bytes.count(b"a/b.txt"))
        malformed.write_bytes(archive_bytes.replace(b"a/b.txt", b"a\\b.txt"))
        with self.assertRaisesRegex(cap.CapabilityError, "path traversal"):
            cap.inspect_zip(malformed)
        with self.assertRaisesRegex(cap.CapabilityError, "Empty ZIP"):
            cap.inspect_zip(self.zip([], "empty.zip"))
        corrupt = self.folder / "corrupt.zip"
        corrupt.write_bytes(b"Not an archive")
        with self.assertRaisesRegex(cap.CapabilityError, "Corrupted ZIP"):
            cap.inspect_zip(corrupt)
        with self.assertRaisesRegex(cap.CapabilityError, "ATTACHMENT_UNAVAILABLE"):
            cap.inspect_zip(self.folder / "missing.zip")
        with self.assertRaisesRegex(cap.CapabilityError, "safe limit"):
            cap.inspect_zip(self.zip([("x" + str(i), "x")
                                      for i in range(cap.MAX_ENTRIES + 1)],
                                     "too-many.zip"))

    def test_zip_expansion_bomb_refused(self):
        bomb = self.zip([("big.txt", "x" * (cap.MAX_RATIO * 1024))],
                        "compression.zip")
        with self.assertRaisesRegex(cap.CapabilityError, "expansion"):
            cap.inspect_zip(bomb)


if __name__ == "__main__":
    unittest.main()
