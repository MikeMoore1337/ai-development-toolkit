"""Offline UX/UI evaluation receipts. Synthetic assets do not prove visual quality."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("ux_ui_evals", ROOT / "scripts" / "ux_ui_evals.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def minimal_png(red: int, width: int = 1, height: int = 1) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return (struct.pack("!I", len(data)) + kind + data
                + struct.pack("!I", zlib.crc32(kind + data) & 0xffffffff))
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = b"\x00" + bytes([red, 0, 0]) * width
    pixels = zlib.compress(row * height, level=6)
    return header + chunk(b"IHDR", ihdr) + chunk(b"IDAT", pixels) + chunk(b"IEND", b"")


class UXUIEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenarios = module.catalog(ROOT)

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def asset(self, name, kind, purpose, viewport):
        path = self.root / name
        if kind == "PNG_CAPTURE":
            width, height = (int(x) for x in viewport.split("x"))
            path.write_bytes(minimal_png((len(name) * 17) % 250, width, height))
        else:
            path.write_text(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 500"><rect width="400" height="500" /><text>{name}</text></svg>',
                encoding="utf-8")
        return {"id": name, "purpose": purpose, "kind": kind, "viewport": viewport,
                "path": name}

    def request(self, scenario_id="new-site", with_art=False):
        s = self.scenarios[scenario_id]
        reviews = [{"id": item, "status": "NOT_REVIEWED", "rationale": ""}
                   for item in s["criteria"]]
        directions = [
            {"id": "editorial", "layout_signature": "asymmetric photo spread",
             "information_architecture": "story then catalog"},
            {"id": "market", "layout_signature": "vertical market stalls",
             "information_architecture": "ripeness selector then basket"},
            {"id": "botanical", "layout_signature": "reference atlas panels",
             "information_architecture": "origin map then variety guide"},
        ] if s["needs_three"] else []
        payload = {
            "schema_version": 1, "scenario_id": scenario_id,
            "design_authority": "Current project design contract, UNVERIFIED fixture",
            "directions": directions,
            "chosen_direction": "market" if directions else None,
            "rejected_directions": ["editorial", "botanical"] if directions else [],
            "visual_assets": [],
            "template_risks": [
                "Interchangeable SaaS card grid for a food experience",
                "Invented social proof and misleading price claims",
                "Decorative generic gradients instead of product imagery",
            ] if directions else [],
            "manual_reviews": reviews,
            "owner_approval": "PENDING",
            "implementation_status": "NOT_STARTED",
        }
        if with_art:
            if directions:
                for i, direction in enumerate(directions):
                    payload["visual_assets"].append(self.asset(
                        f"wire{i}.svg", "SVG_SOURCE",
                        "wireframe:" + direction["id"], "400x500"))
            payload["visual_assets"].append(self.asset(
                "desktop.png", "PNG_CAPTURE", "winner:desktop", "1440x900"))
            payload["visual_assets"].append(self.asset(
                "mobile.png", "PNG_CAPTURE", "winner:mobile", "390x844"))
        return payload

    def test_inventory_has_four_bilingual_scenarios_and_no_saas_color_ban(self):
        self.assertEqual(module.CASES, set(self.scenarios))
        for case in self.scenarios.values():
            self.assertTrue(case["request_en"])
            self.assertTrue(case["request_ru"])
            self.assertIn("accessibility", case["criteria"])
            self.assertEqual("HUMAN_VISUAL_REVIEW_REQUIRED", case["expected_gate"])

    def test_no_render_cannot_claim_approval_ready(self):
        for case in self.scenarios:
            with self.subTest(case=case):
                report = module.audit(self.request(case), self.root, self.scenarios)
                self.assertEqual("VISUAL_PACKAGE_MISSING", report["gate"])
                self.assertEqual("NOT_VERIFIED", report["independent_visual_quality"])
                self.assertEqual("NOT_TESTED", report["working_interactions"])
                self.assertEqual("NOT_STARTED", report["implementation_status"])

    def test_three_distinct_visual_sources_still_require_human_review(self):
        result = module.audit(self.request(with_art=True), self.root, self.scenarios)
        self.assertEqual("AWAITING_HUMAN_VISUAL_REVIEW", result["gate"])
        self.assertTrue(result["comparable_three_artifacts"])
        self.assertTrue(result["desktop_mobile_present"])
        self.assertEqual(9, result["manual_review_pending"])
        self.assertEqual("PENDING", result["owner_approval"])
        self.assertEqual("NOT_VERIFIED", result["independent_visual_quality"])
        self.assertTrue(all(
            x["verification"].endswith("NOT_OBSERVED")
            for x in result["asset_digests"] if x["kind"] == "SVG_SOURCE"))

    def test_same_image_reused_for_three_concepts_never_counts_as_comparison(self):
        item = self.request(with_art=True)
        original = (self.root / "wire0.svg").read_bytes()
        for index in (1, 2):
            (self.root / f"wire{index}.svg").write_bytes(original)
        report = module.audit(item, self.root, self.scenarios)
        self.assertEqual("VISUAL_PACKAGE_MISSING", report["gate"])
        self.assertFalse(report["comparable_three_artifacts"])

    def test_mismatched_sketch_viewports_block_comparison(self):
        item = self.request(with_art=True)
        item["visual_assets"][1]["viewport"] = "500x600"
        with self.assertRaisesRegex(module.EvidenceError, "SVG viewBox does not match"):
            module.audit(item, self.root, self.scenarios)

    def test_palette_swaps_and_duplicate_risks_fail_closed(self):
        x = self.request()
        x["directions"][1]["layout_signature"] = x["directions"][0]["layout_signature"]
        with self.assertRaisesRegex(module.EvidenceError, "Palette-only"):
            module.audit(x, self.root, self.scenarios)
        y = self.request()
        y["template_risks"][2] = y["template_risks"][0]
        with self.assertRaisesRegex(module.EvidenceError, "Three distinct"):
            module.audit(y, self.root, self.scenarios)

    def test_fake_owner_acceptance_or_implementation_rejected(self):
        report = self.request("minor-ui-fix", with_art=True)
        report["owner_approval"] = "OWNER_ACCEPTED"
        with self.assertRaisesRegex(module.EvidenceError, "owner approval"):
            module.audit(report, self.root, self.scenarios)
        report["owner_approval"] = "PENDING"
        report["implementation_status"] = "IMPLEMENTED"
        with self.assertRaisesRegex(module.EvidenceError, "cannot claim UI implementation"):
            module.audit(report, self.root, self.scenarios)

    def test_review_needs_rationale_and_never_certifies_accessibility(self):
        report = self.request("responsive-accessibility", with_art=True)
        report["manual_reviews"][0]["status"] = "ACCEPT"
        with self.assertRaisesRegex(module.EvidenceError, "specific rationale"):
            module.audit(report, self.root, self.scenarios)
        report["manual_reviews"][0]["rationale"] = "Checked focus order using keyboard input."
        result = module.audit(report, self.root, self.scenarios)
        self.assertEqual("NOT_TESTED", result["accessibility_conformance"])
        self.assertEqual(1, result["manual_review_declared"])
        report["manual_reviews"][0]["status"] = "REVISE"
        self.assertEqual("NEEDS_DESIGN_REVISION",
                         module.audit(report, self.root, self.scenarios)["gate"])

    def test_small_png_cannot_claim_desktop_viewport(self):
        path = self.root / "fraud.png"
        path.write_bytes(minimal_png(11, 1, 1))
        record = {"id": "fraud", "purpose": "winner:desktop",
                  "kind": "PNG_CAPTURE", "viewport": "1440x900", "path": "fraud.png"}
        with self.assertRaisesRegex(module.EvidenceError, "dimensions do not match"):
            module.asset_record(record, self.root)

    def test_html_source_is_not_automatically_rendered_winner(self):
        report = self.request("minor-ui-fix", with_art=True)
        (self.root / "desktop.png").unlink()
        (self.root / "desktop.html").write_text("<!doctype html><html><body>Preview</body></html>",
                                                 encoding="utf-8")
        for artifact in report["visual_assets"]:
            if artifact["purpose"] == "winner:desktop":
                artifact.update(path="desktop.html", kind="HTML_SOURCE")
        result = module.audit(report, self.root, self.scenarios)
        self.assertEqual("VISUAL_PACKAGE_MISSING", result["gate"])
        self.assertFalse(result["desktop_mobile_present"])

    def test_symlink_traversal_and_missing_artifacts_rejected(self):
        r = self.request("minor-ui-fix")
        for name in ("../secret.png", "/tmp/demo.png", "bad//path.png", "C:/temp/a.png"):
            bad = {"id": "bad", "purpose": "winner:desktop", "path": name,
                   "viewport": "1440x900", "kind": "PNG_CAPTURE"}
            with self.subTest(name=name):
                with self.assertRaisesRegex(module.EvidenceError, "Unsafe"):
                    module.asset_record(bad, self.root)
        bad = {"id": "x", "purpose": "winner:desktop", "path": "absent.png",
               "viewport": "1440x900", "kind": "PNG_CAPTURE"}
        with self.assertRaisesRegex(module.EvidenceError, "missing"):
            module.asset_record(bad, self.root)
        outside = self.root / "outside"
        outside.write_bytes(minimal_png(1))
        try:
            (self.root / "shortcut.png").symlink_to(outside)
        except (OSError, NotImplementedError):
            pass  # Windows without symlink privilege still tests traversal/missing files.
        else:
            bad["path"] = "shortcut.png"
            with self.assertRaisesRegex(module.EvidenceError, "Symlink"):
                module.asset_record(bad, self.root)

    def test_small_fix_is_exempt_from_three_concepts_but_needs_visual_evidence(self):
        item = self.request("minor-ui-fix", with_art=True)
        result = module.audit(item, self.root, self.scenarios)
        self.assertEqual("AWAITING_HUMAN_VISUAL_REVIEW", result["gate"])
        self.assertFalse(result["comparable_three_artifacts"])
        item["directions"] = [{"id": "needless"}]
        with self.assertRaisesRegex(module.EvidenceError, "must not fabricate"):
            module.audit(item, self.root, self.scenarios)


if __name__ == "__main__":
    unittest.main()
