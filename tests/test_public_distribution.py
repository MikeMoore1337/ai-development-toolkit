import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_pack import inspect

PONYTAIL_BLOBS = {
    "ponytail": "d64edd32265ba21cbf5270158f04e97d96925f27",
    "ponytail-review": "a50e3ac6ded6fccc9edae34ce37877bbce11e3fa",
    "ponytail-audit": "ff9a95480700600fe2664d2d0906a4d750b2da0b",
    "ponytail-debt": "3124f520a65d2a4fa75a2f5db6225c38ebdb8620",
    "ponytail-gain": "1edff0e461fad6b671733ea6796aea9e417e266b",
    "ponytail-help": "34fccb3ff542b3b8d4d131e6120a1812c9c4617a",
}
PONYTAIL_LICENSE_BLOB = "715d483338cea4365f0d91a27799cf61226d6bcf"


def git_blob_sha(path):
    # Canonicalize Git-managed text: Windows may check out the upstream MIT LICENSE with CRLF.
    content = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


class DistributionTests(unittest.TestCase):
    def test_pack_validation(self):
        self.assertEqual([], inspect())

    def test_only_pinned_optional_originals(self):
        directory = ROOT / "third_party" / "ponytail-v5.3.2" / "skills"
        self.assertEqual(
            sorted(PONYTAIL_BLOBS),
            sorted(p.name for p in directory.iterdir() if p.is_dir()),
        )
        for name, expected_sha in PONYTAIL_BLOBS.items():
            with self.subTest(skill=name):
                path = directory / name / "SKILL.md"
                self.assertEqual(expected_sha, git_blob_sha(path))
        self.assertEqual(
            PONYTAIL_LICENSE_BLOB,
            git_blob_sha(ROOT / "third_party" / "ponytail-v5.3.2" / "LICENSE"),
        )

    def test_public_manifest(self):
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertTrue(manifest["make_feature_source_bundled"])
        self.assertEqual(7, manifest["original_skills_bundled_as_opt_in"])
        self.assertEqual({"contract-first", "api-connector-builder", "code-tour", "module-regression", "error-handling", "mcp-dependency-review"},
                         set(manifest["extension_packs"]["native-ecc-ports"]["skills"]) - {"windows-desktop-e2e"})
        self.assertEqual(
            "16352ac229eb08a9598dcae48fe9f2b342567d86",
            manifest["source_revision_pins"]["DietrichGebert/ponytail"],
        )

    def test_private_archive_absent(self):
        self.assertFalse(list(ROOT.rglob("make-feature-0.3.0*.gz")))
        self.assertFalse((ROOT / "make-feature").exists())


if __name__ == "__main__":
    unittest.main()
