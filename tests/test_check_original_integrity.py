"""Offline regression for the original-source integrity gate (Issue #524)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_original_integrity", ROOT / "scripts/check_original_integrity.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class OriginalIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.skill = self.root / "SKILL.md"
        self.skill.write_text("---\nname: synthetic-original\n---\n", encoding="utf-8")
        self.revision = "a" * 40
        self.manifest = {"repo": "example/original", "commit": self.revision,
                         "source": "skills/original", "files": [self.entry("SKILL.md")]}
        self.write_manifest()

    def entry(self, name):
        contents = (self.root / name).read_bytes()
        return {"path": name, "sha256": hashlib.sha256(contents).hexdigest(), "bytes": len(contents)}

    def write_manifest(self):
        (self.root / "UPSTREAM.json").write_text(json.dumps(self.manifest), encoding="utf-8")

    def check(self, expected_commit=None):
        return checker.verify(self.root, expected_repo="example/original", expected_commit=expected_commit)

    def test_consistent_does_not_claim_upstream_identity(self):
        original = self.skill.read_bytes()
        result = self.check(self.revision)
        self.assertEqual("CONSISTENT_WITH_LOCAL_MANIFEST", result["status"])
        self.assertEqual(1, result["files_matched"])
        self.assertFalse(result["upstream_identity_verified"])
        self.assertEqual(original, self.skill.read_bytes())

    def test_modified_skill_is_detected(self):
        self.skill.write_text("modified", encoding="utf-8")
        result = self.check(self.revision)
        self.assertEqual("SOURCE_DRIFT", result["status"])
        self.assertEqual(["SKILL.md"], result["mismatches"])

    def test_missing_manifest_is_unattested(self):
        (self.root / "UPSTREAM.json").unlink()
        self.assertEqual("NO_LOCAL_MANIFEST", self.check()["status"])

    def test_wrong_revision_is_detected(self):
        self.assertEqual("SOURCE_DRIFT", self.check("b"*40)["status"])

    def test_unsafe_or_duplicate_paths_are_rejected(self):
        for bad in ("../outside.md", "/outside.md", "./SKILL.md", "sub\\SKILL.md"):
            with self.subTest(path=bad):
                self.manifest["files"].append({"path": bad, "sha256": "0"*64, "bytes": 0})
                self.write_manifest()
                self.assertEqual("SOURCE_DRIFT", self.check()["status"])
                self.manifest["files"].pop()
        self.manifest["files"].append(self.entry("SKILL.md"))
        self.write_manifest()
        self.assertEqual("SOURCE_DRIFT", self.check()["status"])

    def test_references_require_check_before_originality_claim(self):
        source = (ROOT / "integrations/chatgpt-plugin/ai-development-toolkit/skills/toolkit-ui-review/references/ORIGINALS.md").read_text(encoding="utf-8")
        for phrase in ("check_original_integrity.py", "SOURCE_DRIFT", "originality", "independently verified", "Verified-source failover", "pristine source copy", "original entrypoint", "not** the original blind run"):
            self.assertIn(phrase, source)


if __name__ == "__main__":
    unittest.main()
