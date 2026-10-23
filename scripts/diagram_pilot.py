#!/usr/bin/env python3
"""Issue #265: deterministic, offline, evidence-linked static architecture diagrams.

This is original Toolkit code, NOT a copy of the Diagram Design upstream skill.
It only renders small left-to-right DAG-like diagrams from explicit JSON.
"""
from __future__ import annotations

import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
import sys

NODE_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,31}\Z")
HEX = re.compile(r"#[0-9a-fA-F]{6}\Z")
MAX_NODES = 16
MAX_EDGES = 28


def _required_string(obj: dict, key: str, limit: int = 120) -> str:
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(f"{key}: required nonempty string, max {limit} characters")
    if any(ord(ch) < 32 for ch in value):
        raise ValueError(f"{key}: control characters are not permitted")
    return value.strip()


def validate(spec: object) -> dict:
    if not isinstance(spec, dict) or type(spec.get("version")) is not int or spec["version"] != 1:
        raise ValueError("version: expected integer 1")
    _required_string(spec, "title", 100)
    accent = spec.get("accent", "#2563eb")
    if not isinstance(accent, str) or not HEX.fullmatch(accent):
        raise ValueError("accent: expected six-digit hex color")
    nodes, edges = spec.get("nodes"), spec.get("edges")
    if not isinstance(nodes, list) or not 1 <= len(nodes) <= MAX_NODES:
        raise ValueError(f"nodes: expected 1..{MAX_NODES} entries")
    if not isinstance(edges, list) or len(edges) > MAX_EDGES:
        raise ValueError(f"edges: expected 0..{MAX_EDGES} entries")
    seen: dict[str, int] = {}
    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            raise ValueError(f"nodes[{i}]: expected object")
        identifier = _required_string(node, "id", 32)
        if not NODE_ID.fullmatch(identifier) or identifier in seen:
            raise ValueError(f"nodes[{i}]: invalid or duplicate id")
        _required_string(node, "label", 64)
        _required_string(node, "evidence", 250)
        column = node.get("column")
        if type(column) is not int or not 0 <= column <= 3:
            raise ValueError(f"nodes[{i}]: column must be integer 0..3")
        seen[identifier] = column
    pairs: set[tuple[str, str, str]] = set()
    for i, edge in enumerate(edges):
        if not isinstance(edge, dict):
            raise ValueError(f"edges[{i}]: expected object")
        source = _required_string(edge, "from", 32)
        target = _required_string(edge, "to", 32)
        label = _required_string(edge, "label", 50)
        _required_string(edge, "evidence", 250)
        if source not in seen or target not in seen:
            raise ValueError(f"edges[{i}]: both endpoints must exist")
        if seen[source] >= seen[target]:
            raise ValueError(f"edges[{i}]: pilot requires left-to-right forward edges")
        key = (source, target, label)
        if key in pairs:
            raise ValueError(f"edges[{i}]: duplicate edge")
        pairs.add(key)
    return spec


def render(spec: dict) -> str:
    validate(spec)
    nodes, edges = spec["nodes"], spec["edges"]
    counts = Counter(n["column"] for n in nodes)
    columns = max(counts) + 1
    width = max(360, 90 + columns * 245)
    height = max(230, 142 + max(counts.values()) * 112)
    positions: dict[str, tuple[int, int]] = {}
    per_column: Counter = Counter()
    for node in nodes:
        col = node["column"]
        positions[node["id"]] = (50 + col * 245, 65 + per_column[col] * 112)
        per_column[col] += 1

    shapes: list[str] = []
    for edge in edges:
        x1, y1 = positions[edge["from"]]
        x2, y2 = positions[edge["to"]]
        a, b, c, d = x1 + 180, y1 + 37, x2 - 8, y2 + 37
        delta = max(25, (c - a) // 3)
        path = f"M {a} {b} C {a + delta} {b}, {c - delta} {d}, {c} {d}"
        shapes.append(f'<path d="{path}" fill="none" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>')
    for node in nodes:
        x, y = positions[node["id"]]
        label = escape(node["label"], quote=True)
        shapes.append(f'<g><rect x="{x}" y="{y}" width="180" height="74" rx="8" fill="#f8fafc" stroke="#334155" stroke-width="1.5"/>'
                      f'<text x="{x + 90}" y="{y + 44}" text-anchor="middle" fill="#0f172a" font-size="14">{label}</text></g>')
    references = []
    for n in nodes:
        references.append(f'<li>Узел <code>{escape(n["id"], quote=True)}</code>: {escape(n["evidence"], quote=True)}</li>')
    for e in edges:
        references.append(f'<li>Связь <code>{escape(e["from"], quote=True)} → {escape(e["to"], quote=True)}</code>: '
                          f'{escape(e["label"], quote=True)} - {escape(e["evidence"], quote=True)}</li>')
    title = escape(spec["title"], quote=True)
    accent = spec.get("accent", "#2563eb")
    description = "Узлов: " + str(len(nodes)) + "; связей: " + str(len(edges)) + ". Направление слева направо."
    svg_body = "\n".join(shapes)
    refs = "\n".join(references)
    return f'''<!doctype html>
<html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{title}</title><style>
:root {{color-scheme:light;--accent:{accent}}}
body {{font-family:system-ui,sans-serif;color:#0f172a;background:#fff;margin:2rem;line-height:1.5}}
main {{max-width:1100px;margin:auto}} h1 {{border-left:4px solid var(--accent);padding-left:1rem}}
svg {{display:block;width:100%;height:auto;border:1px solid #cbd5e1;border-radius:8px}}
details {{margin-top:1.5rem}} code {{overflow-wrap:anywhere}}
</style></head><body><main><h1>{title}</h1>
<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="svgtitle svgdesc" viewBox="0 0 {width} {height}">
<title id="svgtitle">{title}</title><desc id="svgdesc">{description}</desc>
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto">
<path d="M0,0 L6,3 L0,6 Z" fill="#64748b"/></marker></defs>
{svg_body}</svg>
<details><summary>Происхождение элементов схемы</summary><ul>{refs}</ul></details>
<p>Синтетический или предоставленный пользователем вход. Точность источников и визуальное качество не подтверждаются генератором.</p>
</main></body></html>
'''


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render an evidence-linked offline HTML/SVG diagram.")
    parser.add_argument("input", type=Path, help="JSON specification")
    parser.add_argument("--output", required=True, type=Path, help="New HTML file (never overwritten)")
    args = parser.parse_args(argv)
    try:
        spec = json.loads(args.input.read_text(encoding="utf-8"))
        html = render(spec)
        with args.output.open("x", encoding="utf-8") as out:
            out.write(html)
    except (OSError, ValueError, TypeError) as exc:
        print(f"DIAGRAM_PILOT_ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"DIAGRAM_PILOT_CREATED: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
