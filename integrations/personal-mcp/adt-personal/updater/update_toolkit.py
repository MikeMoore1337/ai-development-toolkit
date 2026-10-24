#!/usr/bin/env python3
"""Unattended, stdlib-only updater for the dedicated read-only ADT reference checkout.

This program never updates the MCP adapter, target projects, or Codex settings.
It operates only on a dedicated Git checkout configured during personal setup.
"""
from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tarfile
import tempfile
from typing import Any

EXPECTED_ORIGIN = "https://github.com/MikeMoore1337/ai-development-toolkit.git"
MAX_ARCHIVE_BYTES = 48 * 1024 * 1024
MAX_ITEMS = 10000


class UpdateError(Exception):
    pass


def run_git(source: Path, *args: str, timeout: int = 40, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo", "GCM_INTERACTIVE": "Never"}
    try:
        result = subprocess.run(
            ["git", "-C", str(source), *args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
            env=environment, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise UpdateError(f"git_{args[0]}_unavailable_or_timeout") from exc
    if check and result.returncode:
        raise UpdateError(f"git_{args[0]}_failed")
    return result


def git_text(source: Path, *args: str) -> str:
    return run_git(source, *args).stdout.decode("utf-8", errors="replace").strip()


def check_sha(value: str) -> str:
    if not re.fullmatch(r"[a-fA-F0-9]{40}|[a-fA-F0-9]{64}", value):
        raise UpdateError("invalid_git_sha")
    return value.lower()


def check_origin(source: Path, expected_origin: str) -> None:
    if not (source / "MANIFEST.json").is_file() or not (source / ".git").exists():
        raise UpdateError("missing_dedicated_toolkit_checkout")
    # Git for Windows prints C:/... while pathlib often prints C:\\... .
    top_level = Path(git_text(source, "rev-parse", "--show-toplevel")).resolve()
    if os.path.normcase(str(top_level)) != os.path.normcase(str(source.resolve())):
        raise UpdateError("not_at_git_checkout_root")
    if git_text(source, "remote", "get-url", "origin").rstrip("/") != expected_origin.rstrip("/"):
        raise UpdateError("unexpected_git_origin")
    if git_text(source, "symbolic-ref", "--quiet", "--short", "HEAD") != "main":
        raise UpdateError("not_on_main_branch")
    if run_git(source, "status", "--porcelain", "--untracked-files=all").stdout.strip():
        raise UpdateError("local_changes_present")


def safe_name(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise UpdateError("invalid_declared_path")
    posix = PurePosixPath(value)
    if posix.is_absolute() or any(part in ("", ".", "..") for part in value.split("/")) or ":" in value:
        raise UpdateError("invalid_declared_path")
    return value


def validate_commit(source: Path, sha: str) -> dict[str, Any]:
    """Check every declared skill, role and profile BEFORE checkout mutation.

    git archive yields committed blobs, not untrusted working-tree scripts;
    validation reads bytes only and never executes repository code.
    """
    archive = run_git(source, "archive", "--format=tar", sha, timeout=60).stdout
    if len(archive) > MAX_ARCHIVE_BYTES:
        raise UpdateError("candidate_archive_too_large")
    files: dict[str, bytes] = {}
    total = 0
    try:
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:") as tf:
            for index, member in enumerate(tf):
                if index >= MAX_ITEMS:
                    raise UpdateError("candidate_has_too_many_files")
                name = safe_name(member.name.rstrip("/"))
                if member.isdir():
                    continue
                if not member.isfile() or member.issym() or member.islnk():
                    raise UpdateError("candidate_contains_link_or_special_file")
                total += member.size
                if total > MAX_ARCHIVE_BYTES:
                    raise UpdateError("candidate_files_too_large")
                if name in files:
                    raise UpdateError("duplicate_candidate_path")
                handle = tf.extractfile(member)
                if handle is None:
                    raise UpdateError("candidate_file_unreadable")
                files[name] = handle.read()
    except (tarfile.TarError, UnicodeError, OSError) as exc:
        raise UpdateError("candidate_archive_invalid") from exc
    try:
        manifest = json.loads(files["MANIFEST.json"].decode("utf-8"))
    except (KeyError, ValueError, UnicodeError) as exc:
        raise UpdateError("candidate_manifest_invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("package") != "ai-development-toolkit":
        raise UpdateError("candidate_wrong_package")
    profiles = manifest.get("profiles")
    if not isinstance(profiles, dict) or not profiles:
        raise UpdateError("candidate_profiles_invalid")
    paths: dict[str, str] = {}
    for key in ("core_skills", "extension_skills"):
        names = manifest.get(key, [])
        if not isinstance(names, list):
            raise UpdateError("candidate_skills_invalid")
        for name in names:
            safe_name(name)
            paths[name] = f".agents/skills/{name}/SKILL.md"
    # Core skills can include additional directories not enumerated in the manifest.
    for path in files:
        if re.fullmatch(r"\.agents/skills/[^/]+/SKILL\.md", path):
            name = path.split("/")[2]
            paths.setdefault(name, path)
    role_paths: set[str] = set()
    for role in manifest.get("core_roles", []):
        safe_name(role)
        role_paths.add(f".agents/roles/{role}.md")
    packs = manifest.get("extension_packs", {})
    if not isinstance(packs, dict):
        raise UpdateError("candidate_packs_invalid")
    for entry in packs.values():
        if not isinstance(entry, dict):
            raise UpdateError("candidate_pack_invalid")
        root = entry.get("skill_root")
        for name in entry.get("skills", []):
            safe_name(name)
            paths.setdefault(name, f"{safe_name(root)}/{name}/SKILL.md")
        role_root = entry.get("role_root")
        for role in entry.get("roles", []):
            safe_name(role)
            if not role_root:
                raise UpdateError("candidate_missing_role_root")
            role_paths.add(f"{safe_name(role_root)}/{role}.md")
    if not paths or not role_paths:
        raise UpdateError("candidate_empty_inventory")
    for profile, names in profiles.items():
        safe_name(profile)
        if not isinstance(names, list) or not names or any(name not in paths for name in names):
            raise UpdateError("candidate_profile_has_unknown_skill")
    for name, path in paths.items():
        if safe_name(path) not in files:
            raise UpdateError(f"candidate_missing_skill:{name}")
        try:
            data = files[path].decode("utf-8")
        except UnicodeError as exc:
            raise UpdateError(f"candidate_skill_invalid_utf8:{name}") from exc
        if not data.startswith("---\n"):
            raise UpdateError(f"candidate_skill_no_frontmatter:{name}")
        front = data.split("\n---\n", 1)
        if len(front) != 2:
            raise UpdateError(f"candidate_skill_no_frontmatter_end:{name}")
        title = re.search(r"(?m)^name:\s*['\"]?([^\n'\"]+)['\"]?\s*$", front[0])
        desc = re.search(r"(?m)^description:\s*\S", front[0])
        if not title or title.group(1).strip() != name or not desc:
            raise UpdateError(f"candidate_skill_metadata_invalid:{name}")
    for path in role_paths:
        if safe_name(path) not in files:
            raise UpdateError(f"candidate_missing_role:{path}")
        try:
            if not files[path].decode("utf-8").strip():
                raise UpdateError(f"candidate_role_empty:{path}")
        except UnicodeError as exc:
            raise UpdateError(f"candidate_role_invalid_utf8:{path}") from exc
    return {"toolkit_version": manifest.get("version"), "skills": len(paths),
            "roles": len(role_paths), "profiles": len(profiles)}


def read_state(state_file: Path) -> dict[str, Any]:
    if not state_file.exists():
        return {}
    try:
        value = json.loads(state_file.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError):
        return {}


def write_state(state_file: Path, state: dict[str, Any]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    temp = state_file.with_name(state_file.name + ".tmp")
    temp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, state_file)


def self_version(source: Path) -> str:
    try:
        manifest = json.loads((source / "MANIFEST.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise UpdateError("current_manifest_invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("package") != "ai-development-toolkit":
        raise UpdateError("current_manifest_invalid")
    value = manifest.get("version")
    return value if isinstance(value, str) and value else "NOT_VERIFIED"


def preflight(source: Path, state_dir: Path, *,
              expected_origin: str = EXPECTED_ORIGIN) -> dict[str, Any]:
    """Offline read-only status of the dedicated checkout; no fetch or writes."""
    source = source.resolve()
    check_origin(source, expected_origin)
    revision = check_sha(git_text(source, "rev-parse", "HEAD"))
    state = read_state(state_dir / "state.json")
    previous = state.get("previous_good_revision")
    eligible = False
    if isinstance(previous, str):
        try:
            previous = check_sha(previous)
            pinned = check_sha(git_text(source, "rev-parse", "refs/adt-personal/previous-good"))
            eligible = (state.get("active_revision") == revision and previous == pinned
                        and previous != revision
                        and run_git(source, "merge-base", "--is-ancestor",
                                    previous, revision, check=False).returncode == 0)
        except UpdateError:
            eligible = False
    return {
        "status": "PREFLIGHT",
        "toolkit_version": self_version(source),
        "active_revision": revision,
        "last_known_revision": state.get("last_known_revision", "NOT_VERIFIED"),
        "last_known_toolkit_version": state.get("last_known_toolkit_version", "NOT_VERIFIED"),
        "state_matches_checkout": state.get("active_revision") == revision,
        "rollback_eligible": eligible,
        "previous_good_revision": previous if eligible else None,
        "mcp_adapter_version": "NOT_VERIFIED",
        "chatgpt_plugin_version": "NOT_VERIFIED",
        "client_runtime_compatibility": "NOT_TESTED",
        "source_trust": "EXPECTED_GIT_ORIGIN_NOT_CRYPTOGRAPHIC_SIGNATURE",
        "scope": "DEDICATED_REFERENCE_CHECKOUT_ONLY",
        "network_used": False,
        "project_files_changed": False,
    }


def rollback(source: Path, state_dir: Path, *, apply: bool = False,
             expected_origin: str = EXPECTED_ORIGIN) -> dict[str, Any]:
    """Explicit safe rollback of only the clean dedicated reference checkout."""
    source = source.resolve()
    state_dir = state_dir.resolve()
    report = preflight(source, state_dir, expected_origin=expected_origin)
    if not report["rollback_eligible"]:
        raise UpdateError("rollback_unavailable_or_checkout_state_mismatch")
    target = report["previous_good_revision"]
    old = report["active_revision"]
    info = validate_commit(source, target)
    if not apply:
        return {"status": "ROLLBACK_PREVIEW", "active_revision": old,
                "previous_good_revision": target, "would_restore": info,
                "project_files_changed": False, "network_used": False}
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = state_dir / "update.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise UpdateError("another_update_is_in_progress") from exc
    os.close(fd)
    try:
        current = preflight(source, state_dir, expected_origin=expected_origin)
        if not current["rollback_eligible"] or current["active_revision"] != old:
            raise UpdateError("source_changed_before_rollback")
        run_git(source, "reset", "--hard", target)
        if (check_sha(git_text(source, "rev-parse", "HEAD")) != target or
                run_git(source, "status", "--porcelain", "--untracked-files=all").stdout.strip()):
            raise UpdateError("rollback_result_requires_manual_review")
        state_file = state_dir / "state.json"
        state = read_state(state_file)
        write_state(state_file, {**state,
                                 "active_revision": target,
                                 "previous_good_revision": None,
                                 "last_success_local_date": None,
                                 "last_attempt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                 "last_attempt_status": "ROLLED_BACK",
                                 "last_error": None})
        return {"status": "ROLLED_BACK", "previous_revision": old,
                "active_revision": target, **info,
                "project_files_changed": False, "network_used": False}
    finally:
        lock.unlink(missing_ok=True)


def update(source: Path, state_dir: Path, *, expected_origin: str = EXPECTED_ORIGIN,
           force: bool = False, today: str | None = None) -> dict[str, Any]:
    source = source.resolve()
    state_dir = state_dir.resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    lock = state_dir / "update.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        # Scheduled Task has a 5 minute deadline. Recover abandoned locks only
        # after 15 minutes; never remove a fresh lock held by another run.
        try:
            import time
            if time.time() - lock.stat().st_mtime <= 15 * 60:
                raise UpdateError("another_update_is_in_progress") from exc
            lock.unlink()
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as race:
            raise UpdateError("another_update_is_in_progress") from race
    os.close(fd)
    try:
        check_origin(source, expected_origin)
        old = check_sha(git_text(source, "rev-parse", "HEAD"))
        day = today or dt.datetime.now().astimezone().date().isoformat()
        state_file = state_dir / "state.json"
        state = read_state(state_file)
        if not force and state.get("last_success_local_date") == day and state.get("active_revision") == old:
            return {"status": "SKIPPED_ALREADY_CHECKED_TODAY", "active_revision": old,
                    "toolkit_version": state.get("last_known_toolkit_version", "NOT_VERIFIED")}
        try:
            run_git(source, "fetch", "--no-tags", "origin", "refs/heads/main", timeout=65)
            candidate = check_sha(git_text(source, "rev-parse", "FETCH_HEAD"))
            if old != candidate:
                ancestor = run_git(source, "merge-base", "--is-ancestor", old, candidate, check=False)
                if ancestor.returncode != 0:
                    raise UpdateError("non_fast_forward_remote_history")
                info = validate_commit(source, candidate)
                # Must still be the same clean source immediately before mutation.
                check_origin(source, expected_origin)
                if git_text(source, "rev-parse", "HEAD") != old:
                    raise UpdateError("source_changed_during_update")
                run_git(source, "update-ref", "refs/adt-personal/previous-good", old)
                run_git(source, "merge", "--ff-only", candidate)
                try:
                    check_origin(source, expected_origin)
                    if check_sha(git_text(source, "rev-parse", "HEAD")) != candidate:
                        raise UpdateError("post_update_revision_mismatch")
                    # Filesystem must agree with the already verified Git tree.
                    current_manifest = json.loads((source / "MANIFEST.json").read_text(encoding="utf-8"))
                    if current_manifest.get("package") != "ai-development-toolkit":
                        raise UpdateError("post_update_manifest_invalid")
                except (UpdateError, ValueError, OSError) as exc:
                    # Only rollback our own exact clean commit, never discard concurrent edits.
                    if git_text(source, "rev-parse", "HEAD") == candidate and not run_git(
                        source, "status", "--porcelain", "--untracked-files=all").stdout.strip():
                        run_git(source, "reset", "--hard", old)
                        raise UpdateError("post_update_validation_failed_rolled_back") from exc
                    raise UpdateError("post_update_validation_failed_manual_review_required") from exc
                result = {"status": "UPDATED", "previous_revision": old,
                          "active_revision": candidate, **info}
            else:
                result = {"status": "UP_TO_DATE", "active_revision": old,
                          "toolkit_version": self_version(source)}
        except UpdateError as exc:
            write_state(state_file, {**state, "last_attempt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                     "last_attempt_status": "FAIL", "last_error": str(exc)})
            raise
        write_state(state_file, {**state, "last_attempt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                 "last_attempt_status": result["status"], "last_success_local_date": day,
                                 "active_revision": result["active_revision"],
                                 "last_known_revision": candidate,
                                 "last_known_toolkit_version": result["toolkit_version"],
                                 "previous_good_revision": result.get("previous_revision", state.get("previous_good_revision")),
                                 "last_error": None})
        return result
    except UpdateError as exc:
        # Task Scheduler does not retain stdout by default; persist every failure,
        # including dirty worktrees and invalid/mismatched origins.
        state_file = state_dir / "state.json"
        state = read_state(state_file)
        write_state(state_file, {**state,
                                 "last_attempt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                 "last_attempt_status": "FAIL", "last_error": str(exc)})
        raise
    finally:
        lock.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    local = (Path(os.environ.get("LOCALAPPDATA", str(Path.home() / "AppData" / "Local"))) / "ADT-Personal"
             if os.name == "nt" else Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "adt-personal")
    parser.add_argument("--source", type=Path, default=local / "toolkit-source")
    parser.add_argument("--state-dir", type=Path, default=local / "updater" / "state")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--status", action="store_true", help="Read saved state without network access")
    selection.add_argument("--preflight", action="store_true",
                           help="Inspect versions without network or changes")
    selection.add_argument("--rollback", action="store_true",
                           help="Preview clean-checkout rollback; requires --apply to mutate")
    parser.add_argument("--apply", action="store_true", help="Explicitly apply only --rollback")
    parser.add_argument("--force", action="store_true", help="Ignore once-per-day throttle; never force Git history")
    args = parser.parse_args(argv)
    if args.apply and not args.rollback:
        parser.error("--apply requires --rollback")
    if args.force and (args.rollback or args.preflight or args.status):
        parser.error("--force is only for source refresh")
    if args.status:
        print(json.dumps({"status": "STATE", **read_state(args.state_dir / "state.json")}, ensure_ascii=False))
        return 0
    try:
        if args.preflight:
            result = preflight(args.source, args.state_dir)
        elif args.rollback:
            result = rollback(args.source, args.state_dir, apply=args.apply)
        else:
            result = update(args.source, args.state_dir, force=args.force)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except UpdateError as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
