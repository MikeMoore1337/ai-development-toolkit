#!/usr/bin/env python3
"""Create real Chromium screenshot evidence from authorized local design previews.

This is an optional renderer for the existing UX/UI Design Orchestra, not an
approval, aesthetic evaluator, remote URL fetcher, or third-party installer.
"""
from __future__ import annotations

import argparse
import hashlib
from html import escape
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import tempfile
from urllib.parse import urlsplit
from urllib.request import url2pathname

SCENARIOS = {"new-site", "substantial-redesign", "minor-ui-fix", "responsive-accessibility"}
PURPOSE = re.compile(r"^(?:wireframe:[a-z0-9][a-z0-9-]{0,48}|winner:(?:desktop|mobile)|state:[a-z0-9][a-z0-9-]{0,48})$")
VIEWPORT = re.compile(r"^([1-9]\d{2,3})x([1-9]\d{2,3})$")
MAX_CAPTURES = 12


class CaptureError(ValueError):
    pass


def _linked(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def _in_root(path: Path, root: Path) -> bool:
    """Reject links within an authorized root, including a linked target file."""
    path = path.absolute()
    root = root.absolute()
    if not path.resolve().is_relative_to(root.resolve()):
        return False
    current = path
    while current != root:
        if _linked(current):
            return False
        current = current.parent
    return not _linked(root)


def _source_uri(source: str, root: Path) -> tuple[str, str]:
    if not isinstance(source, str) or not source or len(source) > 512:
        raise CaptureError("Missing or oversized source")
    parsed = urlsplit(source)
    if parsed.scheme:
        if (parsed.scheme != "http" or parsed.hostname not in {"localhost", "127.0.0.1", "::1"}
                or parsed.username is not None or parsed.password is not None
                or not parsed.netloc or parsed.fragment):
            raise CaptureError("Only explicit loopback HTTP preview URLs are allowed")
        try:
            _ = parsed.port
        except ValueError as exc:
            raise CaptureError("Invalid preview port") from exc
        return source, f"{parsed.scheme}://{parsed.netloc}"
    posix = PurePosixPath(source)
    if (posix.is_absolute() or "\\" in source or ":" in source or "\x00" in source
            or any(part in (".", "..", "") for part in source.split("/"))
            or posix.suffix.lower() != ".html"):
        raise CaptureError("Unsafe local HTML source path")
    path = root.joinpath(*posix.parts)
    if not _in_root(path, root) or not path.is_file():
        raise CaptureError("HTML source missing, linked or outside source root")
    return path.resolve().as_uri(), "LOCAL_HTML"


def parse_plan(raw: object, source_root: Path) -> tuple[str, list[dict]]:
    if (not isinstance(raw, dict) or set(raw) != {"schema_version", "scenario_id", "captures"}
            or raw["schema_version"] != 1 or raw["scenario_id"] not in SCENARIOS):
        raise CaptureError("Invalid browser capture plan")
    if not source_root.is_dir() or _linked(source_root):
        raise CaptureError("Source root missing or linked")
    records = raw["captures"]
    if not isinstance(records, list) or not 2 <= len(records) <= MAX_CAPTURES:
        raise CaptureError("Expected 2-12 visual captures")
    result = []
    for item in records:
        if (not isinstance(item, dict) or set(item) != {"purpose", "source", "viewport"}
                or not isinstance(item["purpose"], str) or not PURPOSE.fullmatch(item["purpose"])
                or not isinstance(item["viewport"], str)):
            raise CaptureError("Malformed capture record")
        size = VIEWPORT.fullmatch(item["viewport"])
        if size is None:
            raise CaptureError("Invalid viewport WxH")
        width, height = map(int, size.groups())
        if not 320 <= width <= 4096 or not 320 <= height <= 4096:
            raise CaptureError("Viewport outside supported range")
        url, origin = _source_uri(item["source"], source_root)
        result.append({"purpose": item["purpose"], "url": url, "origin": origin,
                       "viewport": item["viewport"], "width": width, "height": height})
    purposes = [item["purpose"] for item in result]
    if len(set(purposes)) != len(purposes) or not {"winner:desktop", "winner:mobile"} <= set(purposes):
        raise CaptureError("Duplicate purposes or missing desktop/mobile winners")
    winner_desktop = next(x for x in result if x["purpose"] == "winner:desktop")
    winner_mobile = next(x for x in result if x["purpose"] == "winner:mobile")
    if winner_desktop["width"] < 800 or winner_mobile["width"] > 600:
        raise CaptureError("Winners must use distinct desktop/mobile widths")
    wires = [x for x in result if x["purpose"].startswith("wireframe:")]
    if raw["scenario_id"] in {"new-site", "substantial-redesign"}:
        if len(wires) != 3 or len({x["viewport"] for x in wires}) != 1:
            raise CaptureError("Major design requires three equal-sized wireframe captures")
        if len({x["url"] for x in wires}) != 3:
            raise CaptureError("Wireframes must have three independent source views")
    elif wires:
        raise CaptureError("Minor/a11y scenarios do not fabricate three candidates")
    return raw["scenario_id"], result


def request_allowed(url: str, root: Path, allowed_origins: set[str]) -> bool:
    """Block remote subresources and redirects, even when a local HTML embeds them."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme in {"data", "blob"}:
            return True
        if parsed.scheme == "file":
            path = Path(url2pathname(parsed.path))
            return _in_root(path, root)
        return parsed.scheme == "http" and f"{parsed.scheme}://{parsed.netloc}" in allowed_origins
    except (ValueError, OSError):
        return False


PAGE_METRICS = """() => {
  const doc = document.documentElement;
  const body = document.body;
  const width = window.innerWidth;
  const documentWidth = Math.max(doc.scrollWidth, body ? body.scrollWidth : 0);
  const smallTargets = [];
  for (const node of document.querySelectorAll('button,a,input,select,textarea,[role="button"]')) {
    const rect = node.getBoundingClientRect();
    const style = getComputedStyle(node);
    if (style.display === 'none' || style.visibility === 'hidden' || rect.width === 0 || rect.height === 0) continue;
    if (rect.bottom <= 0 || rect.top >= window.innerHeight || rect.right <= 0 || rect.left >= width) continue;
    if (rect.width < 24 || rect.height < 24) smallTargets.push(node.tagName.toLowerCase());
    if (smallTargets.length >= 20) break;
  }
  return {
    viewport_width: width,
    document_width: documentWidth,
    horizontal_overflow_px: Math.max(0, documentWidth - width),
    small_targets_under_24px: smallTargets,
    body_text_characters: body ? body.innerText.trim().length : 0
  };
}"""


def comparison_html(assets: list[dict]) -> str:
    """One read-only local gallery for side-by-side human visual comparison."""
    panels = []
    for item in assets:
        label = escape(item["purpose"])
        path = escape(item["path"], quote=True)
        panels.append(f'<figure><img src="{path}" alt="{label}" loading="lazy"><figcaption>{label}</figcaption></figure>')
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>UX/UI comparison - local evidence</title>'
            '<style>body{margin:24px;font:16px system-ui,sans-serif;color:#212121;background:#f4f4f4}'
            'h1{font-size:24px}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:16px}'
            'figure{margin:0;padding:12px;border:1px solid #bbb;background:white;border-radius:8px;min-width:0}'
            'img{display:block;max-width:100%;height:auto;margin:auto}figcaption{margin-top:12px;font-weight:600;overflow-wrap:anywhere}'
            '</style><h1>UX/UI browser capture comparison</h1><main>'
            + ''.join(panels) + '</main></html>\n')


def capture(plan: dict, source_root: Path, output: Path, *, executable: str | None = None) -> dict:
    scenario, records = parse_plan(plan, source_root)
    toolkit_root = Path(__file__).resolve().parents[1]
    if (not output.parent.is_dir() or output.exists() or _linked(output.parent)
            or output.resolve().is_relative_to(toolkit_root)):
        raise CaptureError("Output must be a new directory outside Toolkit with an existing parent")
    try:
        from playwright.sync_api import Error as PlaywrightError, sync_playwright
    except ImportError as exc:
        raise CaptureError("PLAYWRIGHT_UNAVAILABLE: use an authorized local Playwright installation") from exc
    stage = Path(tempfile.mkdtemp(prefix="adt-visual-", dir=output.parent))
    artifacts = []
    diagnostics = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True, executable_path=executable)
            try:
                origins = {x["origin"] for x in records if x["origin"] != "LOCAL_HTML"}
                for index, item in enumerate(records):
                    mobile = item["width"] <= 600
                    context = browser.new_context(
                        viewport={"width": item["width"], "height": item["height"]},
                        device_scale_factor=1, is_mobile=mobile, has_touch=mobile,
                        reduced_motion="reduce")
                    blocked = [0]
                    errors = [0]
                    try:
                        def route_guard(route):
                            if request_allowed(route.request.url, source_root, origins):
                                route.continue_()
                            else:
                                blocked[0] += 1
                                route.abort()
                        # Chromium cannot reliably route file: navigation. Route only
                        # network traffic and explicitly deny remote HTTP(s) requests.
                        context.route(re.compile(r"^https?://"), route_guard)
                        if not hasattr(context, "route_web_socket"):
                            raise CaptureError("WebSocket blocking unavailable in this Playwright version")
                        context.route_web_socket("**/*", lambda socket: socket.close())
                        page = context.new_page()
                        page.on("pageerror", lambda _error: errors.__setitem__(0, errors[0] + 1))
                        page.goto(item["url"], wait_until="domcontentloaded", timeout=20000)
                        metrics = page.evaluate(PAGE_METRICS)
                        name = f"{index + 1:02d}-{item['purpose'].replace(':', '-')}.png"
                        png = stage / name
                        page.screenshot(path=str(png), animations="disabled", timeout=20000)
                        artifacts.append({"id": f"capture-{index + 1}", "purpose": item["purpose"],
                                          "path": name, "kind": "PNG_CAPTURE",
                                          "viewport": item["viewport"]})
                        diagnostics.append({"purpose": item["purpose"], "source_type": (
                            "LOCAL_HTML" if item["origin"] == "LOCAL_HTML" else "LOCAL_DEV_SERVER"),
                            "sha256": hashlib.sha256(png.read_bytes()).hexdigest(),
                            "layout": metrics, "blocked_requests": blocked[0], "page_errors": errors[0]})
                    finally:
                        context.close()
                browser_version = browser.version
            finally:
                browser.close()
        wire_digests = [x["sha256"] for x in diagnostics
                        if x["purpose"].startswith("wireframe:")]
        distinct_wires = len(wire_digests) == len(set(wire_digests))
        has_defect = (not distinct_wires) or any((x["layout"]["horizontal_overflow_px"] > 1
                          or x["page_errors"] > 0 or x["blocked_requests"] > 0
                          or x["layout"]["body_text_characters"] == 0)
                         for x in diagnostics)
        report = {
            "schema_version": 1, "scenario_id": scenario,
            "renderer": "PLAYWRIGHT_CHROMIUM", "browser_version": browser_version,
            "gate": "NEEDS_LAYOUT_REVIEW" if has_defect else "AWAITING_HUMAN_VISUAL_REVIEW",
            "visual_assets": artifacts, "diagnostics": diagnostics,
            "distinct_sketch_files": distinct_wires,
            "visual_quality": "NOT_VERIFIED", "owner_approval": "NOT_REQUESTED",
            "limitations": "Local browser captures and DOM heuristics only; no aesthetic, WCAG, interaction or owner certification."
        }
        (stage / "comparison.html").write_text(comparison_html(artifacts), encoding="utf-8")
        (stage / "capture_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if output.exists():
            raise CaptureError("Output directory appeared during capture; refusing overwrite")
        stage.rename(output)
        return report
    except PlaywrightError as exc:
        raise CaptureError("BROWSER_RENDER_FAILED: " + str(exc).splitlines()[0]) from exc
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--chromium-executable", help="Approved local Chromium binary; no download occurs")
    args = parser.parse_args(argv)
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        print(json.dumps(capture(plan, args.source_root, args.output,
                                 executable=args.chromium_executable), ensure_ascii=False, indent=2))
    except (CaptureError, OSError, ValueError, RuntimeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
