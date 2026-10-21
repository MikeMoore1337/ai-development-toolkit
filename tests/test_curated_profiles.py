"""Focused skill profiles: old inventory, new choices and manager ownership."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from install import install, skill_sources
from profile_metrics import measure
from skill_manager import ManagerError, operate, read_state

MANIFEST = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
RULES = json.loads((ROOT / "docs/QUALITY_RULES.json").read_text(encoding="utf-8"))
LEGACY_PROFILE_DIGEST = "c26a85dd1c214892cbf1ef6539a743c6f0cc87db53242d07f0103c79ecb40a41"
NEW = {
    "maintenance-support": ["maintenance-support", "defect-management",
                            "failure-triage", "quality-gate-assessment", "release-safety"],
    "data-engineering": ["data-engineering", "data-access", "contract-testing",
                         "database-validation", "reliability-testing"],
    "dependency-maintenance": ["dependency-maintenance", "minimal-safe-change",
                               "code-review", "security-engineering", "release-safety"],
    "observability-sre": ["observability-sre", "failure-triage", "release-safety",
                          "security-boundaries", "reliability-testing"],
    "ui-orchestra": ["ux-ui-design-orchestra", "design-system-consistency",
                     "screenshot-fidelity", "qa-strategy"],
    "accessibility-qa": ["accessibility-testing", "test-analysis-design",
                         "playwright-testing", "quality-gate-assessment"],
    "devops-infrastructure": ["devops-infrastructure", "release-safety",
                             "security-boundaries", "architecture-decisions"],
    "security-engineering": ["security-engineering", "security-boundaries",
                             "security-review", "security-testing"],
    "performance-load-testing": ["performance-load-testing", "test-strategy",
                                 "failure-triage"],
    "reliability-testing": ["reliability-testing", "background-processing",
                            "integration-testing", "failure-triage"],
    "ai-engineering-qa": ["ai-engineering-qa", "research-verification",
                          "security-boundaries", "test-analysis-design", "contract-testing"],
    "docs-technical": ["documentation-maintenance", "research-verification"],
    "backend": ["task-scoping", "architecture-decisions", "service-architecture",
                "api-design", "implementation", "qa-strategy", "code-review"],
    "frontend": ["task-scoping", "design-system-consistency", "component-architecture",
                 "frontend-api-integration", "implementation", "qa-strategy", "code-review"],
    "fullstack": ["task-scoping", "end-to-end-feature-design", "fullstack-integration",
                  "implementation", "qa-strategy", "code-review"],
    "research": ["task-scoping", "research-verification"],
    "product-discovery": ["product-discovery", "task-scoping", "research-verification"],
    "business-system-analysis": ["business-system-analysis", "task-scoping",
                                 "requirement-analysis", "requirements-traceability"],
    "project-delivery-management": ["project-delivery-management", "task-scoping",
                                    "requirements-traceability", "quality-gate-assessment"],
    "ux-design": ["ux-design-process", "design-system-consistency",
                  "component-architecture", "task-scoping"],
}


class CuratedProfileTests(unittest.TestCase):
    def test_legacy_profiles_unchanged(self):
        old = {k: v for k, v in MANIFEST["profiles"].items() if k not in NEW}
        fingerprint = hashlib.sha256(
            json.dumps(old, sort_keys=True, ensure_ascii=False,
                       separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        self.assertEqual(23, len(old))
        self.assertEqual(LEGACY_PROFILE_DIGEST, fingerprint)

    def test_all_profiles_valid_and_new_compositions_minimal(self):
        self.assertEqual(43, len(MANIFEST["profiles"]))
        self.assertTrue(set(NEW).issubset(MANIFEST["profiles"]))
        available = set(skill_sources(MANIFEST))
        for name, expected in NEW.items():
            self.assertEqual(expected, MANIFEST["profiles"][name])
        for name, skills in MANIFEST["profiles"].items():
            with self.subTest(name=name):
                self.assertTrue(skills)
                self.assertEqual(len(skills), len(set(skills)))
                self.assertTrue(set(skills) <= available)
                for rule in RULES["exclusive_workflows"]:
                    self.assertFalse(set(rule["skills"]) <= set(skills),
                                     f"{name} violates {rule['rule_id']}")

    def test_metrics_match_file_bytes_and_are_reproducible(self):
        result = measure(ROOT, MANIFEST)
        self.assertEqual(result, measure(ROOT, MANIFEST))
        self.assertEqual(set(MANIFEST["profiles"]), set(result["profiles"]))
        research = result["profiles"]["research"]
        self.assertEqual(2, research["skill_count"])
        sources = skill_sources(MANIFEST)
        expected = sum(p.stat().st_size
                       for skill in MANIFEST["profiles"]["research"]
                       for p in sources[skill].rglob("*") if p.is_file())
        self.assertEqual(expected, research["installed_file_bytes"])
        self.assertEqual(3, result["profiles"]["frontend"]["overlap_skill_counts"]["ui-fix"])
        with self.assertRaisesRegex(ValueError, "Unknown profile"):
            measure(ROOT, MANIFEST, "absent")

    def test_both_client_previews_leave_files_untouched(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "AGENTS.md").write_bytes(b"private\n")
            (target / "CLAUDE.md").write_bytes(b"private\n")
            for layout in ("codex", "claude"):
                names = MANIFEST["profiles"]["research"]
                install(target, names, False, layout=layout)
                preview = operate("install", target, names=names, layout=layout)
                self.assertFalse(preview["applied"])
            self.assertEqual(sorted(p.name for p in target.iterdir()),
                             ["AGENTS.md", "CLAUDE.md"])

    def test_managed_cross_client_install_and_modified_skill_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "AGENTS.md").write_text("private\n")
            (target / "CLAUDE.md").write_text("private\n")
            names = MANIFEST["profiles"]["research"]
            for layout in ("codex", "claude"):
                result = operate("install", target, names=names, layout=layout,
                                 apply=True)
                self.assertTrue(result["applied"])
                self.assertEqual(set(names), set(read_state(target, layout)["skills"]))
                parent = ".agents" if layout == "codex" else ".claude"
                skill_file = target / parent / "skills" / names[0] / "SKILL.md"
                skill_file.write_text(skill_file.read_text(encoding="utf-8")
                                      + "\nlocal edit", encoding="utf-8")
                with self.assertRaisesRegex(ManagerError, "Local modifications"):
                    operate("update", target, layout=layout, apply=True)
                self.assertIn("local edit", skill_file.read_text(encoding="utf-8"))
            self.assertEqual("private\n", (target / "AGENTS.md").read_text())
            self.assertEqual("private\n", (target / "CLAUDE.md").read_text())

    def test_unmanaged_skill_collision_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            existing = target / ".agents" / "skills" / "task-scoping"
            existing.mkdir(parents=True)
            (existing / "SKILL.md").write_text("CUSTOM\n")
            with self.assertRaisesRegex(ManagerError, "Existing skill"):
                operate("install", target, names=NEW["backend"], apply=True)
            self.assertEqual("CUSTOM\n", (existing / "SKILL.md").read_text())


if __name__ == "__main__":
    unittest.main()
