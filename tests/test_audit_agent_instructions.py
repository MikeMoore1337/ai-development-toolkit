"""No paid model, no filesystem mutation, no raw instruction text in audit output."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_agent_instructions.py"
spec = importlib.util.spec_from_file_location("audit_agent_instructions_376", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class AgentInstructionAuditTests(unittest.TestCase):
    def test_valid_reference_and_no_writes(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            (root / "src.py").write_text("a\nb\n", encoding="utf-8")
            instructions = root / "AGENTS.md"
            instructions.write_text("# Rules\nUse `src.py:2`\n", encoding="utf-8")
            before = instructions.read_bytes()
            result = module.audit(root)
            self.assertEqual(result["findings"], [])
            self.assertEqual(instructions.read_bytes(), before)

    def test_stale_reference_and_cross_file_repeat(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            (root / "AGENTS.md").write_text("- Never publish unreviewed outputs to production\nUse `gone.py:14`\n", encoding="utf-8")
            nested = root / "nested"
            nested.mkdir()
            (nested / "CLAUDE.md").write_text("- Never publish unreviewed outputs to production\n", encoding="utf-8")
            out = module.audit(root)
            codes = [f["code"] for f in out["findings"]]
            self.assertEqual(codes.count("DUPLICATE_CROSS_FILE_RULE"), 2)
            self.assertIn("STALE_OR_UNSAFE_REFERENCE", codes)
            self.assertNotIn("Never publish", json.dumps(out))

    def test_excludes_generated_files(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            (root / "node_modules").mkdir()
            (root / "node_modules" / "AGENTS.md").write_text("- Ignored rule\n", encoding="utf-8")
            self.assertEqual(module.audit(root)["files"], 0)

    def test_no_symlink_escape(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            other = root / "outside.md"
            other.write_text("secret", encoding="utf-8")
            link = root / "AGENTS.md"
            try:
                link.symlink_to(other)
            except (OSError, NotImplementedError):
                self.skipTest("symlink privileges unavailable")
            self.assertEqual(module.audit(root)["findings"][0]["code"], "UNSAFE_FILE")

    def test_oversized_rejected_without_raw_text(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            (root / "AGENTS.md").write_text("s" * (module.MAX_BYTES + 1), encoding="utf-8")
            self.assertEqual(module.audit(root)["findings"][0]["code"], "TOO_LARGE")

    def test_root_symlink_denied(self):
        with tempfile.TemporaryDirectory() as base:
            root = Path(base)
            link = root / "linked"
            try:
                link.symlink_to(root, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("symlink privileges unavailable")
            with self.assertRaises(ValueError):
                module.audit(link)


if __name__ == "__main__":
    unittest.main()
