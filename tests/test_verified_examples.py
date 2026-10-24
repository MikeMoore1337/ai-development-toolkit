"""Four executable, safe source-only examples (no LLM or external clients)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = (
    ("scripts/adt.py", "--json", "profile", "list"),
    ("scripts/skill_routing_eval.py", "--strict"),
    ("scripts/skill_routing_eval.py", "--holdout", "fixtures/skill_routing_untuned_20261024.json"),
    ("scripts/validate_qa_orchestration.py", "fixtures/qa_orchestra_valid.json"),
)


class VerifiedExamplesTests(unittest.TestCase):
    def test_four_examples_exist_in_both_languages(self):
        docs = [
            (ROOT / "docs/VERIFIED_EXAMPLES.md").read_text(encoding="utf-8"),
            (ROOT / "docs/ru/VERIFIED_EXAMPLES.md").read_text(encoding="utf-8"),
        ]
        for content in docs:
            for command in COMMANDS:
                with self.subTest(command=command):
                    self.assertIn("python " + " ".join(command), content)
            for qualifier in ("NOT_RUN", "NOT_TESTED", "NOT_OBSERVED", "NOT_VERIFIED"):
                self.assertIn(qualifier, content)

    def test_all_four_commands_run_without_source_mutation(self):
        tracked = [ROOT / "MANIFEST.json", ROOT / "requirements-dev.txt",
                   ROOT / "fixtures/skill_routing_untuned_20261024.json",
                   ROOT / "fixtures/qa_orchestra_valid.json"]
        before = {str(path): path.read_bytes() for path in tracked}
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
        output = []
        for args in COMMANDS:
            with self.subTest(args=args):
                cp = subprocess.run(
                    [sys.executable, *args], cwd=ROOT, env=env,
                    capture_output=True, encoding="utf-8", errors="replace",
                    timeout=45, check=False,
                )
                self.assertEqual(0, cp.returncode, (cp.stdout + cp.stderr)[-1000:])
                output.append(cp.stdout)
        self.assertIn("profiles", json.loads(output[0]))
        self.assertEqual(16, json.loads(output[2])["count"])
        self.assertEqual("NOT_OBSERVED", json.loads(output[2])["client_skill_selection"])
        self.assertIn("PASS", output[3])
        self.assertEqual(before, {str(path): path.read_bytes() for path in tracked})


if __name__ == "__main__":
    unittest.main()
