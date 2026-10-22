"""Cross-platform offline MCP transport and project-scoped installer regressions."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import toolkit_mcp as mcp  # noqa: E402


class ToolkitMcpTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.project = Path(t.name) / "existing-project"
        self.project.mkdir()
        (self.project / "AGENTS.md").write_text("OWNER_PRIVATE_FIXTURE", encoding="utf-8")

    def _tools(self):
        return mcp.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]

    def _invoke(self, name, **arguments):
        return mcp.handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                           "params": {"name": name, "arguments": arguments}})

    def test_jsonrpc_initialize_and_tools_have_read_only_hints(self):
        response = mcp.handle({"jsonrpc": "2.0", "id": 0, "method": "initialize",
                               "params": {"protocolVersion": "2025-11-25"}})
        self.assertEqual("2025-11-25", response["result"]["protocolVersion"])
        self.assertTrue(response["result"]["instructions"])
        self.assertGreaterEqual(len(self._tools()), 5)
        self.assertTrue(all(v["annotations"]["readOnlyHint"] for v in self._tools()))
        self.assertIsNone(mcp.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}))
        self.assertEqual(-32601, mcp.handle({"jsonrpc": "2.0", "id": 4, "method": "unexpected"})["error"]["code"])

    def test_tools_read_guidance_without_file_changes(self):
        before = (self.project / "AGENTS.md").read_bytes()
        names = mcp._sources()
        self.assertTrue(names)
        skill = sorted(names)[0]
        catalog = self._invoke("toolkit_catalog")
        self.assertIn(skill, catalog["result"]["structuredContent"]["skills"])
        source = self._invoke("toolkit_read_skill", skill=skill)
        self.assertFalse(source["result"].get("isError", False))
        self.assertIn("SOURCE_READ_NOT_CLIENT_ACTIVATION", source["result"]["content"][0]["text"])
        suggestions = self._invoke("toolkit_search_skills", query="quality testing")
        self.assertIn("matches", suggestions["result"]["structuredContent"])
        self._invoke("toolkit_route_task", task="Please test a backend API")
        self.assertEqual(before, (self.project / "AGENTS.md").read_bytes())
        self.assertFalse((self.project / ".adt").exists())

    def test_read_skill_blocks_traversal_and_unknown_name(self):
        skill = sorted(mcp._sources())[0]
        for ref in ("../../AGENTS.md", "references/../../MANIFEST.json",
                    "references\\windows.txt", "/etc/passwd", "references//bad"):
            with self.subTest(ref=ref):
                x = self._invoke("toolkit_read_skill", skill=skill, reference=ref)
                self.assertTrue(x["result"]["isError"])
        self.assertTrue(self._invoke("toolkit_read_skill", skill="none-existing-skill")["result"]["isError"])

    def test_project_preview_is_never_apply(self):
        skill = sorted(mcp._sources())[0]
        preview = self._invoke("toolkit_preview_install", project=str(self.project),
                               layout="codex", skills=[skill])
        self.assertEqual("PREVIEW_ONLY", preview["result"]["structuredContent"]["status"])
        self.assertFalse((self.project / ".adt").exists())
        self.assertFalse((self.project / ".agents").exists())
        status = self._invoke("toolkit_status", project=str(self.project), layout="claude")
        self.assertEqual("READ_ONLY", status["result"]["structuredContent"]["status"])
        self.assertFalse((self.project / ".adt").exists())
        self.assertTrue(self._invoke("toolkit_preview_install", project="../unsafe", layout="codex",
                                     skills=[skill])["result"]["isError"])

    def test_codex_install_preview_apply_idempotence_and_uninstall(self):
        cfg = self.project / ".codex" / "config.toml"
        self.assertEqual("INSTALL", mcp.configure(str(self.project), "codex", apply=False)["action"])
        self.assertFalse(cfg.exists())
        self.assertTrue(mcp.configure(str(self.project), "codex", apply=True)["applied"])
        raw = cfg.read_text(encoding="utf-8")
        self.assertIn("[mcp_servers.ai-development-toolkit]", raw)
        self.assertIn(str((ROOT / "scripts/toolkit_mcp.py").resolve()), raw)
        self.assertEqual("ALREADY_INSTALLED", mcp.configure(str(self.project), "codex", apply=True)["action"])
        self.assertFalse(mcp.configure(str(self.project), "codex", apply=False, remove=True)["applied"])
        self.assertTrue(cfg.exists())
        self.assertTrue(mcp.configure(str(self.project), "codex", apply=True, remove=True)["applied"])
        self.assertNotIn("mcp_servers.ai-development-toolkit", cfg.read_text())
        self.assertEqual("OWNER_PRIVATE_FIXTURE", (self.project / "AGENTS.md").read_text())

    def test_claude_merge_existing_servers_refuses_foreign_entry(self):
        cfg = self.project / ".mcp.json"
        existing = {"mcpServers": {"other-provider": {"command": "echo", "args": ["hello"]}}}
        cfg.write_text(json.dumps(existing), encoding="utf-8")
        mcp.configure(str(self.project), "claude", apply=False)
        self.assertEqual(existing, json.loads(cfg.read_text()))
        mcp.configure(str(self.project), "claude", apply=True)
        current = json.loads(cfg.read_text())
        self.assertIn("other-provider", current["mcpServers"])
        self.assertIn(mcp.NAME, current["mcpServers"])
        current["mcpServers"][mcp.NAME]["command"] = "other-command"
        cfg.write_text(json.dumps(current), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "refusing overwrite"):
            mcp.configure(str(self.project), "claude", apply=True)
        with self.assertRaisesRegex(ValueError, "refusing overwrite"):
            mcp.configure(str(self.project), "claude", apply=True, remove=True)

    def test_bad_codex_config_is_preserved(self):
        cfg = self.project / ".codex" / "config.toml"
        cfg.parent.mkdir()
        cfg.write_text("[invalid\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            mcp.configure(str(self.project), "codex", apply=True)
        self.assertEqual("[invalid\n", cfg.read_text())

    def test_symlink_target_refusal_without_write(self):
        actual = self.project.parent / "real-project"
        actual.mkdir()
        link = self.project.parent / "linked-project"
        try:
            link.symlink_to(actual, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("Symlinks cannot be created on this runner")
        with self.assertRaisesRegex(ValueError, "Linked"):
            mcp.configure(str(link), "claude", apply=True)
        self.assertFalse((actual / ".mcp.json").exists())

    def test_stdlib_stdio_real_process(self):
        request = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-11-25"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "toolkit_search_skills", "arguments": {"query": "frontend"}}},
        ]
        p = subprocess.run([sys.executable, str(ROOT / "scripts/toolkit_mcp.py"), "serve"],
                           input="\n".join(json.dumps(x) for x in request) + "\n",
                           text=True, capture_output=True, timeout=12, check=True)
        data = [json.loads(line) for line in p.stdout.strip().splitlines()]
        self.assertEqual([1, 2, 3], [x["id"] for x in data])
        self.assertIn("tools", data[1]["result"])
        self.assertIn("matches", data[2]["result"]["structuredContent"])
        self.assertEqual("", p.stderr)


if __name__ == "__main__":
    unittest.main()
