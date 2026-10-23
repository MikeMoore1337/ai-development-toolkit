#!/usr/bin/env python3
"""Opt-in, local Skill Manager: owned installs, drift checks, update, uninstall, rollback.

No downloads; all writes require --apply. Existing unmanaged skills are never
adopted or overwritten. Previous versions are saved locally under .adt/history.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import os
import re
import shutil
import sys
import uuid
from copy import deepcopy
from pathlib import Path

from install import ROOT, _ensure_no_symlink_chain, skill_sources

NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA = re.compile(r"^[0-9a-f]{64}$")
TX = re.compile(r"^[0-9a-f]{32}$")
VERSION = 1


class ManagerError(ValueError):
    pass


def tree_digest(root: Path) -> str:
    if not root.is_dir() or root.is_symlink() or root.is_junction():
        raise ManagerError(f"Missing, linked or invalid skill folder: {root}")
    hasher = hashlib.sha256()
    files = sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix())
    if not files:
        raise ManagerError(f"Empty skill folder: {root}")
    for file in files:
        if file.is_symlink() or file.is_junction():
            raise ManagerError(f"Linked skill content is not allowed: {file}")
        if file.is_dir():
            continue
        if not file.is_file():
            raise ManagerError(f"Unexpected skill content: {file}")
        name = file.relative_to(root).as_posix()
        hasher.update(name.encode("utf-8") + b"\0")
        hasher.update(hashlib.sha256(file.read_bytes()).digest())
    if not (root / "SKILL.md").is_file():
        raise ManagerError(f"Skill missing SKILL.md: {root}")
    return hasher.hexdigest()


def file_changes(before: Path | None, after: Path | None) -> list[dict]:
    """Non-mutating per-file diff inventory. Never print private file contents."""
    def files(root: Path | None) -> dict[str, str]:
        if root is None:
            return {}
        tree_digest(root)  # Fail closed for symlinks, junctions and invalid folders.
        return {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()
        }

    previous = files(before)
    proposed = files(after)
    output = []
    for name in sorted(previous.keys() | proposed.keys()):
        old, new = previous.get(name), proposed.get(name)
        if old != new:
            output.append({"path": name,
                           "change": ("added" if old is None else
                                      "deleted" if new is None else "modified"),
                           "before_sha256": old, "after_sha256": new})
    return output


def empty_state(layout: str) -> dict:
    return {"schema_version": VERSION, "layout": layout,
            "skills": {}, "last_transaction": None}


def validate_state(data: object) -> dict:
    if not isinstance(data, dict) or data.get("schema_version") != VERSION:
        raise ManagerError("Unknown or invalid manager lockfile schema")
    if data.get("layout") not in ("codex", "claude"):
        raise ManagerError("Invalid lockfile layout")
    skills = data.get("skills")
    if not isinstance(skills, dict):
        raise ManagerError("Invalid lockfile skills")
    for name, info in skills.items():
        if not isinstance(name, str) or not NAME.fullmatch(name):
            raise ManagerError("Invalid owned skill name")
        if not isinstance(info, dict) or not isinstance(info.get("source_version"), str):
            raise ManagerError(f"Invalid lock entry for {name}")
        if not isinstance(info.get("digest"), str) or not SHA.fullmatch(info["digest"]):
            raise ManagerError(f"Invalid digest for {name}")
    tx = data.get("last_transaction")
    if tx is not None and (not isinstance(tx, str) or not TX.fullmatch(tx)):
        raise ManagerError("Invalid last_transaction")
    return data


def state_path(target: Path, layout: str = "codex") -> Path:
    """Preserve the first client's v1 lock; isolate additional client ownership."""
    if layout not in ("codex", "claude"):
        raise ManagerError(f"Unsupported layout: {layout}")
    directory = target / ".adt"
    primary = directory / "skills-lock.json"
    _ensure_no_symlink_chain(primary)
    if primary.exists():
        try:
            original = validate_state(json.loads(primary.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            raise ManagerError(f"Unable to read lockfile: {exc}") from exc
        if original["layout"] == layout:
            return primary
        return directory / f"skills-lock-{layout}.json"
    # Do not silently create new ownership if someone removed the primary lock.
    for other in ("codex", "claude"):
        secondary = directory / f"skills-lock-{other}.json"
        if secondary.exists() or secondary.is_symlink() or secondary.is_junction():
            raise ManagerError("Primary manager lockfile missing; manual recovery needed")
    return primary


def read_state(target: Path, layout: str = "codex") -> dict:
    path = state_path(target, layout)
    _ensure_no_symlink_chain(path)
    if not path.exists():
        return empty_state(layout)
    try:
        state = validate_state(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManagerError(f"Unable to read lockfile: {exc}") from exc
    if state["layout"] != layout:
        raise ManagerError(f"Lockfile layout mismatch: requested {layout}")
    return state


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                        encoding="utf-8")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def skill_root(target: Path, layout: str) -> Path:
    return target / (".agents" if layout == "codex" else ".claude") / "skills"


@contextlib.contextmanager
def exclusive(target: Path):
    directory = target / ".adt"
    _ensure_no_symlink_chain(directory)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "manager.lock"
    if path.is_symlink():
        raise ManagerError("Linked manager lock is forbidden")
    with path.open("a+b") as lock:
        try:
            if os.name == "nt":
                import msvcrt
                lock.seek(0)
                if not lock.read(1):
                    lock.write(b"\0")
                    lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ManagerError("Another skill-manager operation is running") from exc
        try:
            yield
        finally:
            if os.name == "nt":
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock, fcntl.LOCK_UN)


def orphan_staging(target: Path) -> list[Path]:
    """Recoverable: a crash before meta.json is durable cannot have changed skills."""
    history = target / ".adt" / "history"
    if not history.exists():
        return []
    if history.is_symlink() or history.is_junction():
        raise ManagerError("Linked manager history is forbidden")
    orphans = []
    for folder in history.iterdir():
        if (folder / "meta.json").exists():
            continue
        if not folder.is_dir() or folder.is_symlink() or folder.is_junction():
            raise ManagerError(f"Unsafe transaction record: {folder}")
        if not TX.fullmatch(folder.name) or (folder / "old").exists():
            raise ManagerError(f"Unrecognized unfinished transaction: {folder}")
        for entry in folder.iterdir():
            if entry.is_symlink() or entry.is_junction():
                raise ManagerError(f"Linked unfinished transaction: {entry}")
            if entry.name == "staged" and entry.is_dir():
                continue
            if (entry.name.startswith("meta.json.") and
                    entry.name.endswith(".tmp") and entry.is_file()):
                continue
            raise ManagerError(f"Unknown unfinished transaction content: {entry}")
        orphans.append(folder)
    return orphans


def pending_transactions(target: Path) -> list[Path]:
    history = target / ".adt" / "history"
    if not history.exists():
        return []
    if history.is_symlink() or history.is_junction():
        raise ManagerError("Linked manager history is forbidden")
    pending: list[Path] = []
    for folder in history.iterdir():
        if folder.is_symlink() or folder.is_junction() or not folder.is_dir():
            raise ManagerError(f"Unsafe transaction record: {folder}")
        metadata = folder / "meta.json"
        if not metadata.is_file() or metadata.is_symlink():
            if folder in orphan_staging(target):
                continue
            raise ManagerError(f"Incomplete transaction metadata: {folder}")
        details = json.loads(metadata.read_text(encoding="utf-8"))
        if details.get("status") == "pending":
            pending.append(folder)
        elif details.get("status") not in ("committed", "recovered"):
            raise ManagerError(f"Unknown transaction status: {folder}")
    return pending


def no_pending(target: Path) -> None:
    if pending_transactions(target) or orphan_staging(target):
        raise ManagerError("Interrupted transaction detected: run recover --apply")


def verify_owned(target: Path, state: dict) -> None:
    folder = skill_root(target, state["layout"])
    _ensure_no_symlink_chain(folder)
    for name, info in state["skills"].items():
        dest = folder / name
        if tree_digest(dest) != info["digest"]:
            raise ManagerError(f"Local modifications detected in {name}; refusing mutation")


def _recover_one(target: Path, folder: Path) -> None:
    meta_path = folder / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("status") != "pending":
        return
    before = validate_state(meta["before"])
    after = validate_state(meta["after"])
    changes = meta["changes"]
    if (not isinstance(changes, list) or
            any(not isinstance(name, str) or not NAME.fullmatch(name) for name in changes)):
        raise ManagerError("Invalid recovery record")
    current = read_state(target, before["layout"])
    if current not in (before, after):
        raise ManagerError("Lockfile changed during interruption; manual recovery needed")
    root = skill_root(target, before["layout"])
    for name in reversed(changes):
        dest, old = root / name, folder / "old" / name
        _ensure_no_symlink_chain(dest)
        _ensure_no_symlink_chain(old)
        if old.exists():
            if dest.exists():
                fingerprint = tree_digest(dest)
                if (fingerprint not in {
                        x["digest"] for x in (before["skills"].get(name),
                                              after["skills"].get(name)) if x}):
                    raise ManagerError(f"Modified {name} since interruption; manual recovery needed")
                shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            os.replace(old, dest)
        elif name in before["skills"]:
            if not dest.exists() or tree_digest(dest) != before["skills"][name]["digest"]:
                raise ManagerError(f"Missing previous backup for {name}")
        elif dest.exists():
            candidate = after["skills"].get(name)
            if candidate is None or tree_digest(dest) != candidate["digest"]:
                raise ManagerError(f"Unrecognized newly-created skill {name}")
            # Without a committed ownership lock an identical folder might
            # have been created by the user between preview and mutation.
            # Prefer manual recovery to deleting unverifiable user content.
            if current != after:
                raise ManagerError(
                    f"Uncommitted new skill {name} requires manual recovery")
            shutil.rmtree(dest)
    atomic_json(state_path(target, before["layout"]), before)
    meta["status"] = "recovered"
    atomic_json(meta_path, meta)


def _apply(target: Path, before: dict, after: dict, changes: list[str],
           sources: dict[str, Path | None]) -> None:
    if not changes:
        return
    tid = uuid.uuid4().hex
    after["last_transaction"] = tid
    base = target / ".adt" / "history" / tid
    base.mkdir(parents=True)
    root = skill_root(target, before["layout"])
    try:
        for name in changes:
            source = sources[name]
            if source is not None:
                _ensure_no_symlink_chain(source)
                tree_digest(source)
                shutil.copytree(source, base / "staged" / name, symlinks=False)
                if tree_digest(base / "staged" / name) != after["skills"][name]["digest"]:
                    raise ManagerError(f"Source changed during staging: {name}")
        meta = {"status": "pending", "before": before, "after": after, "changes": changes}
        atomic_json(base / "meta.json", meta)
        for name in changes:
            dest, old = root / name, base / "old" / name
            _ensure_no_symlink_chain(dest)
            if name in before["skills"]:
                if tree_digest(dest) != before["skills"][name]["digest"]:
                    raise ManagerError(f"Local modifications during staging: {name}")
            elif dest.exists() or dest.is_symlink() or dest.is_junction():
                raise ManagerError(f"Destination occupied during staging: {dest}")
            if dest.exists():
                old.parent.mkdir(parents=True, exist_ok=True)
                os.replace(dest, old)
            if sources[name] is not None:
                dest.parent.mkdir(parents=True, exist_ok=True)
                os.replace(base / "staged" / name, dest)
        atomic_json(state_path(target, before["layout"]), after)
        meta["status"] = "committed"
        atomic_json(base / "meta.json", meta)
    except BaseException:
        if (base / "meta.json").exists():
            _recover_one(target, base)
        else:
            shutil.rmtree(base)
        raise


def operate(action: str, target: Path, *, names: list[str] | None = None,
            layout: str = "codex", apply: bool = False,
            source_root: Path = ROOT, from_layout: str | None = None) -> dict:
    target = target.expanduser().absolute()
    if not target.is_dir():
        raise ManagerError("Target must be an existing directory")
    _ensure_no_symlink_chain(target)
    _ensure_no_symlink_chain(target / ".adt")
    if action == "migrate":
        if from_layout not in ("codex", "claude") or from_layout == layout:
            raise ManagerError("migrate requires a different --from-layout")
        if names:
            raise ManagerError("migrate selects all owned source skills; omit --skills/--profile")
    elif from_layout is not None:
        raise ManagerError("--from-layout is supported only for migrate")
    if action == "recover":
        if not apply:
            return {"action": action, "pending": len(pending_transactions(target)),
                    "orphan_staging": len(orphan_staging(target)), "applied": False}
        with exclusive(target):
            pending = pending_transactions(target)
            orphans = orphan_staging(target)
            for entry in sorted(pending):
                _recover_one(target, entry)
            for entry in sorted(orphans):
                shutil.rmtree(entry)
            return {"action": action, "recovered": len(pending),
                    "discarded_incomplete_staging": len(orphans), "applied": True}
    if action == "status" and apply:
        raise ManagerError("status is always read-only; omit --apply")
    if apply:
        with exclusive(target):
            return _operate(action, target, names or [], layout, apply, source_root,
                            from_layout)
    return _operate(action, target, names or [], layout, apply, source_root,
                    from_layout)


def safe_source(name: str, sources: dict[str, Path], source_root: Path) -> Path:
    """Disallow malformed manifests from escaping the toolkit checkout."""
    relative = sources[name].relative_to(ROOT)
    if ".." in relative.parts:
        raise ManagerError(f"Source path escapes toolkit: {name}")
    source = source_root / relative
    if not source.resolve().is_relative_to(source_root.resolve()):
        raise ManagerError(f"Source path escapes toolkit: {name}")
    _ensure_no_symlink_chain(source)
    return source


def _operate(action: str, target: Path, names: list[str], layout: str,
             apply: bool, source_root: Path, from_layout: str | None) -> dict:
    no_pending(target)
    state = read_state(target, layout)
    root = skill_root(target, state["layout"])
    _ensure_no_symlink_chain(root)
    manifest = json.loads((source_root / "MANIFEST.json").read_text(encoding="utf-8"))
    sources = skill_sources(manifest)
    version = str(manifest["version"])
    if action == "status":
        report = {}
        for name, old in state["skills"].items():
            dest = root / name
            try:
                actual = tree_digest(dest)
                state_value = "clean" if actual == old["digest"] else "modified"
            except ManagerError:
                state_value = "missing_or_unsafe"
            source = sources.get(name)
            try:
                candidate = tree_digest(safe_source(name, sources, source_root)) if source else None
            except (ManagerError, ValueError):
                candidate = None
            report[name] = {"status": state_value, "source_update_available":
                            candidate is not None and candidate != old["digest"]}
        return {"action": "status", "layout": state["layout"], "skills": report,
                "skills_dir": str(root), "lockfile": str(state_path(target, layout))}
    if action not in ("install", "migrate", "update", "uninstall", "rollback"):
        raise ManagerError(f"Unsupported operation {action}")
    verify_owned(target, state)
    if action == "migrate":
        source_state = read_state(target, from_layout)
        verify_owned(target, source_state)
        names = sorted(source_state["skills"])
        if not names:
            raise ManagerError("No managed source skills to migrate")
        for name in names:
            if name not in sources:
                raise ManagerError(f"Source removed for managed skill: {name}")
            source = safe_source(name, sources, source_root)
            if tree_digest(source) != source_state["skills"][name]["digest"]:
                raise ManagerError(
                    f"Toolkit source differs from installed {name}; "
                    "refusing a non-identical migration")
    new = deepcopy(state)
    changes: list[str] = []
    staged: dict[str, Path | None] = {}
    if action in ("install", "migrate"):
        if not names:
            raise ManagerError("Install requires --profile or --skills")
        for name in names:
            if name not in sources:
                raise ManagerError(f"Unknown skill: {name}")
            dest = root / name
            if (name in state["skills"] or dest.exists() or
                    dest.is_symlink() or dest.is_junction()):
                raise ManagerError(f"Existing skill cannot be adopted or overwritten: {name}")
            source = safe_source(name, sources, source_root)
            new["skills"][name] = {"digest": tree_digest(source), "source_version": version}
            staged[name] = source
            changes.append(name)
    elif action == "update":
        for name, old in state["skills"].items():
            if name not in sources:
                raise ManagerError(f"Source removed for owned skill: {name}")
            source = safe_source(name, sources, source_root)
            digest = tree_digest(source)
            if digest != old["digest"]:
                new["skills"][name] = {"digest": digest, "source_version": version}
                staged[name] = source
                changes.append(name)
    elif action == "uninstall":
        if not names:
            raise ManagerError("Uninstall requires explicit --skills")
        for name in names:
            if name not in state["skills"]:
                raise ManagerError(f"Skill is not owned: {name}")
            del new["skills"][name]
            staged[name] = None
            changes.append(name)
    else:
        tid = state["last_transaction"]
        if not tid:
            raise ManagerError("No transaction available for rollback")
        record = target / ".adt" / "history" / tid / "meta.json"
        meta = json.loads(record.read_text(encoding="utf-8"))
        if meta.get("status") != "committed" or meta.get("after") != state:
            raise ManagerError("Rollback metadata does not match current state")
        previous = validate_state(meta["before"])
        if previous["layout"] != state["layout"]:
            raise ManagerError("Rollback layout mismatch")
        new["skills"] = deepcopy(previous["skills"])
        for name in meta["changes"]:
            if not NAME.fullmatch(name):
                raise ManagerError("Invalid rollback path")
            old = target / ".adt" / "history" / tid / "old" / name
            if name in previous["skills"]:
                if tree_digest(old) != previous["skills"][name]["digest"]:
                    raise ManagerError(f"Rollback backup damaged for {name}")
                staged[name] = old
            else:
                staged[name] = None
            changes.append(name)
    changes.sort()
    summary = {
        "action": action, "layout": layout, "changes": changes, "applied": False,
        "file_diffs": {
            name: file_changes(root / name if (root / name).exists() else None,
                               staged[name]) for name in changes
        },
    }
    if apply and changes:
        _apply(target, state, new, changes, staged)
        summary["applied"] = True
    return summary



def external_preview(target: Path, candidate_dir: Path, manifest_file: Path,
                     *, layout: str = "codex") -> dict:
    """Preview a separately supplied Skill candidate. NEVER install an external Skill.

    This deliberately shares the existing ownership and file-diff machinery
    but not the internal installer / staging / transaction path.
    """
    from external_skill_gate import review

    target = target.expanduser().absolute()
    candidate_dir = candidate_dir.expanduser().absolute()
    manifest_file = manifest_file.expanduser().absolute()
    if layout not in ("codex", "claude"):
        raise ManagerError("Unsupported layout")
    if not target.is_dir():
        raise ManagerError("Target must be an existing directory")
    _ensure_no_symlink_chain(target)
    _ensure_no_symlink_chain(target / ".adt")
    _ensure_no_symlink_chain(candidate_dir)
    _ensure_no_symlink_chain(manifest_file)
    if (candidate_dir.resolve().is_relative_to(target.resolve())
            or target.resolve().is_relative_to(candidate_dir.resolve())):
        raise ManagerError("Candidate directory must be separate from target project")
    if manifest_file.resolve().is_relative_to(candidate_dir.resolve()):
        raise ManagerError("Review manifest must be outside candidate tree")
    if manifest_file.resolve().is_relative_to(target.resolve()):
        raise ManagerError("Review manifest must be outside target project")
    no_pending(target)

    gate = review(candidate_dir, manifest_file)
    report = {
        "action": "external-preview",
        "layout": layout,
        "gate": gate,
        "applied": False,
        "installation": "NOT_AUTHORIZED",
        "external_execution": "NOT_RUN",
        "external_network": "NOT_RUN",
        "provenance_verified": False,
        "manual_owner_approval_required": True,
        "file_diffs": [],
    }
    if gate["decision"] == "REJECT":
        return {**report, "status": "REFUSED_SECURITY_GATE"}

    # The static review established schema/filename bounds and checksums.
    # These attributes are still self-declared, NOT upstream provenance.
    source = json.loads(manifest_file.read_text(encoding="utf-8"))
    name = source["candidate_id"]
    root = skill_root(target, layout)
    dest = root / name
    _ensure_no_symlink_chain(dest)
    state = read_state(target, layout)
    if dest.exists() or dest.is_symlink() or dest.is_junction():
        if name not in state["skills"]:
            return {**report, "status": "REFUSED_UNMANAGED_DESTINATION",
                    "candidate_id": name}
        # Refuse to use changed or missing owned files as a trustworthy
        # before-snapshot; never modify/recover the project here.
        if tree_digest(dest) != state["skills"][name]["digest"]:
            return {**report, "status": "REFUSED_OWNED_DRIFT",
                    "candidate_id": name}
        prior = dest
    elif name in state["skills"]:
        return {**report, "status": "REFUSED_OWNED_DRIFT",
                "candidate_id": name}
    else:
        prior = None
    changes = file_changes(prior, candidate_dir)
    return {
        **report,
        "status": ("NEEDS_MANUAL_REVIEW" if gate["decision"] == "NEEDS_MANUAL_REVIEW"
                   else "CANDIDATE_ONLY"),
        "candidate_id": name,
        "source_url": source["source_url"],
        "source_revision": source["source_revision"],
        "license": source["license"],
        "source_metadata": "OPERATOR_DECLARED_NOT_INDEPENDENTLY_VERIFIED",
        "destination_status": "OWNED_CLEAN" if prior is not None else "EMPTY",
        "file_diffs": changes,
    }

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["catalog", "install", "migrate", "status",
                                           "update", "uninstall", "rollback", "recover", "external-preview"])
    parser.add_argument("--target", type=Path)
    parser.add_argument("--layout", choices=["codex", "claude"], default="codex")
    parser.add_argument("--from-layout", choices=["codex", "claude"],
                        help="Existing managed client to copy from (migrate only)")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--profile")
    selection.add_argument("--skills", help="Comma-separated explicit skill names")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--candidate-dir", type=Path, help="External candidate files; preview only")
    parser.add_argument("--manifest", type=Path, help="Operator-supplied pinned review manifest")
    args = parser.parse_args()
    try:
        if args.action == "catalog":
            if (args.target or args.skills or args.apply or args.from_layout
                    or args.candidate_dir or args.manifest):
                raise ManagerError("catalog is read-only; use only optional --profile")
            manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
            if args.profile:
                if args.profile not in manifest["profiles"]:
                    raise ManagerError(f"Unknown profile: {args.profile}")
                result = {"action": "catalog", "profile": args.profile,
                          "skills": manifest["profiles"][args.profile]}
            else:
                result = {"action": "catalog",
                          "profiles": sorted(manifest["profiles"]),
                          "skills": sorted(skill_sources(manifest))}
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 0
        if args.action == "external-preview":
            if args.target is None or args.candidate_dir is None or args.manifest is None:
                raise ManagerError("external-preview requires --target, --candidate-dir and --manifest")
            if args.apply or args.profile or args.skills or args.from_layout:
                raise ManagerError("external-preview forbids --apply and skill/profile selection")
            result = external_preview(args.target, args.candidate_dir, args.manifest,
                                      layout=args.layout)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return 2 if result["status"].startswith("REFUSED") else 0
        if args.candidate_dir is not None or args.manifest is not None:
            raise ManagerError("External candidate parameters require external-preview")
        if args.target is None:
            raise ManagerError("--target is required except for catalog")
        chosen = []
        if args.profile:
            manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
            if args.profile not in manifest["profiles"]:
                raise ManagerError(f"Unknown profile: {args.profile}")
            chosen = manifest["profiles"][args.profile]
        elif args.skills:
            chosen = [x.strip() for x in args.skills.split(",") if x.strip()]
        if len(chosen) != len(set(chosen)):
            raise ManagerError("Duplicate skill names are forbidden")
        result = operate(args.action, args.target, names=chosen, layout=args.layout,
                         apply=args.apply, from_layout=args.from_layout)
    except (ManagerError, OSError, json.JSONDecodeError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
