"""Synthetic, offline regressions for skill_quality_metrics. No skill code is executed."""
from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import skill_quality_metrics as metrics

BEFORE = "a" * 40
AFTER = "b" * 40
GOOD = "---\nname: alpha\ndescription: Minimal synthetic test skill.\n---\n\n# Alpha\nDo the work.\n"


class QualityMetricsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.folder = self.root / ".agents" / "skills" / "alpha"
        self.folder.mkdir(parents=True)
        self.file = self.folder / "SKILL.md"
        self.file.write_text(GOOD, encoding="utf-8")
        self.manifest = self.root / "MANIFEST.json"
        self.manifest.write_text(json.dumps({
            "core_skills": ["alpha"], "extension_skills": [],
            "extension_packs": {}, "profiles": {"test": ["alpha"]}
        }), encoding="utf-8")

    def report(self, revision=BEFORE):
        return metrics.collect(self.root, revision=revision)

    def test_valid_skill(self):
        report = self.report()
        self.assertEqual(report["status"], "PASS", report["skills"][0]["findings"])
        self.assertEqual(report["skill_count"], 1)
        self.assertEqual(report["structural_pass"], 1)
        one = report["skills"][0]
        self.assertEqual(one["context_footprint"]["skill_md_bytes"]["value"], self.file.stat().st_size)
        self.assertEqual(one["context_footprint"]["skill_md_words"]["value"], len(GOOD.split()))
        self.assertEqual(one["context_footprint"]["model_tokens"]["status"], "NOT_MEASURED")
        self.assertEqual(one["structural_validation"]["official_skills_ref"], "NOT_MEASURED")
        self.assertEqual(one["evidence_levels"]["source_validated"]["status"], "PASS")
        self.assertTrue(all(one["evidence_levels"][name]["status"] == "NOT_MEASURED"
                            for name in ("packaged", "installed", "discovered", "activated", "effective")))


    def test_missing_skill_md(self):
        self.file.unlink()
        report = self.report()
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(x["rule_id"] == "SKILL" for x in report["skills"][0]["findings"]))

    def test_malformed_frontmatter(self):
        self.file.write_text("---\nname: alpha\ndescription: x\nname: alpha\n---\n", encoding="utf-8")
        one = self.report()["skills"][0]
        self.assertEqual(one["structural_validation"]["status"], "FAIL")
        self.assertTrue(any(f["rule_id"] == "FRONTMATTER" for f in one["findings"]))

    def test_broken_reference(self):
        self.file.write_text(GOOD + "\n[missing](references/nope.md)\n", encoding="utf-8")
        self.assertTrue(any(f["rule_id"] == "LINK001" for f in self.report()["skills"][0]["findings"]), self.report()["skills"][0]["findings"])

    def test_unknown_skill_id(self):
        with self.assertRaisesRegex(metrics.MetricsError, "Unknown skill ID"):
            metrics.collect(self.root, "missing", BEFORE)

    def test_invalid_manifest_json(self):
        self.manifest.write_text("{broken", encoding="utf-8")
        with self.assertRaises(metrics.MetricsError):
            self.report()

    def test_manifest_duplicate(self):
        self.manifest.write_text(json.dumps({"core_skills": ["alpha", "alpha"]}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.report()

    def test_empty_skill(self):
        self.file.write_bytes(b"")
        one = self.report()["skills"][0]
        self.assertEqual(one["structural_validation"]["status"], "FAIL")
        self.assertEqual(one["context_footprint"]["skill_md_bytes"]["value"], 0)

    def test_no_optional_references(self):
        one = self.report()["skills"][0]
        self.assertEqual(one["context_footprint"]["reference_files"]["value"], 0)
        self.assertEqual(one["context_footprint"]["reference_bytes"]["value"], 0)

    def test_reference_count_and_bytes(self):
        ref = self.folder / "references" / "example.md"
        ref.parent.mkdir()
        ref.write_text("hello", encoding="utf-8")
        one = self.report()["skills"][0]
        self.assertEqual(one["context_footprint"]["reference_files"]["value"], 1)
        self.assertEqual(one["context_footprint"]["reference_bytes"]["value"], 5)

    def test_linked_resource_denied(self):
        external = self.root / "external.md"
        external.write_text("secret", encoding="utf-8")
        target = self.folder / "linked.md"
        try:
            target.symlink_to(external)
        except (OSError, NotImplementedError):
            self.skipTest("Symlinks unavailable on this Windows runner")
        self.assertEqual(self.report()["status"], "FAIL")
        self.assertTrue(any(f["rule_id"] == "PATH" for f in self.report()["skills"][0]["findings"]))

    def test_linked_skill_dir_denied(self):
        external = self.root / "other"
        external.mkdir()
        (external / "SKILL.md").write_text(GOOD, encoding="utf-8")
        original = self.folder
        self.file.unlink()
        original.rmdir()
        try:
            original.symlink_to(external, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Directory links unavailable on this runner")
        self.assertEqual(self.report()["status"], "FAIL")

    def test_parent_escape_link(self):
        self.file.write_text(GOOD + "\n[escape](../../../../outside.md)\n", encoding="utf-8")
        one = self.report()["skills"][0]
        self.assertTrue(any(f["rule_id"] == "PATH001" for f in one["findings"]))

    def test_absolute_extension_pack_path_rejected(self):
        self.manifest.write_text(json.dumps({
            "core_skills": ["alpha"], "extension_packs": {
                "bad": {"skill_root": str(self.root), "skills": ["beta"]}}
        }), encoding="utf-8")
        with self.assertRaisesRegex(metrics.MetricsError, "Unsafe"):
            self.report()

    def test_repeat_deterministic(self):
        first = metrics.json_bytes(self.report())
        second = metrics.json_bytes(self.report())
        self.assertEqual(first, second)

    def test_file_order_independent(self):
        (self.folder / "z.txt").write_text("Z", encoding="utf-8")
        (self.folder / "a.txt").write_text("A", encoding="utf-8")
        before = self.report()
        with patch.object(os, "walk", wraps=os.walk) as mocked:
            after = self.report()
        self.assertTrue(mocked.called)
        self.assertEqual(before, after)
        self.assertEqual([f["path"] for f in after["skills"][0]["file_inventory"]],
                         sorted(f["path"] for f in after["skills"][0]["file_inventory"]))

    def test_content_change_diff(self):
        before = self.report()
        self.file.write_text(GOOD + "\nNew safe instruction.\n", encoding="utf-8")
        changes = metrics.compare(before, self.report(AFTER))
        self.assertEqual(changes["status"], "PASS")
        kinds = {i["kind"] for x in changes["changes"] for i in x["indicators"]}
        self.assertIn("skill_instructions_changed", kinds)
        self.assertIn("instruction_size_delta", kinds)

    def test_reference_added_diff(self):
        before = self.report()
        (self.folder / "references").mkdir()
        (self.folder / "references" / "added.md").write_text("new", encoding="utf-8")
        kinds = {i["kind"] for x in metrics.compare(before, self.report(AFTER))["changes"] for i in x["indicators"]}
        self.assertIn("file_added", kinds)

    def test_reference_removed_diff(self):
        (self.folder / "references").mkdir()
        ref = self.folder / "references" / "removed.md"
        ref.write_text("before", encoding="utf-8")
        before = self.report()
        ref.unlink()
        kinds = {i["kind"] for x in metrics.compare(before, self.report(AFTER))["changes"] for i in x["indicators"]}
        self.assertIn("file_removed", kinds)

    def test_size_growth_is_not_failure(self):
        before = self.report()
        self.file.write_text(GOOD + ("Keep instructions precise.\n" * 200), encoding="utf-8")
        compared = metrics.compare(before, self.report(AFTER))
        self.assertEqual(compared["status"], "PASS")

    def test_new_broken_link_is_blocker(self):
        before = self.report()
        self.file.write_text(GOOD + "\n[broken](missing.md)\n", encoding="utf-8")
        compared = metrics.compare(before, self.report(AFTER))
        self.assertEqual(compared["status"], "FAIL", compared["changes"])
        self.assertIn("new_structural_failure", str(compared))

    def test_no_empirical_fabrication(self):
        result = self.report()["skills"][0]["empirical_effectiveness"]
        self.assertEqual(set(result), set(metrics.EMPIRICAL_FIELDS))
        self.assertTrue(all(v["status"] == "NOT_MEASURED" and v["value"] is None
                            for v in result.values()))

    def test_unknown_schema(self):
        original = self.report()
        original["schema_version"] = 1234
        with self.assertRaises(metrics.MetricsError):
            metrics.compare(original, self.report(AFTER))

    def test_invalid_baseline_json(self):
        broken = self.root / "baseline.json"
        broken.write_text("not json!", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            json.loads(broken.read_text(encoding="utf-8"))

    def test_unpinned_baseline(self):
        before = self.report()
        before["source_revision"] = None
        with self.assertRaises(metrics.MetricsError):
            metrics.compare(before, self.report(AFTER))

    def test_dirty_baseline_path_rejected(self):
        original = self.report()
        original["skills"][0]["file_inventory"][0]["path"] = "../leak"
        with self.assertRaises(metrics.MetricsError):
            metrics.compare(original, self.report(AFTER))

    def test_new_and_deleted_skill(self):
        before = self.report()
        beta = self.root / ".agents" / "skills" / "beta"
        beta.mkdir()
        (beta / "SKILL.md").write_text(GOOD.replace("alpha", "beta"), encoding="utf-8")
        self.manifest.write_text(json.dumps({"core_skills": ["alpha", "beta"]}), encoding="utf-8")
        candidate = self.report(AFTER)
        self.assertIn("skill_added", str(metrics.compare(before, candidate)))
        self.assertIn("skill_removed", str(metrics.compare(candidate, before)))

    def test_source_file_never_executed(self):
        p = self.folder / "scripts" / "malicious.py"
        p.parent.mkdir()
        marker = self.root / "would_execute"
        p.write_text(f"open({str(marker)!r}, 'w').write('danger')", encoding="utf-8")
        report = self.report()
        self.assertFalse(marker.exists())
        self.assertIn("executable_source", str(report))

    def test_repeat_attestation_requires_actual_check(self):
        one = self.report()["skills"][0]["reproducibility"]
        self.assertEqual(one["status"], "NOT_MEASURED")
        from unittest.mock import patch
        args = ["skill_quality_metrics.py", "--root", str(self.root),
                "--revision", BEFORE, "--check-repeat", "--json-report",
                str(self.root / "report.json")]
        with patch("sys.argv", args):
            self.assertEqual(metrics.main(), 0)
        actual = json.loads((self.root / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(actual["skills"][0]["reproducibility"]["status"], "PASS")
        self.assertEqual(actual["skills"][0]["reproducibility"]["repeat_measurement"], "PASS")

    def test_requires_valid_revision(self):
        with self.assertRaisesRegex(metrics.MetricsError, "full 40-hex"):
            metrics.collect(self.root, revision="HEAD")

    def test_compatible_with_python_path_apis(self):
        self.assertTrue(metrics.safe_path(self.root, self.file))
        self.assertFalse(metrics.safe_path(self.root, self.root.parent / "elsewhere"))
        self.assertEqual(self.report()["status"], "PASS", self.report()["skills"][0]["findings"])


if __name__ == "__main__":
    unittest.main()
