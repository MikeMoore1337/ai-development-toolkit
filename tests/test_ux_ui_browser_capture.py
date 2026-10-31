"""Synthetic, offline tests of browser capture planning and artifact receipts."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("visual_capture", ROOT / "scripts/ux_ui_browser_capture.py")
visual = importlib.util.module_from_spec(spec)
spec.loader.exec_module(visual)


def png(width: int, height: int, shade: int = 128) -> bytes:
    def chunk(tag, data):
        return struct.pack("!I", len(data)) + tag + data + struct.pack(
            "!I", zlib.crc32(tag + data) & 0xffffffff)
    pixels = zlib.compress((b"\x00" + bytes([shade, shade, shade]) * width) * height)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(
        "!IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", pixels)
        + chunk(b"IEND", b""))


FakePlaywrightError = type("PlaywrightError", (Exception,), {})


class FakeBrowser:
    version = "test-0"

    def __init__(self, overflow=0):
        self.overflow = overflow
        self.contexts = []

    def new_context(self, **settings):
        context = FakeContext(settings, self.overflow)
        self.contexts.append(context)
        return context

    def close(self):
        pass


class FakeContext:
    def __init__(self, settings, overflow):
        self.settings, self.overflow = settings, overflow
        self.route_guard = None
        self.socket_guard = None

    def route(self, _pattern, fn):
        self.route_guard = fn

    def route_web_socket(self, _pattern, fn):
        self.socket_guard = fn

    def new_page(self):
        return FakePage(self)

    def close(self):
        pass


class FakePage:
    def __init__(self, context):
        self.context = context

    def on(self, _event, _handler):
        pass

    def goto(self, source, **_settings):
        self.source = source

    def set_content(self, html, **_settings):
        self.source = html

    def close(self):
        pass

    def evaluate(self, _js):
        return {"viewport_width": self.context.settings["viewport"]["width"],
                "document_width": self.context.settings["viewport"]["width"] + self.context.overflow,
                "horizontal_overflow_px": self.context.overflow,
                "small_targets_under_24px": [], "body_text_characters": 60}

    def screenshot(self, *, path, **_settings):
        viewport = self.context.settings["viewport"]
        Path(path).write_bytes(png(viewport["width"], viewport["height"], sum(self.source.encode()) % 250))


class FakePlaywright:
    def __init__(self, overflow=0):
        self.browser = FakeBrowser(overflow)
        self.chromium = SimpleNamespace(launch=lambda **_kw: self.browser)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        pass


class BrowserCaptureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        for name in "abc":
            (self.source / (name + ".html")).write_text(
                f"<!doctype html><html><body><h1>Preview {name}</h1></body></html>", encoding="utf-8")
        self.plan = {"schema_version": 1, "scenario_id": "new-site", "captures": [
            {"purpose": "wireframe:" + x, "source": x + ".html", "viewport": "400x600"}
            for x in "abc"
        ] + [
            {"purpose": "winner:desktop", "source": "a.html", "viewport": "1440x900"},
            {"purpose": "winner:mobile", "source": "a.html", "viewport": "390x844"},
        ]}

    def test_accepts_three_sourced_sketches_and_responsive_winner(self):
        scenario, items = visual.parse_plan(self.plan, self.source)
        self.assertEqual("new-site", scenario)
        self.assertEqual(5, len(items))
        self.assertTrue(items[0]["url"].startswith("file:"))
        self.assertEqual("LOCAL_HTML", items[0]["origin"])

    def test_rejects_missing_or_duplicate_directions(self):
        self.plan["captures"][1]["purpose"] = self.plan["captures"][0]["purpose"]
        with self.assertRaisesRegex(visual.CaptureError, "Duplicate"):
            visual.parse_plan(self.plan, self.source)
        self.plan["captures"][1]["purpose"] = "wireframe:b"
        self.plan["captures"][1]["viewport"] = "420x600"
        with self.assertRaisesRegex(visual.CaptureError, "equal-sized"):
            visual.parse_plan(self.plan, self.source)

    def test_prevents_unsafe_paths_and_outside_requests(self):
        for source in ("../private.html", "/etc/passwd", "C:/private.html", "http://example.com/", "https://localhost/", "a\\b.html"):
            with self.subTest(source=source):
                self.plan["captures"][0]["source"] = source
                with self.assertRaises(visual.CaptureError):
                    visual.parse_plan(self.plan, self.source)
        self.assertFalse(visual.request_allowed("https://example.com/api", self.source, set()))
        self.assertFalse(visual.request_allowed("http://127.0.0.1:9999/secret", self.source, set()))
        self.assertTrue(visual.request_allowed("http://127.0.0.1:3000/app", self.source,
                                               {"http://127.0.0.1:3000"}))
        self.assertTrue(visual.request_allowed((self.source / "a.html").as_uri(), self.source, set()))
        self.assertFalse(visual.request_allowed((self.root / "secret.txt").as_uri(), self.source, set()))

    def test_canonical_root_alias_walk_terminates(self):
        # A path that resolves inside source_root but has a different lexical
        # ancestor chain previously caused an infinite walk on Windows.
        (self.source / "nested").mkdir()
        alias = self.source / "nested" / ".." / "a.html"
        self.assertTrue(visual._in_root(alias, self.source))
        self.assertFalse(visual._in_root(self.root / "outside.html", self.source))

    def test_rejects_symlink_sources(self):
        target = self.source / "linked.html"
        try:
            target.symlink_to(self.source / "a.html")
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable on this platform")
        self.plan["captures"][0]["source"] = "linked.html"
        with self.assertRaisesRegex(visual.CaptureError, "linked"):
            visual.parse_plan(self.plan, self.source)

    def _run_fake(self, overflow=0):
        fake = FakePlaywright(overflow)
        fake_module = ModuleType("playwright.sync_api")
        fake_module.Error = FakePlaywrightError
        fake_module.sync_playwright = lambda: fake
        with patch.dict(sys.modules, {"playwright.sync_api": fake_module}):
            output = self.root / "captures"
            report = visual.capture(self.plan, self.source, output)
        return report, fake, output

    def test_emits_actual_file_receipts_without_claiming_visual_approval(self):
        report, fake, folder = self._run_fake()
        self.assertEqual("AWAITING_HUMAN_VISUAL_REVIEW", report["gate"])
        self.assertEqual("NOT_VERIFIED", report["visual_quality"])
        self.assertEqual("NOT_REQUESTED", report["owner_approval"])
        self.assertEqual(5, len(report["visual_assets"]))
        self.assertTrue(report["distinct_sketch_files"])
        gallery = (folder / "comparison.html").read_text(encoding="utf-8")
        self.assertEqual(5, gallery.count("<figure>"))
        self.assertIn("wireframe:a", gallery)

        self.assertEqual(5, len(fake.browser.contexts))
        self.assertEqual((390, 844), tuple(fake.browser.contexts[-1].settings["viewport"].values()))
        self.assertTrue(fake.browser.contexts[-1].settings["is_mobile"])
        self.assertEqual(json.loads((folder / "capture_report.json").read_text()), report)
        for asset in report["visual_assets"]:
            self.assertTrue((folder / asset["path"]).is_file())
        with self.assertRaisesRegex(visual.CaptureError, "Output must be a new"):
            visual.capture(self.plan, self.source, folder)

    def test_horizontal_overflow_blocks_automatic_clearance(self):
        report, _fake, _folder = self._run_fake(overflow=37)
        self.assertEqual("NEEDS_LAYOUT_REVIEW", report["gate"])
        self.assertEqual(37, report["diagnostics"][0]["layout"]["horizontal_overflow_px"])

    def test_identical_rendered_sketches_require_layout_review(self):
        class SameImagePage(FakePage):
            def screenshot(self, *, path, **_settings):
                viewport = self.context.settings["viewport"]
                Path(path).write_bytes(png(viewport["width"], viewport["height"]))
        with patch.object(FakeContext, "new_page", lambda ctx: SameImagePage(ctx)):
            report, _fake, folder = self._run_fake()
        self.assertEqual("NEEDS_LAYOUT_REVIEW", report["gate"])
        self.assertFalse(report["distinct_sketch_files"])
        self.assertTrue((folder / "comparison.html").is_file())

    def test_dangling_output_symlink_rejected_without_overwrite(self):
        target = self.root / "absent-output"
        try:
            (self.root / "captures").symlink_to(target, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Cannot create symlink on this platform")
        with self.assertRaisesRegex(visual.CaptureError, "Output must be a new"):
            self._run_fake()
        self.assertTrue((self.root / "captures").is_symlink())

    def test_blocked_local_navigation_uses_explicit_inline_fallback(self):
        with patch.object(FakePage, "goto", side_effect=FakePlaywrightError(
                "Page.goto: net::ERR_BLOCKED_BY_ADMINISTRATOR")):
            report, _fake, folder = self._run_fake()
        self.assertTrue((folder / "comparison.html").is_file())
        self.assertTrue(all(item["inline_html_fallback"] for item in report["diagnostics"]))
        self.assertEqual("AWAITING_HUMAN_VISUAL_REVIEW", report["gate"])

    def test_local_fallback_does_not_decode_windows_file_uri(self):
        with patch.object(FakePage, "goto", side_effect=FakePlaywrightError(
                "Page.goto: net::ERR_BLOCKED_BY_ADMINISTRATOR")):
            with patch.object(visual, "url2pathname", side_effect=AssertionError(
                    "Do not reparse a validated local file URI")):
                report, _fake, _folder = self._run_fake()
        self.assertTrue(all(x["inline_html_fallback"] for x in report["diagnostics"]))

    def test_inline_fallback_never_applies_to_loopback_http(self):
        self.plan["captures"][0]["source"] = "http://127.0.0.1:6000/preview"
        with patch.object(FakePage, "goto", side_effect=FakePlaywrightError(
                "Page.goto: net::ERR_BLOCKED_BY_ADMINISTRATOR")):
            with self.assertRaisesRegex(visual.CaptureError, "BROWSER_RENDER_FAILED"):
                self._run_fake()
        self.assertFalse((self.root / "captures").exists())

    def test_wrong_mobile_layout_viewport_requires_review(self):
        original = FakePage.evaluate
        def wrong_mobile(self, js):
            result = original(self, js)
            if self.context.settings["is_mobile"]:
                result["viewport_width"] = 980
                result["document_width"] = 980
            return result
        with patch.object(FakePage, "evaluate", wrong_mobile):
            report, _fake, _folder = self._run_fake()
        self.assertEqual("NEEDS_LAYOUT_REVIEW", report["gate"])
        self.assertEqual(980, report["diagnostics"][-1]["layout"]["viewport_width"])

    def test_tiny_interactive_target_requires_review(self):
        original = FakePage.evaluate
        def tiny_button(self, js):
            result = original(self, js)
            result["small_targets_under_24px"] = ["button"]
            return result
        with patch.object(FakePage, "evaluate", tiny_button):
            report, _fake, _folder = self._run_fake()
        self.assertEqual("NEEDS_LAYOUT_REVIEW", report["gate"])

    def test_minor_fix_does_not_require_three_wireframes(self):
        self.plan["scenario_id"] = "minor-ui-fix"
        self.plan["captures"] = self.plan["captures"][-2:]
        self.assertEqual(2, len(visual.parse_plan(self.plan, self.source)[1]))


if __name__ == "__main__":
    unittest.main()
