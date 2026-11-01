"""Offline regression tests for exhaustive upstream-only ECC catalogue (#435)."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ecc_gap_catalog as audit


class CatalogueTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.base = Path(t.name)
        self.ecc = self.base / "ecc"
        self.toolkit = self.base / "toolkit"
        self.ecc.mkdir()
        self.toolkit.mkdir()
        (self.ecc / "manifests").mkdir()
        (self.toolkit / "provenance").mkdir()
        (self.toolkit / "integrations" / "ecc").mkdir(parents=True)
        for path, content in {
            "skills/unique/SKILL.md": "---\nname: unique\ndescription: Original unique workflow\n---\n# Original unique\n",
            "skills/overlap/SKILL.md": "---\nname: overlap\ndescription: Similar title only\n---\n",
            "agents/one.md": "# Agent one\n",
            "commands/one.md": "# Command one\n",
            "rules/common/rule.md": "# Common rule\n",
            "rules/common/non-md.json": "{}\n",
        }.items():
            f = self.ecc / path
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_text(content, encoding="utf-8")
        (self.ecc / "manifests" / "install-components.json").write_text(json.dumps({
            "components": [{"id": "skill:unique", "modules": ["workflow-quality"]}]
        }), encoding="utf-8")
        (self.ecc / "manifests" / "install-modules.json").write_text(json.dumps({
            "modules": [{"id": "workflow-quality", "dependencies": [], "targets": ["codex", "hermes"]}]
        }), encoding="utf-8")
        (self.toolkit / "provenance" / "skills.json").write_text(json.dumps({
            "components": [{"kind": "skill", "path": ".agents/skills/overlap"}]
        }), encoding="utf-8")
        (self.toolkit / "integrations" / "ecc" / "catalog_review.json").write_text(
            json.dumps({"schema_version": 1, "decisions": [{
                "path": "skills/unique", "status": "ADOPT_AS_IS_CANDIDATE",
                "analogue": "NOT_VERIFIED", "reason": "Exact official selective component registration"
            }]}), encoding="utf-8")
        subprocess.run(["git", "init", "-q", str(self.ecc)], check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", str(self.ecc), "add", "."], check=True,
                       capture_output=True)
        subprocess.run(["git", "-C", str(self.ecc), "-c", "user.email=test@example.invalid",
                        "-c", "user.name=Fixture", "commit", "-qm", "synthetic"],
                       check=True, capture_output=True)
        self.rev = audit.git(self.ecc, "rev-parse", "HEAD")

    def test_every_file_group_is_accounted_for_and_no_autoinstall(self):
        rows = audit.build(self.ecc, self.toolkit, self.rev)
        self.assertEqual(6, len(rows))
        self.assertEqual({"skill", "agent", "command", "rule"},
                         {row["kind"] for row in rows})
        self.assertEqual(2, len([r for r in rows if r["kind"] == "rule"]))
        self.assertTrue(all(r["owner_gate"] == "EXPLICIT_OPT_IN_REQUIRED" for r in rows))
        self.assertEqual("HOLD_REVIEW", next(r for r in rows
              if r["upstream_path"] == "skills/overlap")["status"])
        one = next(r for r in rows if r["upstream_path"] == "skills/unique")
        self.assertEqual("ADOPT_AS_IS_CANDIDATE", one["status"])
        self.assertEqual("codex,hermes", one["host_targets"])
        self.assertEqual("NOT_VERIFIED", one["live_client"])

    def test_six_native_source_skills_have_exact_real_manifest_analogues(self):
        """A shipped skill is not a future candidate or a live-client success."""
        reviewed = json.loads((ROOT / "integrations/ecc/catalog_review.json").read_text(
            encoding="utf-8"))
        decisions = {r["path"]: r for r in reviewed["decisions"]}
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        native = manifest["extension_packs"]["native-ecc-ports"]
        expected = {"contract-first", "api-connector-builder", "code-tour",
                    "windows-desktop-e2e", "module-regression", "error-handling"}
        self.assertEqual(expected, set(native["skills"]))
        self.assertFalse(native["auto_install"])
        self.assertTrue(native["standalone"])
        for name in expected:
            with self.subTest(name=name):
                row = decisions["skills/" + name]
                self.assertEqual("ALREADY_PRESENT", row["status"])
                path = f"optional-original-skills/{name}/SKILL.md"
                self.assertEqual(path, row["analogue"])
                self.assertTrue((ROOT / path).is_file())
                self.assertTrue((ROOT / "optional-original-skills" /
                                 name / "LICENSE").is_file())
                self.assertIn("NOT_VERIFIED", row["reason"] + " " + row["test_case"])
                self.assertNotIn("ecc-universal", row["analogue"])
        self.assertTrue((ROOT / "optional-original-skills/windows-desktop-e2e/"
                         "references/ORIGINAL_SKILL.md").is_file())
        self.assertTrue((ROOT / "optional-original-skills/module-regression/"
                         "templates/REGRESSION.example.md").is_file())
        self.assertEqual(0, len(expected - set(native["skills"])))

    def test_reviewed_ecc_overlap_reuses_native_controller_with_evidence(self):
        """Approved overlaps must have a real Toolkit file and explicit missing-oracle gates."""
        review = json.loads((ROOT / "integrations/ecc/catalog_review.json").read_text(
            encoding="utf-8"))
        decisions = {entry["path"]: entry for entry in review["decisions"]}
        expected = {
            "skills/change-impact": (
                "extensions/qa/skills/change-impact-analysis/SKILL.md",
                ("change -> affected surface", "failure mode",
                 "remaining uncertainty"),
            ),
            "skills/tdd-workflow": (
                ".agents/skills/feature-delivery/SKILL.md",
                ("Optional test-first cycle", "observe RED", "observe GREEN",
                 "NOT_VERIFIED", "Do not mandate a universal 80%"),
            ),
        }
        for source, (analogue, evidence_terms) in expected.items():
            with self.subTest(source=source):
                decision = decisions[source]
                self.assertEqual("ALREADY_PRESENT", decision["status"])
                self.assertEqual(analogue, decision["analogue"])
                native = ROOT / analogue
                self.assertTrue(native.is_file(), analogue)
                source_text = native.read_text(encoding="utf-8")
                for term in evidence_terms:
                    self.assertIn(term, source_text)
                self.assertTrue(decision["reason"])
                self.assertTrue(decision["test_case"])
        feature = (ROOT / ".agents/skills/feature-delivery/SKILL.md").read_text(
            encoding="utf-8")
        for marker in ("Pre-change vs actual-diff alignment", "actual diff",
                       "MATCHED", "CHANGED", "NOT_VERIFIED"):
            self.assertIn(marker, feature)
        self.assertIn("license-constrained QA impact skill stays byte-unchanged",
                      decisions["skills/change-impact"]["benefit"])
        self.assertEqual("HOLD_UNSUPPORTED",
                         decisions["skills/continuous-learning"]["status"])
        # No auto-install or activation claim; original 601-component inventory
        # remains pending review for entries not explicitly recorded above.
        self.assertIn("never installation authorization", review["note"])

    def test_all_reviewed_candidates_can_become_native_without_phantom_adoption(self):
        """Full catalogue may have zero unmerged candidates after native integration."""
        root = self.toolkit / ".agents/skills/unique"
        root.mkdir(parents=True)
        (root / "SKILL.md").write_text("---\nname: unique\ndescription: Fixture\n---\n", encoding="utf-8")
        decisions = self.toolkit / "integrations/ecc/catalog_review.json"
        decisions.write_text(json.dumps({"schema_version": 1, "decisions": [{
            "path": "skills/unique", "status": "ALREADY_PRESENT",
            "analogue": ".agents/skills/unique/SKILL.md",
            "reason": "Synthetic original source already merged into Toolkit"
        }]}), encoding="utf-8")
        rows = audit.build(self.ecc, self.toolkit, self.rev)
        self.assertTrue(any(row["status"] == "ALREADY_PRESENT" for row in rows))
        self.assertFalse(any(row["status"] == "ADOPT_AS_IS_CANDIDATE" for row in rows))
        workflow = (ROOT / ".github/workflows/ecc-gap-catalog.yml").read_text(
            encoding="utf-8")
        self.assertIn('assert any(x["status"] == "ALREADY_PRESENT" for x in rows)', workflow)
        self.assertNotIn(
            'assert any(x["status"] == "ADOPT_AS_IS_CANDIDATE" for x in rows)', workflow)

    def test_additional_ecc_source_review_keeps_non_native_components_on_hold(self):
        review = json.loads((ROOT / "integrations/ecc/catalog_review.json").read_text(
            encoding="utf-8"))
        by_path = {row["path"]: row for row in review["decisions"]}
        expected = {
            "skills/test-collaboration": "HOLD_REVIEW",
            "skills/architecture-decision-records": "ALREADY_PRESENT",
            "skills/ai-regression-testing": "HOLD_CONFLICT",
            "skills/codebase-onboarding": "HOLD_CONFLICT",
        }
        for path, status in expected.items():
            with self.subTest(source=path):
                self.assertEqual(status, by_path[path]["status"])
                self.assertTrue(by_path[path]["reason"])
                self.assertTrue(by_path[path]["benefit"])
                self.assertTrue(by_path[path]["test_case"])
                self.assertTrue((ROOT / by_path[path]["analogue"]).is_file())
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        shipped = set(manifest["extension_packs"]["native-ecc-ports"]["skills"])
        self.assertTrue({path.split("/")[-1] for path in expected}.isdisjoint(shipped))


    def test_nine_additional_pinned_source_decisions_are_nonautomatic(self):
        """Native source review is not permission to install, delegate or run tools."""
        review = json.loads((ROOT / "integrations/ecc/catalog_review.json").read_text(
            encoding="utf-8"))
        rows = {item["path"]: item for item in review["decisions"]}
        expected = {
            "skills/browser-qa": "ALREADY_PRESENT",
            "skills/frontend-a11y": "ALREADY_PRESENT",
            "skills/seo": "ALREADY_PRESENT",
            "skills/python-testing": "HOLD_CONFLICT",
            "skills/react-testing": "HOLD_REVIEW",
            "skills/fastapi-patterns": "HOLD_REVIEW",
            "skills/design-system": "HOLD_REVIEW",
            "skills/agent-eval": "HOLD_UNSUPPORTED",
            "skills/python-patterns": "HOLD_REVIEW",
        }
        original_blobs = {
            "skills/browser-qa": "f6358d6ac8b43edb7cb894481de56c53e19b3cf2",
            "skills/frontend-a11y": "a39419935900b1ac1003827d83c896610350b619",
            "skills/seo": "a4032a5b5a98c4b09eabf4e4f8971ed664887496",
            "skills/python-testing": "8e68a084ad890afb901c43741a733e6d076958b0",
            "skills/react-testing": "babaf6ebef80f1e6ba66ef5242372dd175870a40",
            "skills/fastapi-patterns": "b4a0a5b5873d90d05797b830ab5966e4cb53ee9d",
            "skills/design-system": "c041ed8ab627ebad68c00d062603963fc179fae9",
            "skills/agent-eval": "c082704f19ad58e8f0aa986a25f1da0b29809922",
            "skills/python-patterns": "ced3d588d816fb6880dfef4d67f30cab9d1b82df",
        }
        self.assertEqual(36, len(rows))
        native = set(json.loads((ROOT / "MANIFEST.json").read_text(
            encoding="utf-8"))["extension_packs"]["native-ecc-ports"]["skills"])
        self.assertTrue({p.rsplit("/", 1)[-1] for p in expected}.isdisjoint(native))
        for source, status in expected.items():
            with self.subTest(source=source):
                row = rows[source]
                self.assertEqual(status, row["status"])
                self.assertEqual(original_blobs[source], row["source_blob"])
                self.assertTrue(all(c in "0123456789abcdef" for c in row["source_blob"]))
                self.assertTrue(row["reason"] and row["benefit"] and row["test_case"])
                if row["analogue"] != "NOT_VERIFIED":
                    self.assertTrue((ROOT / row["analogue"]).is_file())
        self.assertIn("no runtime", review["note"])

    def test_multiline_original_description_is_not_lost(self):
        frontmatter = "---\ndescription: >-\n  Cross module dependency audit\n  with schema compatibility.\n---\n"
        result = audit.frontmatter(frontmatter)
        self.assertEqual("Cross module dependency audit with schema compatibility.",
                         result["description"])

    def test_wrong_source_pin_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "differs"):
            audit.build(self.ecc, self.toolkit, "a" * 40)

    def test_stale_manually_reviewed_component_blocks_catalogue(self):
        file = self.toolkit / "integrations" / "ecc" / "catalog_review.json"
        file.write_text(json.dumps({"schema_version": 1, "decisions": [{
            "path": "skills/absent", "status": "ALREADY_PRESENT", "reason": "fake",
            "analogue": ".agents/skills/absent"
        }]}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "absent from pinned upstream"):
            audit.build(self.ecc, self.toolkit, self.rev)

    def test_claimed_coverage_requires_on_disk_toolkit_evidence(self):
        file = self.toolkit / "integrations" / "ecc" / "catalog_review.json"
        file.write_text(json.dumps({"schema_version": 1, "decisions": [{
            "path": "skills/overlap", "status": "ALREADY_PRESENT", "reason": "fake",
            "analogue": ".agents/skills/overlap/SKILL.md"
        }]}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "lacks real Toolkit evidence"):
            audit.build(self.ecc, self.toolkit, self.rev)

    def test_duplicate_and_unknown_decisions_fail_closed(self):
        file = self.toolkit / "integrations" / "ecc" / "catalog_review.json"
        file.write_text(json.dumps({"schema_version": 1, "decisions": [
            {"path": "skills/unique", "status": "ADOPT_AS_IS_CANDIDATE", "reason": "test"},
            {"path": "skills/unique", "status": "ADOPT_AS_IS_CANDIDATE", "reason": "duplicate"}
        ]}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            audit.build(self.ecc, self.toolkit, self.rev)


if __name__ == "__main__":
    unittest.main()
