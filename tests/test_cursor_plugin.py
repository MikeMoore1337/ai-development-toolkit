"""Cursor plugin packaging and reversible local installation contracts."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "integrations" / "cursor-plugin"
MANAGER = PLUGIN / "scripts" / "manage.py"
LAUNCHER = PLUGIN / "scripts" / "launch_mcp.py"

class CursorPluginContract(unittest.TestCase):
    def test_manifest_and_mcp(self):
        manifest = json.loads((PLUGIN / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))
        config = json.loads((PLUGIN / "mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "ai-development-toolkit")
        self.assertEqual(manifest["mcpServers"], "./mcp.json")
        self.assertEqual(set(config["mcpServers"]), {"adt-personal"})
        self.assertEqual(config["mcpServers"]["adt-personal"]["args"], ["${CURSOR_PLUGIN_ROOT}/scripts/launch_mcp.py"])
        self.assertEqual(config["mcpServers"]["adt-personal"]["type"], "stdio")
        self.assertNotIn("token", json.dumps(config).lower())
        self.assertEqual(len(list((PLUGIN / "skills").glob("*/SKILL.md"))), 4)
        self.assertEqual(len(list((PLUGIN / "commands").glob("*.md"))), 4)
        for p in (PLUGIN / "skills").glob("*/SKILL.md"):
            value = p.read_text(encoding="utf-8")
            self.assertTrue(value.startswith("---\nname: "))
            self.assertIn("\ndescription:", value)
        for p in (PLUGIN / "commands").glob("*.md"):
            self.assertIn("description:", p.read_text(encoding="utf-8"))

    def run_manager(self, *args, source=PLUGIN, target=None, state=None):
        command = [sys.executable, str(MANAGER), *args, "--source", str(source)]
        if target:
            command.extend(["--target", str(target)])
        if state:
            command.extend(["--state-dir", str(state)])
        p = subprocess.run(command, capture_output=True, text=True, timeout=35)
        return p.returncode, json.loads(p.stdout)

    def test_install_update_rollback_and_drift(self):
        with tempfile.TemporaryDirectory() as scratch:
            home = Path(scratch)
            target = home / "plugins" / "ai-development-toolkit"
            state = home / "state"
            status, preview = self.run_manager("install", target=target, state=state)
            self.assertEqual((status, preview["status"]), (0, "PREVIEW"))
            self.assertFalse(target.exists())
            status, installed = self.run_manager("install", "--apply", target=target, state=state)
            self.assertEqual((status, installed["status"]), (0, "INSTALLED"))
            status, info = self.run_manager("status", target=target, state=state)
            self.assertEqual((status, info["status"]), (0, "MANAGED_CLEAN"))
            status, repeat = self.run_manager("update", "--apply", target=target, state=state)
            self.assertEqual((status, repeat["status"]), (0, "ALREADY_CURRENT"))
            replacement = home / "new-source"
            shutil.copytree(PLUGIN, replacement)
            (replacement / "README.md").write_text("updated help text\n", encoding="utf-8")
            status, result = self.run_manager("update", "--apply", source=replacement, target=target, state=state)
            self.assertEqual((status, result["status"]), (0, "UPDATED"))
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "updated help text\n")
            status, result = self.run_manager("rollback", "--apply", target=target, state=state)
            self.assertEqual((status, result["status"]), (0, "RESTORED_PREVIOUS"))
            self.assertNotEqual((target / "README.md").read_text(encoding="utf-8"), "updated help text\n")
            (target / "README.md").write_text("owner edit\n", encoding="utf-8")
            status, rejected = self.run_manager("update", "--apply", target=target, state=state)
            self.assertEqual((status, rejected["status"]), (2, "BLOCKED"))
            self.assertEqual((target / "README.md").read_text(encoding="utf-8"), "owner edit\n")

    def test_unmanaged_directory_not_overwritten(self):
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / "ai-development-toolkit"
            target.mkdir()
            sentinel = target / "owner.txt"
            sentinel.write_text("keep", encoding="utf-8")
            status, body = self.run_manager("install", "--apply", target=target, state=Path(scratch) / "state")
            self.assertEqual((status, body["status"]), (2, "BLOCKED"))
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_first_install_rollback_removes_only_managed_package(self):
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / "ai-development-toolkit"
            state = Path(scratch) / "state"
            self.assertEqual(self.run_manager("install", "--apply", target=target, state=state)[0], 0)
            status, body = self.run_manager("rollback", "--apply", target=target, state=state)
            self.assertEqual((status, body["status"]), (0, "UNINSTALLED"))
            self.assertFalse(target.exists())

    def test_reuse_existing_global_mcp_installs_without_duplicate(self):
        from unittest.mock import patch
        import importlib.util
        spec = importlib.util.spec_from_file_location('adt_cursor_manage', MANAGER)
        adapter = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'dont_write_bytecode', True):
            spec.loader.exec_module(adapter)
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / "ai-development-toolkit"
            state = Path(scratch) / "state"
            with patch.object(adapter, "has_global_adt_mcp", return_value=True):
                result = adapter.perform_install(PLUGIN, target, state, reuse_global_mcp=True)
                self.assertEqual(result["mcp_mode"], "reuse-global")
                self.assertFalse((target / "mcp.json").exists())
                manifest = json.loads((target / ".cursor-plugin/plugin.json").read_text(encoding="utf-8"))
                self.assertNotIn("mcpServers", manifest)
                status, info = adapter.inspection(target)
                self.assertEqual(status, "MANAGED_CLEAN")
                self.assertEqual(info["mcp_mode"], "reuse-global")
                self.assertEqual(adapter.perform_install(PLUGIN, target, state, reuse_global_mcp=True)["status"], "ALREADY_CURRENT")
                self.assertEqual(adapter.perform_rollback(target, state)["status"], "UNINSTALLED")

    def test_reuse_requires_existing_global_mcp(self):
        from unittest.mock import patch
        import importlib.util
        spec = importlib.util.spec_from_file_location('adt_cursor_manage', MANAGER)
        adapter = importlib.util.module_from_spec(spec)
        with patch.object(sys, 'dont_write_bytecode', True):
            spec.loader.exec_module(adapter)
        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / "ai-development-toolkit"
            with patch.object(adapter, "has_global_adt_mcp", return_value=False):
                with self.assertRaisesRegex(ValueError, "global ADT MCP"):
                    adapter.perform_install(PLUGIN, target, Path(scratch) / "state", reuse_global_mcp=True)
            self.assertFalse(target.exists())

    def test_launcher_doctor_does_not_start_server(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            server = root / "adt_mcp.py"
            server.write_text("raise SystemExit('server must not be executed')\n", encoding="utf-8")
            source = root / "source"
            source.mkdir()
            (source / "MANIFEST.json").write_text("{}", encoding="utf-8")
            env = os.environ.copy()
            env["ADT_PERSONAL_MCP"] = str(server.resolve())
            env["ADT_TOOLKIT_SOURCE"] = str(source.resolve())
            p = subprocess.run([sys.executable, str(LAUNCHER), "--doctor"], env=env,
                               capture_output=True, text=True, timeout=15)
            self.assertEqual(p.returncode, 0, p.stderr)
            result = json.loads(p.stdout)
            self.assertEqual(result["mcp_invocation"], "NOT_RUN")
            self.assertEqual(result["status"], "READY")

if __name__ == "__main__":
    unittest.main()
