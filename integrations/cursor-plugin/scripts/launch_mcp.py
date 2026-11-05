#!/usr/bin/env python3
"""Cursor stdio launcher for the EXISTING read-only ADT Personal MCP.

No install, network request, paid model call or project mutation is performed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


def installed_root() -> Path:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            raise ValueError("LOCALAPPDATA is missing")
        return Path(base) / "ADT-Personal"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "adt-personal"


def locate() -> tuple[Path, Path]:
    root = installed_root()
    mcp = Path(os.environ.get("ADT_PERSONAL_MCP", str(root / "mcp" / "adt_mcp.py"))).expanduser()
    source = Path(os.environ.get("ADT_TOOLKIT_SOURCE", str(root / "toolkit-source"))).expanduser()
    if not mcp.is_absolute() or not source.is_absolute():
        raise ValueError("ADT_PERSONAL_MCP and ADT_TOOLKIT_SOURCE must be absolute paths")
    if not mcp.is_file():
        raise FileNotFoundError("ADT Personal MCP not installed: " + str(mcp))
    if not (source / "MANIFEST.json").is_file():
        raise FileNotFoundError("Toolkit reference checkout unavailable: " + str(source))
    return mcp.resolve(strict=True), source.resolve(strict=True)


def main() -> int:
    try:
        mcp, source = locate()
        if len(sys.argv) > 1:
            if sys.argv[1:] == ["--doctor"]:
                print(json.dumps({
                    "status": "READY",
                    "mcp_exists": True,
                    "source_manifest_exists": True,
                    "cursor_discovery": "NOT_VERIFIED",
                    "mcp_invocation": "NOT_RUN",
                    "adapter": "EXISTING_ADT_PERSONAL_MCP",
                }, ensure_ascii=False))
                return 0
            if sys.argv[1:] == ["--check"]:
                result = subprocess.run(
                    [sys.executable, str(mcp), "--source", str(source), "--check"],
                    timeout=20, check=False,
                )
                return result.returncode
            raise ValueError("Supported arguments: --doctor or --check")
        # The MCP server owns stdout from this point onwards (JSON-RPC only).
        os.execv(sys.executable, [sys.executable, "-u", str(mcp), "--source", str(source)])
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        print("ADT_CURSOR_MCP_ERROR: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
