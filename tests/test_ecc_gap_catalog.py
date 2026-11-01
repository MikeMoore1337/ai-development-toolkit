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
        # The synthetic manually reviewed entry is pinned like production records.
        review_file = self.toolkit / "integrations" / "ecc" / "catalog_review.json"
        review = json.loads(review_file.read_text(encoding="utf-8"))
        review["decisions"][0]["source_blob"] = audit.git(
            self.ecc, "rev-parse", "HEAD:skills/unique/SKILL.md")
        review_file.write_text(json.dumps(review), encoding="utf-8")

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

    def test_fifteen_native_source_skills_have_exact_real_manifest_analogues(self):
        """A shipped skill is not a future candidate or a live-client success."""
        reviewed = json.loads((ROOT / "integrations/ecc/catalog_review.json").read_text(
            encoding="utf-8"))
        decisions = {r["path"]: r for r in reviewed["decisions"]}
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        native = manifest["extension_packs"]["native-ecc-ports"]
        expected = {"contract-first", "api-connector-builder", "code-tour",
                    "windows-desktop-e2e", "module-regression", "error-handling", "mcp-dependency-review",
                    "agent-introspection-debugging", "content-hash-cache-pattern",
                    "loop-design-check", "make-interfaces-feel-better", "article-writing",
                    "click-path-audit", "brand-voice", "content-engine"}
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
            "reason": "Synthetic original source already merged into Toolkit",
            "source_blob": audit.git(self.ecc, "rev-parse", "HEAD:skills/unique/SKILL.md"),
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
        self.assertEqual(60, len(rows))
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

    def test_three_p0_sources_are_pinned_and_no_auto_install(self):
        data = json.loads((ROOT / "integrations/ecc/catalog_review.json").read_text(
            encoding="utf-8"))
        reviewed = {row["path"]: row for row in data["decisions"]}
        expected = {
            "skills/mcp-dependency-review": ("ALREADY_PRESENT", "4b08af8b05d44a0301693fc025a60ca5f4e8ee6d"),
            "skills/click-path-audit": ("ALREADY_PRESENT", "ffc469829b6c4bf893c4f6212d4110e87e9568d6"),
            "skills/agent-architecture-audit": ("HOLD_CONFLICT", "a3c2caa67b0ca7e5323d4e853d898f599694ff10"),
        }
        self.assertEqual(60, len(reviewed))
        for path, (status, blob) in expected.items():
            with self.subTest(path=path):
                row = reviewed[path]
                self.assertEqual(status, row["status"])
                self.assertEqual(blob, row["source_blob"])
                self.assertTrue((ROOT / row["analogue"]).is_file())
                self.assertTrue(row["reason"] and row["benefit"] and row["test_case"])
        native = set(json.loads((ROOT / "MANIFEST.json").read_text(
            encoding="utf-8"))["extension_packs"]["native-ecc-ports"]["skills"])
        self.assertIn("mcp-dependency-review", native)
        self.assertIn("click-path-audit", native)
        self.assertNotIn("agent-architecture-audit", native)


    def test_cross_stack_14_original_blobs_and_no_implicit_adoption(self):
        """Source-backed semantics must not install or execute unapproved upstream skills."""
        review = json.loads((ROOT / "integrations/ecc/catalog_review.json").read_text(
            encoding="utf-8"))
        records = {row["path"]: row for row in review["decisions"]}
        expected = {
            "skills/accessibility": ("HOLD_REVIEW", "0685394eef10a1bf1e5c02f67a3a8b06ae210cc4"),
            "skills/backend-patterns": ("ALREADY_PRESENT", "1142d0a51de34808f8493bac40b68aa745dcd80e"),
            "skills/github-ops": ("HOLD_CONFLICT", "dbbe7b129d9d722e8f0e622c3d8f045fc97bd855"),
            "skills/security-review": ("ALREADY_PRESENT", "3f26b0df65661425de4e5c40c295e04edcad7a83"),
            "skills/mcp-server-patterns": ("HOLD_REVIEW", "503c31bad5ef287368e3badf23226314fad68dbe"),
            "skills/i18n-sync": ("HOLD_REVIEW", "91e0436803310f58e6929c7a53ae85c7d4ed9802"),
            "skills/deployment-patterns": ("ALREADY_PRESENT", "b9d279f8a99889b6f36db99b17b762374474dc99"),
            "skills/react-performance": ("HOLD_REVIEW", "6952967cf4b894f900b5cf692e851ababaf854f5"),
            "skills/postgres-patterns": ("HOLD_REVIEW", "12a3a4a05c2278c7fe1316d9403b5ca037dadf69"),
            "skills/docs-governance": ("HOLD_CONFLICT", "ae00cf8b3f96dcca17f6c53176afccd669150157"),
            "skills/cost-aware-llm-pipeline": ("HOLD_CONFLICT", "e38c15c6d355dfb97c44b9de40f7cb235bfd3f9f"),
            "skills/skill-host-compat": ("HOLD_REVIEW", "220e8b3117056b3924ed1c9c11e28b5de09f9293"),
            "skills/frontend-design-direction": ("HOLD_REVIEW", "6139c73ec7de85b33d62f121cb263f95dfd69f8c"),
            "skills/conventional-commit-review": ("HOLD_REVIEW", "a53c70f6b153c6204ee31bb26b6ee0bc3efb5851"),
        }
        self.assertEqual(60, len(records))
        native = set(json.loads((ROOT / "MANIFEST.json").read_text(
            encoding="utf-8"))["extension_packs"]["native-ecc-ports"]["skills"])
        for path, (status, blob) in expected.items():
            with self.subTest(path=path):
                row = records[path]
                self.assertEqual(status, row["status"])
                self.assertEqual(blob, row["source_blob"])
                self.assertTrue(row["reason"] and row["benefit"] and row["test_case"])
                self.assertNotIn(path.rsplit("/", 1)[-1], native)
                if row["analogue"] != "NOT_VERIFIED":
                    self.assertTrue((ROOT / row["analogue"]).is_file())

    def test_source_wide_relevance_is_only_provisional(self):
        rows = audit.build(self.ecc, self.toolkit, self.rev)
        report = audit.relevance_report(rows, self.ecc, self.toolkit)
        self.assertEqual(6, report["total"])
        self.assertEqual(1, report["manually_decided"])
        self.assertEqual(5, report["pending_semantic_review"])
        self.assertFalse(report["autoinstall"])
        self.assertFalse(report["external_runtime_executed"])
        self.assertTrue(all(x["live_client"] == "NOT_VERIFIED" for x in report["entries"]))
        self.assertEqual(6, len({x["upstream_path"] for x in report["entries"]}))
        unknown = next(x for x in report["entries"] if x["upstream_path"] == "agents/one.md")
        self.assertEqual("NOT_APPROVED", unknown["adoption"])
        self.assertEqual("HOST_PRECEDENCE_REVIEW", unknown["source_screen"]
                         ) if unknown["domains"] else self.assertEqual(
                             "SPECIALIZED_OR_HOST_BOUND", unknown["source_screen"])

    def test_relevance_screen_flags_commands_but_never_runs_them(self):
        row = dict(upstream_path="skills/react-testing", primary_file="skills/react-testing/SKILL.md",
                   name="react-testing", description="React component tests and QA",
                   trigger="Use when writing tests", kind="skill",
                   sha256_component="a" * 64, upstream_revision="b" * 40,
                   toolkit_analogue="NOT_VERIFIED", status="HOLD_REVIEW")
        source = "# React Testing\n## Examples\nDo not run 'npx tool'.\nNever publish without consent.\n"
        result = audit.classify_relevance(row, source, set())
        self.assertEqual("CANDIDATE_FOR_DEEP_REVIEW", result["source_screen"])
        self.assertIn("testing", result["domains"])
        self.assertIn("development", result["domains"])
        self.assertEqual("NOT_APPROVED", result["adoption"])
        self.assertIn("CHECK_EXTERNAL_RUNTIME_AND_COST", result["source_signals"])
        self.assertIn("CHECK_SIDE_EFFECTS_AND_PERMISSIONS", result["source_signals"])
        with self.assertRaisesRegex(ValueError, "missing original"):
            audit.classify_relevance(row, "", set())

    def test_two_editorial_sources_are_pinned_and_not_autopublished(self):
        reviewed = json.loads((ROOT / "integrations/ecc/catalog_review.json").read_text(encoding="utf-8"))
        by_path = {row["path"]: row for row in reviewed["decisions"]}
        for name, blob in {
            "brand-voice": "a70421076f3aba4f2d1a0886888b839095b50380",
            "content-engine": "28ddd4e1676f4ea67d34a9d244a94164e088b80e",
        }.items():
            row = by_path["skills/" + name]
            self.assertEqual("ALREADY_PRESENT", row["status"])
            self.assertEqual(blob, row["source_blob"])
            self.assertTrue((ROOT / row["analogue"]).is_file())
            self.assertTrue(row["test_case"] and row["reason"])
            self.assertIn("NOT_VERIFIED", row["test_case"])
        manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(["brand-voice", "content-engine"],
                         manifest["profiles"]["native-editorial-suite"])
        self.assertFalse(manifest["extension_packs"]["native-ecc-ports"]["auto_install"])

    def test_multiline_original_description_is_not_lost(self):
        frontmatter = "---\ndescription: >-\n  Cross module dependency audit\n  with schema compatibility.\n---\n"
        result = audit.frontmatter(frontmatter)
        self.assertEqual("Cross module dependency audit with schema compatibility.",
                         result["description"])

    def test_all_manual_source_decisions_have_pinned_git_blobs(self):
        review = json.loads((ROOT / "integrations/ecc/catalog_review.json").read_text(
            encoding="utf-8"))
        self.assertEqual(60, len(review["decisions"]))
        self.assertTrue(all(
            isinstance(row.get("source_blob"), str)
            and len(row["source_blob"]) == 40
            and all(char in "0123456789abcdef" for char in row["source_blob"])
            for row in review["decisions"]
        ))

    def test_source_blob_must_be_present_and_well_formed(self):
        file = self.toolkit / "integrations" / "ecc" / "catalog_review.json"
        review = json.loads(file.read_text(encoding="utf-8"))
        for invalid in (None, "", "z" * 40, "0" * 39):
            with self.subTest(invalid=invalid):
                row = dict(review["decisions"][0])
                if invalid is None:
                    row.pop("source_blob", None)
                else:
                    row["source_blob"] = invalid
                file.write_text(json.dumps({"schema_version": 1, "decisions": [row]}),
                                encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "source blob missing or invalid"):
                    audit.build(self.ecc, self.toolkit, self.rev)

    def test_mismatched_git_blob_fails_closed(self):
        file = self.toolkit / "integrations" / "ecc" / "catalog_review.json"
        review = json.loads(file.read_text(encoding="utf-8"))
        review["decisions"][0]["source_blob"] = "0" * 40
        file.write_text(json.dumps(review), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "source blob differs from pinned Git tree"):
            audit.build(self.ecc, self.toolkit, self.rev)

    def test_dirty_checkout_with_pinned_head_fails_closed(self):
        path = self.ecc / "skills" / "unique" / "SKILL.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nInjected local edit\n",
                        encoding="utf-8")
        self.assertEqual(self.rev, audit.git(self.ecc, "rev-parse", "HEAD"))
        with self.assertRaisesRegex(ValueError, "working tree differs from pinned HEAD"):
            audit.build(self.ecc, self.toolkit, self.rev)

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
            "analogue": ".agents/skills/overlap/SKILL.md",
            "source_blob": audit.git(self.ecc, "rev-parse", "HEAD:skills/overlap/SKILL.md"),
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
