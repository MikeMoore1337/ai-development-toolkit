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
    "docs/ru/RELEASE_PROCESS.md",
    "docs/ROADMAP.md", "docs/ru/ROADMAP.md",
    "docs/SKILL_EVALS.md", "docs/ru/SKILL_EVALS.md",
    "docs/INTEGRATIONS.md", "docs/ru/INTEGRATIONS.md",
    "docs/MCP_INSTALL.md", "docs/ru/MCP_INSTALL.md",
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

    def test_current_release_status_must_match_candidate_or_published(self):
        version = self.manifest["version"]
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        status = "candidate" if "**Next release candidate:**" in readme else "released"
        opposite = "released" if status == "candidate" else "candidate"
        self.replace("CHANGELOG.md", f"{version} ({status},", f"{version} ({opposite},")
        self.check("DOC004")

    def test_missing_unreleased(self):
        version = self.manifest["version"]
        self.replace("CHANGELOG.md", f"## Unreleased (main after v{version})", "## Upcoming")
        self.check("DOC004")

    def test_published_release_cannot_reference_wrong_tag(self):
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        candidate = "**Next release candidate:**" in readme
        version = self.manifest["version"]
        if candidate:
            major, minor, patch = (int(value) for value in version.split("."))
            version = f"{major}.{minor}.{patch - 1}"
        self.replace("README.md", f"/releases/tag/v{version}", "/releases/tag/v0.0.0")
        self.check("DOC004")

    def test_published_release_requires_exact_tag_guard(self):
        self.replace("docs/RELEASE_PROCESS.md",
                     "TAG_MANIFEST_VERSION_MISMATCH", "IGNORE_RELEASE_VERSION")
        self.check("DOC004")

    def test_russian_release_process_version_drift(self):
        readme = (self.root / "README.md").read_text(encoding="utf-8")
        version = self.manifest["version"]
        if "**Next release candidate:**" in readme:
            major, minor, patch = (int(value) for value in version.split("."))
            version = f"{major}.{minor}.{patch - 1}"
        self.replace("docs/ru/RELEASE_PROCESS.md",
                     f"Последний публичный тег: [v{version}]",
                     "Последний публичный тег: [v0.0.0]")
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


    def test_human_install_guides_separate_preview_and_apply(self):
        """A newcomer must not copy preview and write operations together."""
        import re

        for path in ("docs/INSTALLATION.md", "docs/ru/INSTALLATION.md"):
            with self.subTest(path=path):
                body = (ROOT / path).read_text(encoding="utf-8")
                blocks = [match.group(2) for match in re.finditer(
                    r"(?m)^(```|~~~)(?:bash|powershell)\n([\s\S]*?)\n\1[ \t]*$",
                    body,
                )]
                self.assertGreaterEqual(len(blocks), 7)
                operations = ("adt.py init", "skill_manager.py install",
                              "skill_manager.py migrate", "skill_manager.py update",
                              "skill_manager.py uninstall", "skill_manager.py recover",
                              "skill_manager.py rollback")
                for block in blocks:
                    commands = [line for line in block.splitlines()
                                if any(op in line for op in operations)
                                and not line.lstrip().startswith("#")]
                    has_preview = any("--apply" not in line for line in commands)
                    has_apply = any("--apply" in line for line in commands)
                    self.assertFalse(has_preview and has_apply, path)

    def test_russian_docs_index_starts_with_user_goals(self):
        text = (ROOT / "docs/ru/README.md").read_text(encoding="utf-8")
        self.assertLess(text.index("## С чего начать"), text.index("## Подключение Toolkit MCP"))
        self.assertLess(text.index("## С чего начать"), text.index("## Установка по платформам"))
        self.assertIn("BEGINNER_START.md", text)

    def test_roadmap_mirrors_completed_delivery_and_live_followups(self):
        """Current roadmaps must not omit closed delivery or imply paid trials."""
        for path in ("docs/ROADMAP.md", "docs/ru/ROADMAP.md"):
            with self.subTest(path=path):
                text = (self.root / path).read_text(encoding="utf-8")
                for number in (*range(271, 281), 293, *range(294, 302), 11, 141):
                    self.assertIn(f"#{number}", text)
                self.assertIn("NOT_PLANNED", text)
                self.assertIn("ZERO-SPEND", text)
                self.assertIn("NOT_MEASURED", text)
                self.assertIn("MANIFEST.json", text)

    def test_historical_skill_fixture_does_not_claim_current_catalog(self):
        for path in ("docs/SKILL_EVALS.md", "docs/ru/SKILL_EVALS.md"):
            with self.subTest(path=path):
                text = (self.root / path).read_text(encoding="utf-8")
                self.assertIn("65", text)
                self.assertIn("82", text)
                self.assertIn("#141", text)
                self.assertIn("#11", text)
                self.assertNotIn("all 65 declared skills", text)


    def test_all_four_integration_paths_are_honest_and_verifiable(self):
        for path in ("docs/INTEGRATIONS.md", "docs/ru/INTEGRATIONS.md"):
            with self.subTest(path=path):
                text = (self.root / path).read_text(encoding="utf-8")
                for value in ("ChatGPT", "Personal MCP", "Project MCP",
                              "Skill Manager", "Python 3.10+", "Python 3.12+",
                              "toolkit_info", "toolkit_prepare_task", "--apply",
                              "NOT_VERIFIED", "NOT_MEASURED",
                              "MCP_INSTALL.md", "INSTALLATION.md", "L4", "L5", "L6"):
                    self.assertIn(value, text)

    def test_project_mcp_docs_link_to_single_integration_guide(self):
        for path in ("docs/MCP_INSTALL.md", "docs/ru/MCP_INSTALL.md"):
            with self.subTest(path=path):
                text = (self.root / path).read_text(encoding="utf-8")
                self.assertIn("(INTEGRATIONS.md)", text)
                self.assertIn("Python 3.12+", text)


if __name__ == "__main__":
    unittest.main()
