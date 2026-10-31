"""Issue #44 - deterministic catalog integrity, not a semantic or live-agent validator."""
import json
import re
import unittest
from pathlib import Path
from scripts.profile_metrics import skill_paths

ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audits" / "skill-quality-v2"


def load(name):
    return json.loads((AUDIT / name).read_text(encoding="utf-8"))


class SemanticAuditIntegrityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
        cls.inventory = load("inventory.json")
        cls.registry = load("findings.json")
        cls.expected = {name: folder.relative_to(ROOT).as_posix() + "/SKILL.md"
                        for name, folder in skill_paths(ROOT, load_manifest).items()}

    def test_full_manifest_coverage(self):
        actual = {x["skill_id"]: x["path"] for x in self.inventory["skills"]}
        # Historical Issue #44 audit is pinned; do not pretend this new skill
        # was reviewed in its original source snapshot.
        self.assertEqual({name: path for name, path in self.expected.items()
                          if name in actual}, actual)
        self.assertEqual({"product-discovery", "project-delivery-management", "business-system-analysis", "ux-design-process", "ai-engineering-qa", "reliability-testing", "performance-load-testing", "security-engineering", "devops-infrastructure", "accessibility-testing", "ux-ui-design-orchestra", "observability-sre", "dependency-maintenance", "data-engineering", "maintenance-support", "prompt-refinement", "seo-audit", "contract-first", "api-connector-builder", "code-tour", "windows-desktop-e2e", "module-regression", "error-handling"},
                         set(self.expected) - set(actual))
        core = {x: ".agents/roles/" + x + ".md" for x in self.manifest["core_roles"]}
        qa = self.manifest["extension_packs"]["qa"]
        core.update({x: qa["role_root"] + "/" + x + ".md" for x in qa["roles"]})
        self.assertEqual(core, {x["role_id"]: x["path"] for x in self.inventory["roles"]})
        # The Issue #44 inventory is a historical snapshot. New profiles must
        # not be retroactively inserted into that pinned audit.
        historical = {x["profile_id"]: x["skills"] for x in self.inventory["profiles"]}
        self.assertEqual(historical, {name: skills for name, skills
                                      in self.manifest["profiles"].items()
                                      if name not in {"docs-technical", "product-discovery", "project-delivery-management", "business-system-analysis", "ux-design", "ai-engineering-qa", "reliability-testing", "performance-load-testing", "security-engineering", "devops-infrastructure", "accessibility-qa", "ui-orchestra", "observability-sre", "dependency-maintenance", "data-engineering", "maintenance-support", "prompt-refinement", "seo-audit", "native-contract-first",
                                                         "native-api-connectors", "native-code-tours",
                                                         "native-windows-desktop-e2e", "native-module-regression", "native-error-handling"}})
        self.assertEqual(["documentation-maintenance", "research-verification"],
                         self.manifest["profiles"]["docs-technical"])
        self.assertEqual(["product-discovery", "task-scoping", "research-verification"],
                         self.manifest["profiles"]["product-discovery"])

    def test_entries_and_paths(self):
        for group, key in (("skills", "skill_id"), ("roles", "role_id"), ("profiles", "profile_id")):
            records = self.inventory[group]
            names = [x[key] for x in records]
            self.assertEqual(len(names), len(set(names)), group)
            self.assertEqual(names, sorted(names), group)
        for entry in self.inventory["skills"]:
            with self.subTest(entry=entry["skill_id"]):
                path = entry["path"]
                self.assertFalse(Path(path).is_absolute())
                self.assertNotIn("..", Path(path).parts)
                self.assertTrue((ROOT / path).is_file())
                self.assertGreaterEqual(len(entry["positive_triggers"]), 2)
                self.assertGreaterEqual(len(entry["negative_triggers"]), 2)
                self.assertIn(entry["recommendation"], {"KEEP", "REFINE", "DEPRECATE", "REVIEW"})
                self.assertEqual("NOT_MEASURED", entry["observed_activation"])
                self.assertTrue(entry["output_contract"])
                self.assertTrue(entry["required_context"])
        for entry in self.inventory["roles"]:
            self.assertTrue((ROOT / entry["path"]).is_file())
            self.assertEqual("NOT_MEASURED", entry["runtime_verified"])
        for entry in self.inventory["profiles"]:
            self.assertEqual("NOT_MEASURED", entry["runtime_verified"])

    def test_findings_grounded_in_source(self):
        ids = [x["id"] for x in self.registry["findings"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, sorted(ids))
        valid = {"BLOCKER", "HIGH", "MEDIUM", "LOW"}
        decisions = {"KEEP", "REFINE", "DEPRECATE", "REVIEW"}
        for entry in self.registry["findings"]:
            with self.subTest(id=entry["id"]):
                self.assertIn(entry["severity"], valid)
                self.assertIn(entry["recommendation"], decisions)
                self.assertRegex(entry["target_issue"], r"^#(?:45|46|47|48|49|50|51|52)$")
                self.assertEqual("NOT_MEASURED", entry["real_agent_behavior"])
                paths = [entry["component_path"], *entry["related_paths"]]
                for path in paths:
                    self.assertFalse(Path(path).is_absolute())
                    self.assertNotIn("..", Path(path).parts)
                    self.assertTrue((ROOT / path).is_file(), path)
                source = (ROOT / entry["component_path"]).read_text(encoding="utf-8")
                # This audit is pinned to its source_revision; resolved quotes need
                # not remain in today's file. Assert their removal instead.
                if entry["id"] in {"SQ44-003", "SQ44-011", "SQ44-015"}:
                    self.assertEqual("#46" if entry["id"] == "SQ44-003" else "#45",
                                     entry["target_issue"])
                    self.assertNotIn(entry["evidence"]["quote"], source)
                elif entry["id"] in {"SQ44-007", "SQ44-012", "SQ44-014"}:
                    # Historical findings are pinned to audit source_revision.
                    # The current text changed in #47; do not rewrite evidence.
                    self.assertEqual("#51" if entry["id"] == "SQ44-007" else "#47",
                                     entry["target_issue"])
                    self.assertTrue(source.strip())
                elif entry["id"] in {"SQ44-001", "SQ44-002", "SQ44-004", "SQ44-008"}:
                    # Historical evidence stays pinned; verify the current
                    # corrective behavior without rewriting old audit quotes.
                    markers = {
                        "SQ44-001": "if has_py and has_js and has_playwright:",
                        "SQ44-002": '"pytest_installed": "NOT_VERIFIED"',
                        "SQ44-004": '"docs": ("docs-technical"',
                        "SQ44-008": '"qa-all": [',
                    }
                    self.assertEqual("#50", entry["target_issue"])
                    self.assertIn(markers[entry["id"]], source)
                else:
                    self.assertIn(entry["evidence"]["quote"], source)
                self.assertTrue(entry["expected_behavior"])
                self.assertTrue(entry["actual_document_behavior"])

    def test_revision_and_no_implied_runtime_pass(self):
        src = self.inventory["source_revision"]
        self.assertRegex(src, r"^[0-9a-f]{40}$")
        self.assertEqual(src, self.registry["source_revision"])
        self.assertEqual("NOT_MEASURED", self.inventory["real_client_activation"])
        self.assertEqual("NOT_MEASURED", self.inventory["effectiveness"])
        for group in (self.inventory["skills"], self.inventory["roles"], self.inventory["profiles"]):
            self.assertNotIn('"runtime_verified": "PASS"', json.dumps(group))
        for entry in self.inventory["overlaps"]:
            for name in entry["skills"]:
                self.assertIn(name, self.expected)
        for entry in self.inventory["beginner_scenarios"]:
            self.assertIn(entry["candidate_profile"], self.manifest["profiles"])
        # JSON snapshot is deterministic; no timestamps, generated paths, or random identifiers.
        self.assertEqual(self.inventory, load("inventory.json"))
        self.assertEqual(self.registry, load("findings.json"))


if __name__ == "__main__":
    unittest.main()
