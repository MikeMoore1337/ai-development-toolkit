"""Issue #265: deterministic offline diagram pilot; no network or models."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from diagram_pilot import main, render, validate

EXAMPLE = json.loads((ROOT / "docs/examples/diagram-pilot.synthetic.json").read_text(encoding="utf-8"))


class DiagramPilotTests(unittest.TestCase):
    def sample(self):
        return copy.deepcopy(EXAMPLE)

    def test_sample_is_valid_and_contains_no_external_runtime(self):
        sample = self.sample()
        self.assertIs(validate(sample), sample)
        page = render(sample)
        self.assertEqual(page, render(sample))
        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg" role="img"', page)
        self.assertIn("default-src 'none'", page)
        self.assertIn("Происхождение элементов схемы", page)
        self.assertEqual(page.count("Synthetic fixture: scenario D-01"), 7)
        self.assertNotIn("<script", page)
        self.assertNotIn("<iframe", page)
        self.assertNotIn("<link ", page)
        self.assertNotIn("fetch(", page)

    def test_html_and_attributes_escaped(self):
        sample = self.sample()
        sample["title"] = "<script>alert('x')</script>"
        sample["nodes"][0]["label"] = '<img src=x onerror="alert(1)">'
        sample["nodes"][0]["evidence"] = '<a href="https://attacker.invalid">unsafe</a>'
        page = render(sample)
        self.assertNotIn("<script>", page)
        self.assertNotIn("<img ", page)
        self.assertNotIn("<a href=", page)
        self.assertIn("&lt;script&gt;", page)
        self.assertIn("&lt;img", page)
        self.assertIn("&lt;a href=", page)

    def test_reject_invalid_graph_inputs(self):
        cases = []
        v = self.sample()
        v["nodes"][1]["id"] = "client"
        cases.append(v)
        v = self.sample()
        v["nodes"][1]["evidence"] = ""
        cases.append(v)
        v = self.sample()
        v["nodes"][0]["column"] = True
        cases.append(v)
        v = self.sample()
        v["edges"][0]["to"] = "missing"
        cases.append(v)
        v = self.sample()
        v["edges"][0]["from"] = "api"
        cases.append(v)
        v = self.sample()
        v["edges"].append(copy.deepcopy(v["edges"][0]))
        cases.append(v)
        v = self.sample()
        v["accent"] = "red; background:url(https://example.org)"
        cases.append(v)
        v = self.sample()
        v["title"] += "\n"
        cases.append(v)
        v = self.sample()
        v["nodes"] = []
        cases.append(v)
        v = self.sample()
        v["version"] = True
        cases.append(v)
        for case in cases:
            with self.subTest(case=case):
                with self.assertRaises(ValueError):
                    render(case)

    def test_cli_creates_once_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "diagram.html"
            spec = ROOT / "docs/examples/diagram-pilot.synthetic.json"
            self.assertEqual(0, main([str(spec), "--output", str(output)]))
            original = output.read_text(encoding="utf-8")
            self.assertIn("svg", original)
            self.assertEqual(2, main([str(spec), "--output", str(output)]))
            self.assertEqual(original, output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
