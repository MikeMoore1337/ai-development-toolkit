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
from verify_checksums import canonical_bytes  # noqa: E402


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

    def test_owner_approval_required_for_unverified_derivatives(self):
        self.data["components"][0].update(
            origin="adapted", source_reference="synthetic-work-source"
        )
        self.check("OWNER_APPROVAL")

    def test_claiming_verified_external_code_cannot_avoid_owner_gate(self):
        self.data["components"][0].update(
            origin="redistributed",
            source_reference="synthetic-external-source",
            status="verified",
            distribution_basis="independently confirmed via fixture notice",
        )
        self.check("OWNER_APPROVAL", mode="release")

    def _approve_fixture(self):
        import hashlib
        path = ".agents/skills/original"
        file_path = path + "/SKILL.md"
        digest = hashlib.sha256(canonical_bytes((self.root / file_path).read_bytes())).hexdigest()
        self.data["components"][0].update(
            origin="adapted", source_reference="synthetic-work-source",
            owner_approval_id="SYNTHETIC", status="documented",
            distribution="included",
        )
        self.data["owner_review_record"] = {
            "id": "SYNTHETIC", "source": "owner_reported",
            "review_outcomes": "permitted",
            "approved_components": {path: {file_path: digest}},
            "approved_metadata": {path: {
                "origin": "adapted", "license": "MIT", "status": "documented",
                "distribution": "included", "kind": "skill",
            }},
        }
        self.write()

    def test_frozen_owner_scope_requires_matching_file_bytes(self):
        self._approve_fixture()
        self.assertTrue(validate(self.root, "release")["ok"])
        file_path = ".agents/skills/original/SKILL.md"
        self._put(file_path, (self.root / file_path).read_text(encoding="utf-8") + "modified\n")
        result = validate(self.root, "release")
        self.assertTrue(any(e.startswith("OWNER_FINGERPRINT:") for e in result["issues"]), result)

    def test_frozen_owner_scope_rejects_new_files(self):
        self._approve_fixture()
        self._put(".agents/skills/original/extra.md", "New private fragment\n")
        self.check("OWNER_SCOPE", mode="release")

    def test_missing_frozen_review_snapshot_fails_closed(self):
        self._approve_fixture()
        self.data["owner_review_record"]["approved_components"] = {}
        self.check("OWNER_SCOPE", mode="release")

    def test_unrecognised_owner_id_fails_closed(self):
        self._approve_fixture()
        self.data["components"][0]["owner_approval_id"] = "NOT_THE_APPROVAL"
        self.check("OWNER_APPROVAL", mode="release")

    def test_relabel_approved_adaptation_as_original_does_not_bypass(self):
        self._approve_fixture()
        self.data["components"][0]["origin"] = "original"
        self.check("OWNER_CLASSIFICATION", mode="release")

    def test_relabel_approved_item_verified_does_not_bypass(self):
        self._approve_fixture()
        self.data["components"][0]["status"] = "verified"
        self.check("OWNER_CLASSIFICATION", mode="release")

    def test_change_approved_license_must_be_reviewed(self):
        self._approve_fixture()
        self.data["components"][0]["license"] = "Apache-2.0"
        self.check("OWNER_CLASSIFICATION", mode="release")

    def test_relabelled_metadata_cannot_bypass_changed_content(self):
        self._approve_fixture()
        self.data["components"][0]["origin"] = "original"
        file_path = ".agents/skills/original/SKILL.md"
        self._put(file_path, (self.root / file_path).read_text() + "injection\n")
        self.check("OWNER_FINGERPRINT", mode="release")

    def test_owner_metadata_snapshot_is_required(self):
        self._approve_fixture()
        self.data["owner_review_record"].pop("approved_metadata")
        self.check("OWNER_CLASSIFICATION", mode="release")

    def test_owner_metadata_snapshot_cannot_be_partial(self):
        self._approve_fixture()
        self.data["owner_review_record"]["approved_metadata"] = {}
        self.check("OWNER_CLASSIFICATION", mode="release")

    def test_malformed_registry_entry_ids_and_paths_are_reported(self):
        self.data["components"][0]["id"] = []
        self.check("ID")
        self.data["components"][0]["id"] = "fixture"
        self.data["components"][0]["path"] = {}
        self.check("SCHEMA")

    def test_invalid_enum_values_are_reported_not_crashed(self):
        self.data["components"][0]["origin"] = []
        self.check("ORIGIN")
        self.data["components"][0]["origin"] = "original"
        self.data["components"][0]["status"] = []
        self.check("STATUS")

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlinks unsupported")
    def test_nested_symlink_is_rejected(self):
        # Symlink permissions on Windows CI vary; skip only on OS refusal.
        import os
        alias = self.root / ".agents/skills/original/linked.md"
        try:
            alias.symlink_to(self.root / "NOTICE.md")
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks are not permitted on this runner")
        self.check("SYMLINK", mode="release")

    def test_current_tree_release_snapshot_is_eligible(self):
        result = validate(ROOT, "release")
        self.assertTrue(result["ok"], result["issues"][:15])
        self.assertEqual(0, result["counts"].get("verified", 0))

    def test_real_repository_inventory(self):
        result = validate(ROOT)
        self.assertTrue(result["ok"], result["issues"][:12])
        self.assertEqual(51, result["skills"])
        self.assertGreater(result["total"], 100)


if __name__ == "__main__":
    unittest.main()
