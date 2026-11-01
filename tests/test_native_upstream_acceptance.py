"""#492: bounded native CLI acceptance driver negative oracles (offline)."""
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/native_upstream_acceptance.py"
spec = importlib.util.spec_from_file_location("native_upstream_acceptance", SCRIPT)
assert spec and spec.loader
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


class NativeFirstAcceptanceUnitTests(unittest.TestCase):
    def test_no_model_or_codex_cli_in_allowed_commands(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("graphify", source)
        self.assertIn("harness2", source)
        self.assertIn("GOOGLE_APPLICATION_CREDENTIALS", source)
        self.assertNotIn('["codex"', source)
        self.assertNotIn('["claude"', source)
        self.assertNotIn('"harness2", "--bench"', source)

    def test_native_passthrough_acceptance_fails_on_any_overlay(self):
        valid = {
            "status": "NATIVE_UPSTREAM_PASSTHROUGH", "controller": "graphify",
            "skills": [], "priority_skills": [], "selected_skills": [], "roles": [],
            "loaded_skills": [], "loaded_roles": [], "suggested_skills": [],
            "execution": "NOT_RUN", "project_files_changed": False,
            "toolkit_hook_injection": "SKIPPED",
            "required_setup": {"status": "SKIPPED_EXTERNAL_NATIVE"},
        }
        tool.assert_passthrough(valid, controller="graphify")
        for field, broken in (("skills", ["implementation"]),
                              ("loaded_roles", ["orchestrator"]),
                              ("toolkit_hook_injection", "ENABLED"),
                              ("execution", "EXECUTED"),
                              ("project_files_changed", True)):
            with self.subTest(field=field), self.assertRaises(tool.AcceptanceError):
                tool.assert_passthrough({**valid, field: broken}, controller="graphify")
        with self.assertRaises(tool.AcceptanceError):
            tool.assert_passthrough({**valid, "status": "ADVISORY_ONLY"},
                                    controller="graphify")

    def test_graph_summary_rejects_missing_and_empty_graphs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(tool.AcceptanceError):
                tool.graph_summary(root)
            output = root / "graphify-out"
            output.mkdir()
            (output / "graph.json").write_text('{"nodes":[],"links":[]}')
            with self.assertRaises(tool.AcceptanceError):
                tool.graph_summary(root)

    def test_clean_environment_excludes_model_keys(self):
        env = tool.clean_env()
        self.assertNotIn("OPENAI_API_KEY", env)
        self.assertNotIn("ANTHROPIC_API_KEY", env)
        self.assertEqual(env["PYTHONDONTWRITEBYTECODE"], "1")


if __name__ == "__main__":
    unittest.main()
