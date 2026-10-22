#!/usr/bin/env python3
"""Build reproducible source-only MCP/ChatGPT bundles from one reviewed checkout.

This does not install, update, publish or run any bundled code. ZIP byte
identity is tested within a given runtime; compression libraries may differ
between platforms, so consumers should verify the recorded SHA256.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import stat
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

BASE = Path(__file__).resolve().parent
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
MAX_ARCHIVE_FILES = 2048
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_ARCHIVE_BYTES = 32 * 1024 * 1024


class BundleError(ValueError):
    """Refuse unsafe source inputs before writing output archives."""


def source_version(path: Path) -> str:
    """Read MCP VERSION from syntax tree without importing/executing a server."""
    try:
        parsed = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, SyntaxError) as exc:
        raise BundleError("Cannot parse MCP server version") from exc
    versions = [
        node.value.value
        for node in parsed.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "VERSION"
                for target in node.targets)
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(versions) != 1:
        raise BundleError("MCP VERSION literal missing or ambiguous")
    return checked_version(versions[0])


def checked_version(version: str) -> str:
    import re
    if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
        raise BundleError("Unsafe or missing component version")
    return version


def source_files(src: Path) -> list[tuple[str, bytes]]:
    if not src.is_dir() or src.is_symlink():
        raise BundleError("Source directory unavailable or linked")
    files = []
    size = 0
    for path in src.rglob("*"):
        relative = path.relative_to(src)
        if ({"__pycache__", ".git", ".pytest_cache", ".mypy_cache"} & set(relative.parts)
                or path.name in {".DS_Store", "Thumbs.db"}
                or path.suffix in (".pyc", ".pyo")):
            continue
        # pathlib.is_file() follows symlinks; reject symlinks before reading.
        if path.is_symlink():
            raise BundleError("Refusing linked source path: " + relative.as_posix())
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise BundleError("Refusing non-regular source: " + relative.as_posix())
        if path.stat().st_size > MAX_FILE_BYTES:
            raise BundleError("Source file exceeds size limit")
        data = path.read_bytes()
        size += len(data)
        if size > MAX_ARCHIVE_BYTES or len(files) >= MAX_ARCHIVE_FILES:
            raise BundleError("Bundle input limits exceeded")
        files.append((relative.as_posix(), data))
    if not files:
        raise BundleError("Empty bundle source")
    return sorted(files)


def archive(src: Path, dest: Path, top: str) -> dict:
    if not top or "/" in top or "\\" in top or top in (".", ".."):
        raise BundleError("Unsafe archive prefix")
    members = source_files(src)
    with ZipFile(dest, "w", compression=ZIP_DEFLATED, compresslevel=9) as output:
        for rel, data in members:
            info = ZipInfo(f"{top}/{rel}", ZIP_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            output.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)
    with ZipFile(dest, "r") as output:
        if output.testzip() is not None:
            raise BundleError("Archive CRC verification failed")
        if len(output.namelist()) != len(members):
            raise BundleError("Unexpected archive member count")
        if any(output.read(f"{top}/{rel}") != data for rel, data in members):
            raise BundleError("Archive content differs from sources")
    return {
        "path": str(dest),
        "members": len(members),
        "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(
            json.dumps([(rel, hashlib.sha256(data).hexdigest()) for rel, data in members],
                       separators=(",", ":"), ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=BASE / "dist")
    args = parser.parse_args(argv)
    server = BASE / "personal-mcp" / "adt-personal"
    plugin = BASE / "chatgpt-plugin" / "ai-development-toolkit"
    try:
        mcp_version = source_version(server / "mcp" / "adt_mcp.py")
        plugin_manifest = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
        if not isinstance(plugin_manifest, dict) or plugin_manifest.get("name") != plugin.name:
            raise BundleError("Plugin identity differs from source directory")
        plugin_version = checked_version(plugin_manifest.get("version"))
        args.output.mkdir(parents=True, exist_ok=True)
        results = [
            archive(server, args.output / f"AI-Development-Toolkit-Personal-MCP-{mcp_version}.zip",
                    "adt-personal"),
            archive(plugin, args.output / f"AI-Development-Toolkit-ChatGPT-Plugin-{plugin_version}.zip",
                    plugin.name),
        ]
    except (BundleError, OSError, ValueError, UnicodeError) as exc:
        parser.exit(2, "BLOCKED: " + str(exc) + "\n")
    print(json.dumps({
        "status": "SOURCE_ARCHIVES_BUILT_NOT_INSTALLED",
        "source": "LOCAL_CHECKOUT",
        "reproducibility": "REBUILD_AND_COMPARE_SHA256",
        "mcp_source_version": mcp_version,
        "plugin_package_version": plugin_version,
        "chatgpt_installed_plugin": "NOT_VERIFIED",
        "codex_installed_mcp": "NOT_VERIFIED",
        "results": results,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
