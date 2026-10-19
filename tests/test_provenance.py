"""Deterministic provenance validation: negative cases use synthetic, non-private files."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_provenance import validate  # noqa: E402


def component(path: str, kind: str = "metadata", **overrides) -> dict:
    data = dict(
        id="component-" + path.replace("/", "-").replace(".", "-").lower(),
        path=path, name=path.rsplit("/", 1)[-1], kind=kind,
        author="Fixture contributors", origin="original", source_url=None,
        source_reference=None, source_revision=None, license="MIT",
        distribution_basis="Claimed authorship; not independently verified",
        attribution_required=False, attribution_path=None, status="documented",
        evidence="NOTICE.md", last_reviewed="2026-10-19",
        distribution="included", notes="Synthetic fixture",
    )
    data.update(overrides)
    return data


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self._put("MANIFEST.json", json.dumps({
            "skill_root": ".agents/skills", "extension_packs": {},
        }))
        self._put("NOTICE.md", "Synthetic evidence, NOT a permission grant.\n")
        self._put(".agents/skills/original/SKILL.md",
                  "---\nname: original\ndescription: Fixture\nlicense: MIT\n---\n\nHello\n")
        self.data = {"schema_version": 1, "components": [
            component(".agents/skills/original", "skill"),
            component("MANIFEST.json"),
            component("NOTICE.md"),
            component("provenance/skills.json"),
        ]}
        self.write()

    def _put(self, path, content):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    def write(self):
        self._put("provenance/skills.json", json.dumps(self.data))

    def check(self, code, mode="inventory"):
        self.write()
        result = validate(self.root, mode)
        self.assertFalse(result["ok"])
        self.assertTrue(any(line.startswith(code + ":") for line in result["issues"]), result)
        return result

    def test_original_fixture_passes(self):
        self.assertTrue(validate(self.root)["ok"])

    def test_missing_skill_entry(self):
        self.data["components"].pop(0)
        self.check("UNDECLARED_SKILL")

    def test_extra_skill_entry(self):
        self._put(".agents/skills/undeclared/SKILL.md", "---\nname: undeclared\n---\n")
        self.data["components"].append(component(".agents/skills/undeclared", "skill"))
        self.data["components"].append(component("not-present/SKILL.md", "skill"))
        self.check("MISSING_PATH")

    def test_duplicate_id(self):
        self.data["components"][1]["id"] = self.data["components"][0]["id"]
        self.check("DUPLICATE_ID")

    def test_duplicate_path(self):
        self.data["components"].append(component("NOTICE.md", id="another-notice"))
        self.check("DUPLICATE_PATH")

    def test_missing_path(self):
        self.data["components"][0]["path"] = "missing/SKILL.md"
        self.check("MISSING_PATH")

    def test_invalid_revision(self):
        self.data["components"][0]["source_revision"] = "main"
        self.check("REVISION")

    def test_third_party_source_missing(self):
        self.data["components"][0]["origin"] = "redistributed"
        self.check("SOURCE_MISSING")

    def test_adapted_source_missing(self):
        self.data["components"][0]["origin"] = "adapted"
        self.check("SOURCE_MISSING")

    def test_missing_license(self):
        self.data["components"][0].update(origin="redistributed", source_reference="local archive",
                                          license="NONE")
        self.check("LICENSE_MISSING")

    def test_license_frontmatter_conflict(self):
        self.data["components"][0]["license"] = "Apache-2.0"
        self.check("LICENSE_CONFLICT")

    def test_restricted_in_release(self):
        self.data["components"][0].update(status="restricted", distribution="owner_gate")
        self.write()
        self.assertTrue(validate(self.root)["ok"])
        self.check("RELEASE_BLOCKED", mode="release")

    def test_unknown_does_not_become_verified(self):
        self.data["components"][0].update(origin="unknown", status="verified")
        self.check("FALSE_VERIFIED")

    def test_unsubstantiated_verified(self):
        self.data["components"][0]["status"] = "verified"
        self.check("FALSE_VERIFIED")

    def test_missing_required_attribution(self):
        self.data["components"][0]["attribution_required"] = True
        self.check("ATTRIBUTION")

    def test_missing_evidence_file(self):
        self.data["components"][0]["evidence"] = "gone.md"
        self.check("EVIDENCE_PATH")

    def test_unsafe_relative_path(self):
        self.data["components"][0]["path"] = "../outside"
        self.check("UNSAFE_PATH")

    def test_unsafe_windows_path(self):
        self.data["components"][0]["path"] = "C:\\private"
        self.check("UNSAFE_PATH")

    def test_corrupt_registry(self):
        self._put("provenance/skills.json", "{damaged")
        result = validate(self.root)
        self.assertFalse(result["ok"])
        self.assertTrue(result["issues"][0].startswith("REGISTRY:"))

    def test_missing_registry(self):
        (self.root / "provenance/skills.json").unlink()
        result = validate(self.root)
        self.assertFalse(result["ok"])

    def test_added_file_not_declared(self):
        self._put("scripts/new.py", "pass\n")
        self.check("UNDECLARED_FILE")

    def test_repeatable_result(self):
        self.write()
        self.assertEqual(validate(self.root), validate(self.root))

    def test_current_tree_release_is_owner_blocked(self):
        result = validate(ROOT, "release")
        self.assertFalse(result["ok"])
        self.assertTrue(any("make-feature" in issue and "RELEASE_BLOCKED" in issue
                            for issue in result["issues"]))
        self.assertTrue(any("extensions-qa" in issue and "RELEASE_BLOCKED" in issue
                            for issue in result["issues"]))

    def test_real_repository_inventory(self):
        result = validate(ROOT)
        self.assertTrue(result["ok"], result["issues"][:12])
        self.assertEqual(51, result["skills"])
        self.assertGreater(result["total"], 100)


if __name__ == "__main__":
    unittest.main()
