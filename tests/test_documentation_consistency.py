"""Negative fixtures for current documentation drift, Issue #47."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("docs_quality_47", ROOT / "scripts/validate_quality.py")
validator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = validator
spec.loader.exec_module(validator)
DOCUMENTS = (
    "README.md", "README.ru.md", "CHANGELOG.md",
    "docs/AGENT_SKILLS_SPEC.md", "docs/UNIVERSAL_ENGINEERING.md",
    "docs/SKILLS_CATALOG.md", "docs/RELEASE_PROCESS.md",
)


class DocumentationConsistencyTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for name in DOCUMENTS:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        self.manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))

    def check(self, expected=None):
        findings = []
        validator.check_current_docs(self.root, self.manifest, findings)
        if expected:
            self.assertIn(expected, [f.rule_id for f in findings], findings)
        else:
            self.assertFalse(findings, findings)

    def replace(self, name, before, after):
        path = self.root / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(before, text)
        path.write_text(text.replace(before, after, 1), encoding="utf-8")

    def test_real_docs(self):
        self.check()

    def test_stale_badge(self):
        self.replace("README.md", "badge/skills-82-", "badge/skills-51-")
        self.check("DOC001")

    def test_new_skills_require_doc_refresh(self):
        self.manifest["extension_packs"]["frontend"]["skills"].append("new-skill")
        self.check("DOC001")

    def test_table_cell_missing(self):
        self.replace("README.md", "Five copy-ready requests and honest limits for each AI client |",
                     "Five copy-ready requests and honest limits for each AI client | Extra |")
        self.check("DOC002")

    def test_table_cell_extra(self):
        self.replace("README.md", "Read relevant guidance before proposing changes; no Toolkit installation required just to use the reference |",
                     "Read relevant guidance before proposing changes; no Toolkit installation required just to use the reference | Extra |")
        self.check("DOC002")

    def test_unknown_profile_in_readme(self):
        self.replace("README.ru.md", "| Реализовать существующую функцию | \x60codex-feature\x60 |",
                     "| Реализовать существующую функцию | \x60unknown\x60 |")
        self.check("DOC003")

    def test_stale_catalog_profile(self):
        self.replace("docs/SKILLS_CATALOG.md", "| \x60backend\x60 |",
                     "| \x60unknown\x60 |")
        self.check("DOC003")

    def test_stale_spec_count(self):
        self.replace("docs/AGENT_SKILLS_SPEC.md", "82 in the checked revision",
                     "51 in the checked revision")
        self.check("DOC001")

    def test_prepared_published_release(self):
        self.replace("CHANGELOG.md", "5.5.4 (candidate,", "5.5.4 (released,")
        self.check("DOC004")

    def test_missing_unreleased(self):
        self.replace("CHANGELOG.md", "## Unreleased (main after v5.5.4)", "## Upcoming")
        self.check("DOC004")

    def test_published_release_cannot_reference_wrong_tag(self):
        self.replace("README.md", "/releases/tag/v5.5.3", "/releases/tag/v5.5.2")
        self.check("DOC004")

    def test_release_candidate_requires_exact_tag_guard(self):
        self.replace("docs/RELEASE_PROCESS.md",
                     "TAG_MANIFEST_VERSION_MISMATCH", "IGNORE_RELEASE_VERSION")
        self.check("DOC004")

    def test_manifest_version_drift(self):
        self.manifest["version"] = "5.9.9"
        self.check("DOC004")

    def test_legacy_quick_start(self):
        self.replace("README.md", "skill_manager.py catalog", "install.py --list-profiles")
        self.check("DOC005")

    def test_historic_snapshot_allowed(self):
        (self.root / "docs/OLD_AUDIT.md").write_text("Historic revision: 51 skills.", encoding="utf-8")
        self.check()


if __name__ == "__main__":
    unittest.main()
