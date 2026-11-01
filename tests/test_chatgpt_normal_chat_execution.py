"""Offline contract for ChatGPT Toolkit normal-chat execution guidance (#499).

These source assertions cannot prove that a connected app was called at runtime.
"""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "integrations/chatgpt-plugin/ai-development-toolkit"
ROUTER = PLUGIN / "skills/toolkit-task-router"
EXECUTION = ROUTER / "references/NORMAL_CHAT_EXECUTION.md"


class ChatGPTNormalChatTests(unittest.TestCase):
    def test_router_explicitly_uses_normal_chat_tools(self):
        text = (ROUTER / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("NORMAL_CHAT_EXECUTION.md", text)
        self.assertIn("Ordinary Chat direct execution (no Work)", text)
        self.assertIn("host tools and connected app actions", text)
        self.assertIn("plugin remains an instruction package", text)
        self.assertIn("BLOCKED", text)

    def test_execution_reference_uses_real_apps_not_fake_shell(self):
        text = EXECUTION.read_text(encoding="utf-8")
        for expected in (
            "ChatGPT Work and Codex are **not prerequisites**",
            "GitHub app",
            "Hermes Agent",
            "immutable revision",
            "No Work and zero-cost boundary",
            "account-specific message/tool limits",
            "user visual acceptance",
            "DEVICE_OFFLINE",
            "NO_AUTHORIZED_WRITE_APP",
            "REFERENCE_ONLY",
            "Do not silently invoke paid",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_native_chatgpt_sandbox_is_an_actual_execution_option(self):
        router = (ROUTER / "SKILL.md").read_text(encoding="utf-8")
        reference = EXECUTION.read_text(encoding="utf-8")
        self.assertIn("native ChatGPT Python/container/browser sandbox", router)
        self.assertIn("Host sandbox first", reference)
        self.assertIn("Python 3.13, Node.js 22, Git, Chromium and Playwright", reference)
        self.assertIn("single-session observation", reference)
        self.assertIn("0 horizontal overflow", reference)
        self.assertIn("0 external requests", reference)
        self.assertIn("BROWSER_EXECUTED", reference)
        self.assertIn("original-skill L5 proof", reference)
        self.assertIn("Do not auto-download engine binaries", reference)
        self.assertIn("Never put user design files in Toolkit", reference)

    def test_existing_plugin_source_does_not_advertise_fictitious_tools(self):
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        capabilities = manifest["extensions"]["com.openai"]["interface"]["capabilities"]
        self.assertEqual([], capabilities)
        self.assertNotIn("mcpServers", manifest)
        self.assertEqual("ai-development-toolkit", manifest["name"])

    def test_routing_ref_exists_and_declares_no_work(self):
        routing = (ROUTER / "references/ROUTING.md").read_text(encoding="utf-8")
        self.assertIn("NORMAL_CHAT_EXECUTION.md", routing)
        self.assertIn("instead of redirecting the user to Work or Codex", routing)

    def test_skill_source_is_not_native_execution_evidence(self):
        text = EXECUTION.read_text(encoding="utf-8")
        self.assertIn("A URL = `REFERENCE_ONLY`", text)
        self.assertIn("a source read = `LOADED`", text)
        self.assertIn("an actual tool invocation requires a verifiable tool result", text)


if __name__ == "__main__":
    unittest.main()
