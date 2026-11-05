#!/usr/bin/env python3
"""Opt-in, reversible local Cursor plugin installer (standard library only)."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

PLUGIN = Path(__file__).resolve().parents[1]
PAYLOAD = ("mcp.json", ".cursor-plugin", "skills", "rules", "commands", "README.md",
           "README.ru.md", "scripts/launch_mcp.py")
MARKER = ".adt-managed.json"
REUSE_GLOBAL = "reuse-global"
BUNDLED_MCP = "bundled"


def has_global_adt_mcp() -> bool:
    """Recognize the already registered ADT stdio server, without altering it."""
    config = Path.home() / ".cursor" / "mcp.json"
    if not config.is_file():
        return False
    reject_links(config)
    try:
        obj = json.loads(config.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    if not isinstance(obj, dict) or not isinstance(obj.get("mcpServers"), dict):
        return False
    item = obj["mcpServers"].get("ai-development-toolkit")
    if not isinstance(item, dict) or item.get("type", "stdio") != "stdio":
        return False
    cmd = str(item.get("command", ""))
    arguments = item.get("args", [])
    if not isinstance(arguments, list) or not all(isinstance(arg, str) for arg in arguments):
        return False
    if Path(cmd).name.lower() not in {"python", "python.exe", "py", "py.exe"}:
        return False
    return "--source" in arguments and any(
        Path(arg).name.lower() == "adt_mcp.py" for arg in arguments
    )


def default_target() -> Path:
    return Path.home() / ".cursor" / "plugins" / "local" / "ai-development-toolkit"


def default_state() -> Path:
    if os.name == "nt":
        return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ADT-Cursor"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "adt-cursor"


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def reject_links(path: Path) -> None:
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError("Symlink/junction path rejected: " + str(part))


def source_files(source: Path) -> dict[str, Path]:
    found = {}
    for item in PAYLOAD:
        node = source / item
        if not node.exists():
            raise FileNotFoundError(str(node))
        paths = sorted(node.rglob("*")) if node.is_dir() else [node]
        for p in paths:
            if p.is_dir():
                continue
            reject_links(p)
            if not p.is_file():
                raise ValueError("Not a regular file: " + str(p))
            found[p.relative_to(source).as_posix()] = p
    return found


def payload_bytes(source: Path, reuse_global_mcp: bool) -> dict[str, bytes]:
    payload = {name: path.read_bytes() for name, path in source_files(source).items()}
    if reuse_global_mcp:
        payload.pop("mcp.json")
        manifest = json.loads(payload[".cursor-plugin/plugin.json"].decode("utf-8"))
        manifest.pop("mcpServers", None)
        # Cursor's default MCP discovery requires mcp.json, intentionally omitted here.
        payload[".cursor-plugin/plugin.json"] = (
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
        ).encode("utf-8")
    return payload


def inspection(target: Path) -> tuple[str, dict]:
    if not target.exists() and not target.is_symlink():
        return "NOT_INSTALLED", {}
    reject_links(target)
    marker = target / MARKER
    if not marker.is_file():
        return "UNMANAGED_CONFLICT", {}
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        files = data["files"]
        if data.get("schema") != 1 or not isinstance(files, dict):
            return "INVALID_MARKER", {}
        if any(not isinstance(k, str) or not isinstance(v, str) or
               Path(k).is_absolute() or ".." in Path(k).parts for k, v in files.items()):
            return "INVALID_MARKER", {}
        actual = {p.relative_to(target).as_posix(): digest(p)
                  for p in target.rglob("*") if p.is_file() and p != marker}
        if actual != files or any(p.is_symlink() for p in target.rglob("*")):
            return "DRIFT", data
    except (OSError, ValueError, KeyError, TypeError):
        return "INVALID_MARKER", {}
    return "MANAGED_CLEAN", data


def write_json(path: Path, obj: dict) -> None:
    temp = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        temp.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)
    finally:
        if temp.exists():
            temp.unlink()


def perform_install(source: Path, target: Path, state_dir: Path, *, reuse_global_mcp: bool = False) -> dict:
    reject_links(target)
    reject_links(state_dir)
    state, _ = inspection(target)
    if state not in ("NOT_INSTALLED", "MANAGED_CLEAN"):
        raise ValueError("Refusing to overwrite " + state)
    if reuse_global_mcp and not has_global_adt_mcp():
        raise ValueError("No compatible global ADT MCP found in ~/.cursor/mcp.json")
    files = payload_bytes(source, reuse_global_mcp)
    planned = {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}
    mode = REUSE_GLOBAL if reuse_global_mcp else BUNDLED_MCP
    if state == "MANAGED_CLEAN":
        marker = json.loads((target / MARKER).read_text(encoding="utf-8"))
        if marker["files"] == planned and marker.get("mcp_mode", BUNDLED_MCP) == mode:
            return {"status": "ALREADY_CURRENT", "files": len(files), "mcp_mode": mode}
    target.parent.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    staging = target.parent / (".adt-cursor-stage-" + uuid.uuid4().hex)
    backup = None
    try:
        staging.mkdir()
        for rel, data in files.items():
            destination = staging / Path(rel)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        version = json.loads((source / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"]
        write_json(staging / MARKER, {"schema": 1, "version": version, "files": planned,
                                      "mcp_mode": mode})
        if target.exists():
            backup_dir = state_dir / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup = backup_dir / ("cursor-" + uuid.uuid4().hex)
            target.rename(backup)
        try:
            staging.rename(target)
            write_json(state_dir / "state.json", {"schema": 1, "backup": str(backup) if backup else None})
        except Exception:
            if target.exists():
                shutil.rmtree(target)
            if backup is not None:
                backup.rename(target)
            raise
        return {"status": "UPDATED" if backup else "INSTALLED", "version": version,
                "files": len(files), "mcp_mode": mode, "rollback_available": True}
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def perform_rollback(target: Path, state_dir: Path) -> dict:
    state, _ = inspection(target)
    if state != "MANAGED_CLEAN":
        raise ValueError("Rollback refused: " + state)
    meta = state_dir / "state.json"
    if not meta.is_file():
        raise ValueError("State record missing")
    data = json.loads(meta.read_text(encoding="utf-8"))
    backup = Path(data["backup"]) if data.get("backup") else None
    if backup is not None:
        backups_dir = (state_dir / "backups").resolve()
        if not backup.resolve().is_relative_to(backups_dir) or inspection(backup)[0] != "MANAGED_CLEAN":
            raise ValueError("Rollback backup invalid or outside managed directory")
    temporary = target.parent / (".adt-cursor-reverting-" + uuid.uuid4().hex)
    target.rename(temporary)
    try:
        if backup is not None:
            backup.rename(target)
        write_json(meta, {"schema": 1, "backup": None})
    except Exception:
        if target.exists():
            target.rename(backup)
        temporary.rename(target)
        raise
    shutil.rmtree(temporary)
    return {"status": "RESTORED_PREVIOUS" if backup else "UNINSTALLED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["install", "update", "status", "doctor", "rollback"])
    parser.add_argument("--apply", action="store_true", help="Explicitly approve filesystem changes")
    parser.add_argument("--reuse-global-mcp", action="store_true",
                        help="Use the already configured Cursor ADT MCP without registering a duplicate")
    parser.add_argument("--source", type=Path, default=PLUGIN)
    parser.add_argument("--target", type=Path, default=default_target())
    parser.add_argument("--state-dir", type=Path, default=default_state())
    args = parser.parse_args()
    try:
        source, target, state_dir = args.source.resolve(), args.target.absolute(), args.state_dir.absolute()
        if target.name != "ai-development-toolkit":
            raise ValueError("Target basename must be ai-development-toolkit")
        reject_links(target)
        status, info = inspection(target)
        if args.action in ("install", "update"):
            if status not in ("NOT_INSTALLED", "MANAGED_CLEAN"):
                raise ValueError("Refusing to overwrite " + status)
            reuse = (args.reuse_global_mcp or
                     (status == "MANAGED_CLEAN" and info.get("mcp_mode") == REUSE_GLOBAL))
            detected_global = has_global_adt_mcp()
            if reuse and not detected_global:
                raise ValueError("Requested --reuse-global-mcp but no compatible ADT MCP is registered")
            if not reuse and detected_global and target == default_target().absolute():
                raise ValueError("ADT MCP already registered in Cursor; rerun with --reuse-global-mcp")
            desired = payload_bytes(source, reuse)
            result = {"status": "PREVIEW", "target_status": status, "target": str(target),
                      "version": json.loads((source / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))["version"],
                      "payload_files": len(desired), "mcp_mode": REUSE_GLOBAL if reuse else BUNDLED_MCP,
                      "applied": False}
            if args.apply:
                result = perform_install(source, target, state_dir, reuse_global_mcp=reuse)
                result["applied"] = True
        elif args.action == "rollback":
            result = {"status": "ROLLBACK_PREVIEW", "target_status": status, "applied": False}
            if args.apply:
                result = perform_rollback(target, state_dir)
                result["applied"] = True
        else:
            result = {"status": status, "version": info.get("version"),
                      "mcp_mode": info.get("mcp_mode"), "applied": False}
            if args.action == "doctor":
                if info.get("mcp_mode") == REUSE_GLOBAL:
                    result["global_adt_mcp_registered"] = has_global_adt_mcp()
                if status == "MANAGED_CLEAN":
                    proc = subprocess.run([sys.executable, str(target / "scripts" / "launch_mcp.py"), "--doctor"],
                                          capture_output=True, text=True, timeout=20, check=False)
                    result["mcp"] = json.loads(proc.stdout) if proc.returncode == 0 else {
                        "status": "BLOCKED", "reason": proc.stderr.strip()[:350]}
                else:
                    result["mcp"] = {"status": "NOT_CHECKED"}
                result["cursor_skill_discovery"] = "NOT_VERIFIED"
                result["cursor_mcp_invocation"] = "NOT_VERIFIED"
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
