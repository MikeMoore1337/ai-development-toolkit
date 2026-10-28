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
        self.assertEqual(5, len(rows))
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
