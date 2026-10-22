#!/usr/bin/env python3
"""Build distributable Codex MCP and ChatGPT plugin ZIPs from repository source."""
from __future__ import annotations
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

BASE = Path(__file__).resolve().parent


def archive(src: Path, dest: Path, top: str) -> dict:
    assert src.is_dir()
    paths = sorted(p for p in src.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    assert paths
    with ZipFile(dest, 'w', ZIP_DEFLATED) as z:
        for path in paths:
            rel = (Path(top) / path.relative_to(src)).as_posix()
            z.write(path, arcname=rel)
    with ZipFile(dest) as z:
        bad = z.testzip()
        assert bad is None, f'Corrupted member: {bad}'
        return {'path': str(dest), 'members': len(z.namelist())}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=BASE/'dist')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    server = BASE/'personal-mcp'/'adt-personal'
    plugin = BASE/'chatgpt-plugin'/'ai-development-toolkit'
    manifest = json.loads((plugin/'plugin.json').read_text(encoding='utf-8'))
    assert manifest['name'] == plugin.name
    results = [
        archive(server, args.output/'AI-Development-Toolkit-Personal-MCP-0.1.9.zip', 'adt-personal'),
        archive(plugin, args.output/'AI-Development-Toolkit-ChatGPT-Plugin-0.1.2.zip', plugin.name),
    ]
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
