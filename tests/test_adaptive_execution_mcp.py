"""Offline MCP exposure for advisor - no agents or network."""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "scripts" / "toolkit_mcp.py"

class AdvisorMcpTests(unittest.TestCase):
    def request(self):
        return {"task_id":"mcp-task","locale":"ru","current_model":"A",
                "available_models":["A","B"],"inventory_status":"VERIFIED",
                "inventory_revision":"1","switching":"VERIFIED","delegation":"UNKNOWN",
                "zero_incremental_cost_verified":True,"signals":["architecture"]}

    def call(self, name, arguments):
        message = {"jsonrpc":"2.0","id":1,"method":"tools/call",
                   "params":{"name":name,"arguments":arguments}}
        with subprocess.Popen([sys.executable, str(SERVER), "serve"],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE, text=True, encoding="utf-8",
                              cwd=ROOT, env={**os.environ, "PYTHONIOENCODING": "utf-8"}) as process:
            stdout, stderr = process.communicate(json.dumps(message)+"\n", timeout=15)
            self.assertEqual(0, process.returncode, stderr)
        return json.loads(stdout.strip().splitlines()[-1])["result"]

    def test_explanation_is_not_approval(self):
        value = self.call("toolkit_advise_execution",{"request":self.request()})
        self.assertEqual("NOT_RUN", value["structuredContent"]["execution"])
        self.assertTrue(value["structuredContent"]["user_selection_required"])

    def test_mcp_rejects_missing_consent(self):
        value = self.call("toolkit_check_execution_consent",{"request":self.request()})
        self.assertTrue(value["isError"])

    def test_mcp_confirms_policy_but_never_executes(self):
        consent = {"task_id":"mcp-task","inventory_revision":"1",
                   "mode":"AUTO_OPT_IN","approved_models":["B"],"max_extra_calls":1}
        value = self.call("toolkit_check_execution_consent",
                          {"request":self.request(),"consent":consent})
        self.assertEqual("NOT_RUN",value["structuredContent"]["execution"])
        self.assertTrue(value["structuredContent"]["extra_calls_authorized"])

if __name__ == "__main__":
    unittest.main()
