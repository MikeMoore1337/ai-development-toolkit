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

    def test_owner_amendment_pins_new_bytes_and_preserves_original(self):
        import hashlib
        self._approve_fixture()
        path = ".agents/skills/original/SKILL.md"
        original_hash = self.data["owner_review_record"]["approved_components"][
            ".agents/skills/original"][path]
        self._put(path, (self.root / path).read_text(encoding="utf-8") + "reapproved revision\n")
        changed_hash = hashlib.sha256(canonical_bytes((self.root / path).read_bytes())).hexdigest()
        self.data["owner_review_amendments"] = [{
            "parent_review_id": "SYNTHETIC", "scope_issue": "#45",
            "source": "owner_reported", "review_outcomes": "permitted",
            "approved_files": {path: changed_hash},
        }]
        self.write()
        self.assertTrue(validate(self.root, "release")["ok"])
        self.assertEqual(original_hash, self.data["owner_review_record"][
            "approved_components"][".agents/skills/original"][path])
        self._put(path, (self.root / path).read_text(encoding="utf-8") + "unapproved\n")
        self.check("OWNER_FINGERPRINT", mode="release")

    def test_chained_owner_reapproval_requires_previous_sha(self):
        import hashlib
        self._approve_fixture()
        path = ".agents/skills/original/SKILL.md"
        self._put(path, "first approved revision\n")
        first = hashlib.sha256(canonical_bytes((self.root / path).read_bytes())).hexdigest()
        self._put(path, "second approved revision\n")
        second = hashlib.sha256(canonical_bytes((self.root / path).read_bytes())).hexdigest()
        initial = {"parent_review_id": "SYNTHETIC", "scope_issue": "#45",
                   "source": "owner_reported", "review_outcomes": "permitted",
                   "approved_files": {path: first}}
        repeat = {"parent_review_id": "SYNTHETIC", "scope_issue": "#124",
                  "source": "owner_reported", "review_outcomes": "permitted",
                  "approved_files": {path: second},
                  "supersedes_files": {path: first}}
        self.data["owner_review_amendments"] = [initial, repeat]
        self.write()
        self.assertTrue(validate(self.root, "release")["ok"])
        repeat["supersedes_files"][path] = "0" * 64
        self.check("OWNER_CHAIN", mode="release")

    def test_reviewed_qa_reference_addition_and_scope_guard(self):
        import hashlib
        self._approve_fixture()
        folder = "extensions/qa/skills/qa-fixture"
        main = folder + "/SKILL.md"
        guide = folder + "/references/FIELD_GUIDE.md"
        self._put(main, "---\nname: qa-fixture\ndescription: Synthetic skill\n---\n")
        self._put(guide, "# Synthetic reference\n")
        manifest = json.loads((self.root / "MANIFEST.json").read_text())
        manifest["extension_packs"]["qa"] = {"skill_root": "extensions/qa/skills"}
        self._put("MANIFEST.json", json.dumps(manifest))
        item = component(folder, "skill", name="qa-fixture", origin="adapted",
                         license="NOASSERTION", source_reference="synthetic",
                         owner_approval_id="SYNTHETIC")
        self.data["components"].append(item)
        review = self.data["owner_review_record"]
        review["approved_components"][folder] = {
            main: hashlib.sha256(canonical_bytes((self.root / main).read_bytes())).hexdigest()
        }
        review["approved_metadata"][folder] = {
            "origin": "adapted", "license": "NOASSERTION",
            "status": "documented", "distribution": "included", "kind": "skill"}
        self.data["owner_review_amendments"] = [{
            "parent_review_id": "SYNTHETIC", "scope_issue": "#124",
            "source": "owner_reported", "review_outcomes": "permitted",
            "reported_at": "2026-10-21", "scope_description": "Synthetic review",
            "approved_files": {}, "added_files": {
                guide: hashlib.sha256(canonical_bytes((self.root / guide).read_bytes())).hexdigest()}}]
        self.write()
        self.assertTrue(validate(self.root, "release")["ok"])
        self._put(guide, "# changed without review\n")
        self.check("OWNER_FINGERPRINT", mode="release")
        self._put(guide, "# Synthetic reference\n")
        self._put(folder + "/references/UNKNOWN.md", "# unapproved\n")
        self.check("OWNER_SCOPE", mode="release")

    def test_reference_scope_cannot_add_new_role(self):
        self._approve_fixture()
        self.data["owner_review_amendments"] = [{
            "parent_review_id": "SYNTHETIC", "scope_issue": "#124",
            "source": "owner_reported", "review_outcomes": "permitted",
            "reported_at": "2026-10-21", "scope_description": "Synthetic attempted expansion",
            "approved_files": {}, "added_files": {
                "extensions/qa/roles/new-executable.md": "0" * 64}}]
        self.check("OWNER_AMENDMENT", mode="release")

    def test_owner_amendment_cannot_expand_path_scope(self):
        self._approve_fixture()
        self.data["owner_review_amendments"] = [{
            "parent_review_id": "SYNTHETIC", "scope_issue": "#45",
            "source": "owner_reported", "review_outcomes": "permitted",
            "approved_files": {".agents/skills/original/extra.md": "0" * 64},
        }]
        self.check("OWNER_AMENDMENT", mode="release")

    def test_owner_amendment_cannot_invent_permission(self):
        self._approve_fixture()
        self.data["owner_review_amendments"] = [{
            "parent_review_id": "OTHER", "scope_issue": "#45",
            "source": "owner_reported", "review_outcomes": "pending",
            "approved_files": {".agents/skills/original/SKILL.md": "0" * 64},
        }]
        self.check("OWNER_AMENDMENT", mode="release")

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

    def test_known_branding_path_requires_approval_even_if_labelled_original(self):
        file_path = "assets/branding/hero.png"
        self._put(file_path, "synthetic placeholder, not a real image")
        self.data["components"].append(component(
            file_path, "asset", origin="original", status="documented",
            license="MIT", distribution="included",
        ))
        self.check("OWNER_APPROVAL", mode="release")

    def test_known_branding_path_cannot_drop_owner_record_to_escape_gate(self):
        self._approve_fixture()
        file_path = "assets/branding/hero.png"
        self._put(file_path, "synthetic test only")
        self.data["components"].append(component(
            file_path, "asset", origin="original",
            status="documented", distribution="included",
        ))
        self.data["owner_review_record"] = None
        self.check("OWNER_APPROVAL", mode="release")

    def test_known_qa_role_path_requires_owner_review(self):
        file_path = "extensions/qa/roles/fixture.md"
        self._put(file_path, "# synthetic fixture\n")
        self.data["components"].append(component(
            file_path, "role", origin="original", status="documented",
            distribution="included",
        ))
        self.check("OWNER_APPROVAL", mode="release")

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

    def test_bad_license_type_on_adapted_entry_is_reported_not_crashed(self):
        self.data["components"][0].update(
            origin="adapted", source_reference="fixture-source", license=[]
        )
        self.check("LICENSE")

    def test_bad_license_type_on_verified_entry_is_reported_not_crashed(self):
        self.data["components"][0].update(
            status="verified", license=[],
            distribution_basis="independently confirmed by synthetic test",
        )
        self.check("LICENSE")

    def test_bad_owner_record_type_is_reported_not_crashed(self):
        self.data["owner_review_record"] = []
        path = "assets/branding/hero.png"
        self._put(path, "synthetic placeholder only")
        self.data["components"].append(component(path, "asset"))
        self.check("OWNER_RECORD", mode="release")

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
        self.assertEqual(82, result["skills"])
        self.assertGreater(result["total"], 100)


if __name__ == "__main__":
    unittest.main()
