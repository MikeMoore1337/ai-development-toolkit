"""Offline client contracts and disposable filesystem fixtures; no client/model calls."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import verify_client_compatibility as compat
import skill_manager as manager


class ClientContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.project = self.root / "project"
        self.project.mkdir()
        self.project.joinpath("AGENTS.md").write_bytes(b"Owner rules\r\n")
        self.project.joinpath("CLAUDE.md").write_bytes(b"Claude rules\n")

    def registry(self, transform=None):
        data = json.loads(compat.REGISTRY.read_text(encoding="utf-8"))
        if transform:
            transform(data)
        file = self.root / "clients.json"
        file.write_text(json.dumps(data), encoding="utf-8")
        return file

    def skill(self, layout=".agents/skills", name="demo", content=None):
        folder = self.project / layout / name
        folder.mkdir(parents=True)
        folder.joinpath("references").mkdir()
        folder.joinpath("references", "guide.md").write_text("# Guide\n", encoding="utf-8")
        folder.joinpath("scripts").mkdir()
        folder.joinpath("scripts", "helper.py").write_text("print('offline')\n", encoding="utf-8")
        folder.joinpath("SKILL.md").write_text(content or (
            f"---\nname: {name}\ndescription: Used to test a portable skill.\n---\n"
            "See [guide](references/guide.md) and [script](scripts/helper.py).\n"
        ), encoding="utf-8")
        return folder

    def test_registry_has_three_documented_clients(self):
        data = compat.load_registry()
        self.assertEqual(set(compat.LAYOUTS), {x["client_id"] for x in data["clients"]})
        for x in data["clients"]:
            self.assertEqual("NOT_TESTED", x["client_discovery_status"])
            self.assertEqual("NOT_TESTED", x["live_activation_status"])
            self.assertEqual("NOT_TESTED", x["effectiveness_status"])

    def test_invalid_schema(self):
        with self.assertRaisesRegex(compat.ContractError, "schema"):
            compat.load_registry(self.registry(lambda d: d.update(schema_version=2)))

    def test_corrupt_registry(self):
        file = self.root / "clients.json"
        file.write_text("{invalid", encoding="utf-8")
        with self.assertRaises(json.JSONDecodeError):
            compat.load_registry(file)

    def test_duplicate_client_rejected(self):
        def change(data):
            data["clients"][1] = copy.deepcopy(data["clients"][0])
        with self.assertRaisesRegex(compat.ContractError, "duplicated"):
            compat.load_registry(self.registry(change))

    def test_unknown_client_rejected(self):
        with self.assertRaisesRegex(compat.ContractError, "Unknown"):
            compat.load_registry(self.registry(lambda d: d["clients"][0].update(client_id="invented")))
        with self.assertRaisesRegex(compat.ContractError, "Unsupported client"):
            compat.check_project(self.project, "invented", ["demo"])

    def test_layout_drift_rejected(self):
        with self.assertRaisesRegex(compat.ContractError, "layout"):
            compat.load_registry(self.registry(lambda d: d["clients"][0].update(supported_skill_layouts=[".evil/skills"])))

    def test_unproven_discovery_claim_rejected(self):
        with self.assertRaisesRegex(compat.ContractError, "L4-L6"):
            compat.load_registry(self.registry(lambda d: d["clients"][0].update(client_discovery_status="VERIFIED")))

    def test_hermes_pin_and_unsupported_manager_required(self):
        with self.assertRaisesRegex(compat.ContractError, "exact commit"):
            compat.load_registry(self.registry(lambda d: d["clients"][2].update(source_revision="main")))
        with self.assertRaisesRegex(compat.ContractError, "No Hermes-specific"):
            compat.load_registry(self.registry(lambda d: d["clients"][2].update(manager_support="VERIFIED")))

    def test_missing_official_documentation_rejected(self):
        with self.assertRaisesRegex(compat.ContractError, "Untrusted documentation"):
            compat.load_registry(self.registry(lambda d: d["clients"][0].update(documentation_url="https://unverified.example/guide")))

    def test_bad_metadata_contract_rejected(self):
        with self.assertRaisesRegex(compat.ContractError, "required"):
            compat.load_registry(self.registry(lambda d: d["clients"][1].update(required_metadata=["description"])))
        with self.assertRaisesRegex(compat.ContractError, "Invalid"):
            compat.load_registry(self.registry(lambda d: d["clients"][0].update(filesystem_test_status="COMPATIBLE")))

    def test_valid_skills_and_nested_files_for_all_clients(self):
        cases = (("codex", ".agents/skills"), ("claude-code", ".claude/skills"),
                 ("hermes", ".agents/skills"), ("hermes", ".hermes/skills"))
        for client, layout in cases:
            with self.subTest(client=client, layout=layout):
                folder = self.project / layout / "demo"
                if not folder.exists():
                    self.skill(layout)
                result = compat.check_project(self.project, client, ["demo"], layout=layout)
                self.assertEqual("PASS", result["status"], result["issues"])
                self.assertEqual("NOT_TESTED", result["levels"]["L4"])

    def test_unknown_layout_fails_closed(self):
        with self.assertRaisesRegex(compat.ContractError, "Unsupported layout"):
            compat.check_project(self.project, "claude-code", ["demo"], layout=".agents/skills")

    def test_missing_skill_and_bad_frontmatter(self):
        result = compat.check_project(self.project, "codex", ["missing"])
        self.assertEqual("FAIL", result["status"])
        self.assertIn("Missing skill", result["issues"][0])
        self.skill(content="---\nname: DEMO\ndescription: test\n---\n")
        self.assertEqual("FAIL", compat.check_project(self.project, "codex", ["demo"])["status"])

    def test_reject_unknown_frontmatter(self):
        self.skill(content="---\nname: demo\ndescription: test\nforeign-field: true\n---\n")
        result = compat.check_project(self.project, "codex", ["demo"])
        self.assertEqual("FAIL", result["status"])
        self.assertIn("unsupported top-level", " ".join(result["issues"]))

    def test_broken_reference_and_escaped_reference(self):
        skill = self.skill()
        (skill / "references" / "guide.md").unlink()
        result = compat.check_project(self.project, "codex", ["demo"])
        self.assertEqual("FAIL", result["status"])
        self.assertIn("Missing or escaping", " ".join(result["issues"]))
        (skill / "SKILL.md").write_text(
            "---\nname: demo\ndescription: test\n---\n[escape](../../../../AGENTS.md)\n", encoding="utf-8")
        result = compat.check_project(self.project, "codex", ["demo"])
        self.assertEqual("FAIL", result["status"])

    def test_symlink_escape_refused_when_supported(self):
        skill = self.skill()
        target = self.root / "outside.md"
        target.write_text("private", encoding="utf-8")
        try:
            (skill / "references" / "linked.md").symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation not permitted by host")
        result = compat.check_project(self.project, "codex", ["demo"])
        self.assertEqual("FAIL", result["status"])
        self.assertIn("Linked path", " ".join(result["issues"]))

    def test_read_only_check_preserves_project_instructions(self):
        self.skill()
        before = [self.project.joinpath(f).read_bytes() for f in ("AGENTS.md", "CLAUDE.md")]
        self.assertEqual("PASS", compat.check_project(self.project, "codex", ["demo"])["status"])
        after = [self.project.joinpath(f).read_bytes() for f in ("AGENTS.md", "CLAUDE.md")]
        self.assertEqual(before, after)
        self.assertFalse((self.project / ".adt").exists())

    def test_manager_qa_profile_install_and_migrate_offline(self):
        # Use the actual QA profile and existing managed-install API (not a new installer).
        names = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))["profiles"]["qa-python"]
        before = {f: (self.project / f).read_bytes() for f in ("AGENTS.md", "CLAUDE.md")}
        preview = manager.operate("install", self.project, layout="codex", names=names)
        self.assertFalse(preview["applied"])
        manager.operate("install", self.project, layout="codex", names=names, apply=True)
        self.assertEqual("PASS", compat.check_project(self.project, "codex", names)["status"])
        migration = manager.operate("migrate", self.project, layout="claude",
                                    from_layout="codex", apply=True)
        self.assertTrue(migration["applied"])
        self.assertEqual("PASS", compat.check_project(self.project, "claude-code", names)["status"])
        for name in names:
            self.assertEqual(manager.tree_digest(self.project / ".agents/skills" / name),
                             manager.tree_digest(self.project / ".claude/skills" / name))
        self.assertEqual(before, {f: (self.project / f).read_bytes() for f in before})
        self.assertEqual([], manager.operate("update", self.project, layout="claude")["changes"])

    def test_manager_unowned_skill_collision_refuses_overwrite(self):
        self.skill(layout=".claude/skills", name="api-testing")
        original = (self.project / ".claude/skills/api-testing/SKILL.md").read_bytes()
        with self.assertRaisesRegex(manager.ManagerError, "Existing skill"):
            manager.operate("install", self.project, layout="claude",
                            names=["api-testing"], apply=True)
        self.assertEqual(original, (self.project / ".claude/skills/api-testing/SKILL.md").read_bytes())


if __name__ == "__main__":
    unittest.main()
