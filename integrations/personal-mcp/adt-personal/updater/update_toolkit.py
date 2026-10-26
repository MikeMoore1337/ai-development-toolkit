#!/usr/bin/env python3
"""Unattended, stdlib-only updater for the dedicated read-only ADT reference checkout.

This program never updates the MCP adapter, target projects, or Codex settings.
It operates only on a dedicated Git checkout configured during personal setup.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import tarfile
import tempfile
from typing import Any

EXPECTED_ORIGIN = "https://github.com/MikeMoore1337/ai-development-toolkit.git"
MAX_ARCHIVE_BYTES = 48 * 1024 * 1024
MAX_ITEMS = 10000
CANDIDATE_REF = "refs/adt-personal/remote-main"


class UpdateError(Exception):
    pass


def run_git(source: Path, *args: str, timeout: int = 40, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    environment = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_ASKPASS": "echo",
                   "GCM_INTERACTIVE": "Never", "GIT_OPTIONAL_LOCKS": "0"}
    try:
        result = subprocess.run(
            ["git", "-C", str(source), "-c", f"core.hooksPath={os.devnull}", *args],
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


def _is_reparse_point(path: Path) -> bool:
    try:
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode):
            return True
        attributes = getattr(info, "st_file_attributes", 0)
        if attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400):
            return True
        is_junction = getattr(path, "is_junction", None)
        return bool(is_junction and is_junction())
    except FileNotFoundError:
        return False
    except NotADirectoryError:
        return False
    except OSError as exc:
        raise UpdateError("unsafe_linked_path") from exc


def _ensure_no_reparse_chain(path: Path) -> None:
    """Reject symlinks and Windows junctions before any path is followed."""
    for component in (path, *path.parents):
        if _is_reparse_point(component):
            raise UpdateError("linked_path_not_allowed")


def _canonical_path(path: Path, *, label: str, strict: bool) -> Path:
    # shortcut: path-based Git APIs cannot close a hostile same-user swap; use an fd-based sandbox if that threat is in scope.
    value = Path(path).expanduser()
    _ensure_no_reparse_chain(value)
    try:
        resolved = value.resolve(strict=strict)
    except (OSError, RuntimeError) as exc:
        raise UpdateError(f"{label}_path_invalid") from exc
    _ensure_no_reparse_chain(resolved)
    return resolved


def _ensure_checkout_has_no_links(source: Path) -> None:
    _ensure_no_reparse_chain(source)
    for relative in (".git", "MANIFEST.json"):
        _ensure_no_reparse_chain(source / relative)
    entries = run_git(source, "ls-files", "-s", "-z").stdout
    for entry in entries.split(b"\0"):
        if not entry:
            continue
        try:
            mode, rest = entry.split(b" ", 1)
        except ValueError as exc:
            raise UpdateError("checkout_file_list_invalid") from exc
        if mode == b"120000":
            raise UpdateError("checkout_contains_symlink")
        try:
            relative = rest.split(b"\t", 1)[1].decode("utf-8")
        except (IndexError, UnicodeError) as exc:
            raise UpdateError("checkout_file_list_invalid") from exc
        _ensure_no_reparse_chain(source / relative)


def _ensure_no_origin_url_rewrite(source: Path, expected_origin: str) -> None:
    result = run_git(source, "config", "--show-origin", "--get-regexp",
                     r"^url\..*\.insteadof$", check=False)
    if result.returncode not in (0, 1):
        raise UpdateError("git_config_failed")
    expected = expected_origin.rstrip("/")
    for line in result.stdout.decode("utf-8", errors="replace").splitlines():
        fields = line.split(None, 2)
        if len(fields) != 3:
            raise UpdateError("git_config_invalid")
        prefix = fields[2].rstrip("/")
        if prefix and expected.startswith(prefix):
            raise UpdateError("unexpected_git_url_rewrite")


def check_origin(source: Path, expected_origin: str, *, require_clean: bool = True) -> None:
    _ensure_checkout_has_no_links(source)
    if (not (source / "MANIFEST.json").is_file()
            or not (source / ".git").is_dir()):
        raise UpdateError("missing_dedicated_toolkit_checkout")
    # Git for Windows prints C:/... while pathlib often prints C:\\... .
    top_level = Path(git_text(source, "rev-parse", "--show-toplevel")).resolve()
    if os.path.normcase(str(top_level)) != os.path.normcase(str(source.resolve())):
        raise UpdateError("not_at_git_checkout_root")
    _ensure_no_origin_url_rewrite(source, expected_origin)
    remote_urls = run_git(source, "remote", "get-url", "--all", "origin").stdout.decode(
        "utf-8", errors="replace").splitlines()
    if (len(remote_urls) != 1 or
            remote_urls[0].rstrip("/") != expected_origin.rstrip("/")):
        raise UpdateError("unexpected_git_origin")
    if git_text(source, "symbolic-ref", "--quiet", "--short", "HEAD") != "main":
        raise UpdateError("not_on_main_branch")
    if require_clean and run_git(source, "status", "--porcelain", "--untracked-files=all").stdout.strip():
        raise UpdateError("local_changes_present")


def version_tuple(value: object) -> tuple[int, int, int]:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value):
        raise UpdateError("unsupported_toolkit_version_format")
    return tuple(int(part) for part in value.split("."))


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
    version_tuple(manifest.get("version"))
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
    core_roles = manifest.get("core_roles", [])
    if not isinstance(core_roles, list):
        raise UpdateError("candidate_roles_invalid")
    role_paths: set[str] = set()
    for role in core_roles:
        safe_name(role)
        role_paths.add(f".agents/roles/{role}.md")
    packs = manifest.get("extension_packs", {})
    if not isinstance(packs, dict):
        raise UpdateError("candidate_packs_invalid")
    for entry in packs.values():
        if not isinstance(entry, dict):
            raise UpdateError("candidate_pack_invalid")
        root = entry.get("skill_root")
        skills = entry.get("skills", [])
        roles = entry.get("roles", [])
        if not isinstance(skills, list) or not isinstance(roles, list):
            raise UpdateError("candidate_pack_invalid")
        for name in skills:
            safe_name(name)
            paths.setdefault(name, f"{safe_name(root)}/{name}/SKILL.md")
        role_root = entry.get("role_root")
        for role in roles:
            safe_name(role)
            if not role_root:
                raise UpdateError("candidate_missing_role_root")
            role_paths.add(f"{safe_name(role_root)}/{role}.md")
    if not paths or not role_paths:
        raise UpdateError("candidate_empty_inventory")
    for profile, names in profiles.items():
        safe_name(profile)
        if (not isinstance(names, list) or not names or
                any(not isinstance(name, str) or name not in paths for name in names)):
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
    _ensure_no_reparse_chain(state_file)
    if not state_file.exists():
        return {}
    try:
        value = json.loads(state_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise UpdateError("state_invalid") from exc
    if not isinstance(value, dict):
        raise UpdateError("state_invalid")
    revision_fields = ("active_revision", "previous_good_revision", "last_known_revision")
    for field in revision_fields:
        item = value.get(field)
        if item is None or (field == "last_known_revision" and item == "NOT_VERIFIED"):
            continue
        try:
            check_sha(item)
        except (TypeError, UpdateError) as exc:
            raise UpdateError("state_invalid") from exc
    for field in ("last_known_toolkit_version", "last_success_local_date",
                  "last_attempt_utc", "last_attempt_status"):
        if field in value and value[field] is not None and not isinstance(value[field], str):
            raise UpdateError("state_invalid")
    if value.get("last_error") is not None and not isinstance(value["last_error"], str):
        raise UpdateError("state_invalid")
    pending_update = value.get("pending_update")
    pending_rollback = value.get("pending_rollback")
    if pending_update is not None and pending_rollback is not None:
        raise UpdateError("state_invalid")
    for pending in (pending_update, pending_rollback):
        if pending is None:
            continue
        if not isinstance(pending, dict):
            raise UpdateError("state_invalid")
        for field in ("from_revision", "to_revision"):
            try:
                check_sha(pending[field])
            except (KeyError, TypeError, UpdateError) as exc:
                raise UpdateError("state_invalid") from exc
        for field in ("from_toolkit_version", "to_toolkit_version", "started_utc"):
            if not isinstance(pending.get(field), str):
                raise UpdateError("state_invalid")
        try:
            version_tuple(pending["from_toolkit_version"])
            version_tuple(pending["to_toolkit_version"])
        except UpdateError as exc:
            raise UpdateError("state_invalid") from exc
    return value


def write_state(state_file: Path, state: dict[str, Any]) -> None:
    _ensure_no_reparse_chain(state_file)
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
        _ensure_no_reparse_chain(state_file)
        payload = (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        fd, temporary = tempfile.mkstemp(prefix=f".{state_file.name}.", suffix=".tmp",
                                         dir=str(state_file.parent))
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            _ensure_no_reparse_chain(state_file)
            os.replace(temporary_path, state_file)
            # shortcut: Windows has no portable directory fsync here; power-loss durability remains OS-dependent.
            if os.name != "nt":
                try:
                    directory_fd = os.open(state_file.parent, os.O_RDONLY)
                except OSError:
                    directory_fd = None
                if directory_fd is not None:
                    try:
                        os.fsync(directory_fd)
                    finally:
                        os.close(directory_fd)
        finally:
            temporary_path.unlink(missing_ok=True)
    except UpdateError:
        raise
    except (OSError, TypeError, ValueError, UnicodeError) as exc:
        raise UpdateError("state_write_failed") from exc


@contextlib.contextmanager
def exclusive_lock(state_dir: Path):
    """Hold an OS lock for the whole mutation; never reclaim by timestamp."""
    _ensure_no_reparse_chain(state_dir)
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        _ensure_no_reparse_chain(state_dir)
        lock_path = state_dir / "update.lock"
        _ensure_no_reparse_chain(lock_path)
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        fd = os.open(lock_path, flags, 0o600)
    except (OSError, UpdateError) as exc:
        if isinstance(exc, UpdateError):
            raise
        raise UpdateError("update_lock_unavailable") from exc
    lock = os.fdopen(fd, "a+b")
    acquired = False
    try:
        try:
            if os.name == "nt":
                import msvcrt
                lock.seek(0)
                if not lock.read(1):
                    lock.seek(0, os.SEEK_END)
                    lock.write(b"\0")
                    lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            acquired = True
        except OSError as exc:
            raise UpdateError("another_update_is_in_progress") from exc
        yield
    finally:
        if acquired:
            try:
                if os.name == "nt":
                    import msvcrt
                    lock.seek(0)
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            finally:
                lock.close()
        else:
            lock.close()


def self_version(source: Path) -> str:
    try:
        manifest = json.loads((source / "MANIFEST.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        raise UpdateError("current_manifest_invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("package") != "ai-development-toolkit":
        raise UpdateError("current_manifest_invalid")
    value = manifest.get("version")
    version_tuple(value)
    return value


def preflight(source: Path, state_dir: Path, *,
              expected_origin: str = EXPECTED_ORIGIN) -> dict[str, Any]:
    """Offline read-only status of the dedicated checkout; no fetch or writes."""
    source = _canonical_path(source, label="source", strict=True)
    state_dir = _canonical_path(state_dir, label="state", strict=False)
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


def _drop_candidate_ref(source: Path) -> None:
    try:
        run_git(source, "update-ref", "-d", CANDIDATE_REF, check=False)
    except UpdateError:
        # A leftover private candidate ref is harmless and is replaced on the
        # next fetch; cleanup must not turn a successful update into a failure.
        pass


def _recover_pending_update(source: Path, state_file: Path, state: dict[str, Any],
                            *, today: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    pending = state.get("pending_update")
    if pending is None:
        return state, None
    from_revision = check_sha(pending["from_revision"])
    to_revision = check_sha(pending["to_revision"])
    if state.get("active_revision") not in (None, from_revision):
        raise UpdateError("interrupted_update_state_mismatch")
    candidate_ref = check_sha(git_text(source, "rev-parse", CANDIDATE_REF))
    if candidate_ref != to_revision:
        raise UpdateError("interrupted_update_state_mismatch")
    if run_git(source, "status", "--porcelain", "--untracked-files=all").stdout.strip():
        raise UpdateError("interrupted_update_requires_manual_review")
    current = check_sha(git_text(source, "rev-parse", "HEAD"))
    if current == from_revision:
        cleared = {**state, "pending_update": None,
                   "last_attempt_status": "RECOVERED_NO_CHANGE",
                   "last_error": "interrupted_update_before_checkout"}
        write_state(state_file, cleared)
        return cleared, None
    if current != to_revision:
        raise UpdateError("interrupted_update_requires_manual_review")
    pinned = check_sha(git_text(source, "rev-parse", "refs/adt-personal/previous-good"))
    if (pinned != from_revision or
            run_git(source, "merge-base", "--is-ancestor", from_revision,
                    to_revision, check=False).returncode != 0):
        raise UpdateError("interrupted_update_requires_manual_review")
    info = validate_commit(source, to_revision)
    if version_tuple(info["toolkit_version"]) < version_tuple(pending["from_toolkit_version"]):
        raise UpdateError("candidate_toolkit_version_downgrade")
    recovered = {**state, "pending_update": None,
                 "last_attempt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                 "last_attempt_status": "RECOVERED_AFTER_INTERRUPTION",
                 "last_success_local_date": today,
                 "active_revision": to_revision,
                 "last_known_revision": to_revision,
                 "last_known_toolkit_version": info["toolkit_version"],
                 "previous_good_revision": from_revision,
                 "last_error": None}
    write_state(state_file, recovered)
    _drop_candidate_ref(source)
    return recovered, {"status": "RECOVERED_AFTER_INTERRUPTION",
                       "previous_revision": from_revision,
                       "active_revision": to_revision, **info}


def _recover_pending_rollback(source: Path, state_file: Path, state: dict[str, Any],
                              *, today: str) -> tuple[dict[str, Any], dict[str, Any] | None]:
    pending = state.get("pending_rollback")
    if pending is None:
        return state, None
    from_revision = check_sha(pending["from_revision"])
    to_revision = check_sha(pending["to_revision"])
    if from_revision == to_revision or state.get("active_revision") not in (None, from_revision):
        raise UpdateError("interrupted_rollback_state_mismatch")
    current = check_sha(git_text(source, "rev-parse", "HEAD"))
    if current == from_revision:
        cleared = {**state, "pending_rollback": None,
                   "last_success_local_date": None,
                   "last_attempt_status": "RECOVERED_ROLLBACK_NO_CHANGE",
                   "last_error": "interrupted_rollback_before_checkout"}
        write_state(state_file, cleared)
        return cleared, None
    if current != to_revision or run_git(
            source, "status", "--porcelain", "--untracked-files=all").stdout.strip():
        raise UpdateError("interrupted_rollback_requires_manual_review")
    pinned = check_sha(git_text(source, "rev-parse", "refs/adt-personal/previous-good"))
    if (pinned != to_revision or
            run_git(source, "merge-base", "--is-ancestor", to_revision,
                    from_revision, check=False).returncode != 0):
        raise UpdateError("interrupted_rollback_requires_manual_review")
    info = validate_commit(source, to_revision)
    recovered = {**state, "pending_rollback": None,
                 "last_attempt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                 "last_attempt_status": "ROLLED_BACK_AFTER_INTERRUPTION",
                 "last_success_local_date": None,
                 "active_revision": to_revision,
                 "last_known_revision": to_revision,
                 "last_known_toolkit_version": info["toolkit_version"],
                 "previous_good_revision": None,
                 "last_error": None}
    write_state(state_file, recovered)
    return recovered, {"status": "ROLLED_BACK_AFTER_INTERRUPTION",
                       "previous_revision": from_revision,
                       "active_revision": to_revision, **info,
                       "project_files_changed": False, "network_used": False}


def _record_failure(state_file: Path, state: dict[str, Any] | None,
                    error: UpdateError) -> None:
    if state is None:
        return
    try:
        write_state(state_file, {**state,
                                 "last_attempt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                 "last_attempt_status": "FAIL",
                                 "last_error": str(error)})
    except UpdateError:
        # Preserve the original failure and any pending recovery journal.
        pass


def _ensure_rollback_inputs_unchanged(source: Path, *, old: str, target: str) -> None:
    try:
        current = check_sha(git_text(source, "rev-parse", "HEAD"))
        pinned = check_sha(git_text(source, "rev-parse", "refs/adt-personal/previous-good"))
    except UpdateError as exc:
        raise UpdateError("source_changed_before_rollback") from exc
    if current != old or pinned != target:
        raise UpdateError("source_changed_before_rollback")


def rollback(source: Path, state_dir: Path, *, apply: bool = False,
             expected_origin: str = EXPECTED_ORIGIN) -> dict[str, Any]:
    """Explicit safe rollback of only the clean dedicated reference checkout."""
    source = _canonical_path(source, label="source", strict=True)
    state_dir = _canonical_path(state_dir, label="state", strict=False)
    if not apply:
        report = preflight(source, state_dir, expected_origin=expected_origin)
        if not report["rollback_eligible"]:
            raise UpdateError("rollback_unavailable_or_checkout_state_mismatch")
        target = report["previous_good_revision"]
        old = report["active_revision"]
        info = validate_commit(source, target)
        return {"status": "ROLLBACK_PREVIEW", "active_revision": old,
                "previous_good_revision": target, "would_restore": info,
                "project_files_changed": False, "network_used": False}
    with exclusive_lock(state_dir):
        state_file = state_dir / "state.json"
        state = read_state(state_file)
        if state.get("pending_update") is not None:
            raise UpdateError("interrupted_update_requires_manual_review")
        if state.get("pending_rollback") is not None:
            check_origin(source, expected_origin, require_clean=False)
            state, recovered = _recover_pending_rollback(
                source, state_file, state, today=dt.datetime.now().astimezone().date().isoformat())
            if recovered is not None:
                return recovered
        current = preflight(source, state_dir, expected_origin=expected_origin)
        if not current["rollback_eligible"]:
            raise UpdateError("rollback_unavailable_or_checkout_state_mismatch")
        target = current["previous_good_revision"]
        old = current["active_revision"]
        info = validate_commit(source, target)
        pending = {
            "from_revision": old,
            "to_revision": target,
            "from_toolkit_version": current["toolkit_version"],
            "to_toolkit_version": info["toolkit_version"],
            "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        }
        write_state(state_file, {**state,
                                 "pending_rollback": pending,
                                 "last_attempt_utc": pending["started_utc"],
                                 "last_attempt_status": "ROLLING_BACK",
                                 "last_error": None})
        # Revalidate after journaling and immediately before the destructive step.
        check_origin(source, expected_origin)
        _ensure_rollback_inputs_unchanged(source, old=old, target=target)
        run_git(source, "reset", "--hard", target)
        if (check_sha(git_text(source, "rev-parse", "HEAD")) != target or
                run_git(source, "status", "--porcelain", "--untracked-files=all").stdout.strip()):
            raise UpdateError("rollback_result_requires_manual_review")
        write_state(state_file, {**state,
                                 "pending_rollback": None,
                                 "active_revision": target,
                                 "previous_good_revision": None,
                                 "last_success_local_date": None,
                                 "last_attempt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                 "last_attempt_status": "ROLLED_BACK",
                                 "last_error": None})
        return {"status": "ROLLED_BACK", "previous_revision": old,
                "active_revision": target, **info,
                "project_files_changed": False, "network_used": False}


def update(source: Path, state_dir: Path, *, expected_origin: str = EXPECTED_ORIGIN,
           force: bool = False, today: str | None = None) -> dict[str, Any]:
    source = _canonical_path(source, label="source", strict=True)
    state_dir = _canonical_path(state_dir, label="state", strict=False)
    state_file = state_dir / "state.json"
    day = today or dt.datetime.now().astimezone().date().isoformat()
    state: dict[str, Any] | None = None
    with exclusive_lock(state_dir):
        try:
            state = read_state(state_file)
            if state.get("pending_rollback") is not None or state.get("pending_update") is not None:
                # Recovery must inspect a possibly interrupted checkout before requiring cleanliness.
                check_origin(source, expected_origin, require_clean=False)
                state, recovered = _recover_pending_rollback(source, state_file, state, today=day)
                if recovered is not None:
                    return recovered
                state, recovered = _recover_pending_update(source, state_file, state, today=day)
                if recovered is not None:
                    return recovered
            check_origin(source, expected_origin)
            old = check_sha(git_text(source, "rev-parse", "HEAD"))
            if state.get("active_revision") not in (None, old):
                raise UpdateError("state_checkout_mismatch")
            if not force and state.get("last_success_local_date") == day and state.get("active_revision") == old:
                return {"status": "SKIPPED_ALREADY_CHECKED_TODAY", "active_revision": old,
                        "toolkit_version": state.get("last_known_toolkit_version", "NOT_VERIFIED")}

            current_version = self_version(source)
            run_git(source, "fetch", "--no-tags", "--no-write-fetch-head", expected_origin,
                    f"+refs/heads/main:{CANDIDATE_REF}", timeout=65)
            candidate = check_sha(git_text(source, "rev-parse", CANDIDATE_REF))
            if old != candidate:
                ancestor = run_git(source, "merge-base", "--is-ancestor", old, candidate, check=False)
                if ancestor.returncode != 0:
                    raise UpdateError("non_fast_forward_remote_history")
                info = validate_commit(source, candidate)
                if version_tuple(info["toolkit_version"]) < version_tuple(current_version):
                    raise UpdateError("candidate_toolkit_version_downgrade")
                # The durable journal is written before Git mutates the checkout.
                pending = {
                    "from_revision": old,
                    "to_revision": candidate,
                    "from_toolkit_version": current_version,
                    "to_toolkit_version": info["toolkit_version"],
                    "started_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                }
                state = {**state, "pending_update": pending,
                         "last_attempt_utc": pending["started_utc"],
                         "last_attempt_status": "UPDATING", "last_error": None}
                write_state(state_file, state)

                # Must still be the same clean source immediately before mutation.
                check_origin(source, expected_origin)
                if git_text(source, "rev-parse", "HEAD") != old:
                    raise UpdateError("source_changed_during_update")
                run_git(source, "update-ref", "refs/adt-personal/previous-good", old)
                try:
                    run_git(source, "merge", "--ff-only", candidate)
                    check_origin(source, expected_origin)
                    if check_sha(git_text(source, "rev-parse", "HEAD")) != candidate:
                        raise UpdateError("post_update_revision_mismatch")
                    # Filesystem must agree with the already verified Git tree.
                    current_manifest = json.loads((source / "MANIFEST.json").read_text(encoding="utf-8"))
                    if (not isinstance(current_manifest, dict) or
                            current_manifest.get("package") != "ai-development-toolkit"):
                        raise UpdateError("post_update_manifest_invalid")
                except (UpdateError, ValueError, UnicodeError, OSError) as exc:
                    # Only rollback our own exact clean commit, never discard concurrent edits.
                    if (git_text(source, "rev-parse", "HEAD") == candidate and
                            not run_git(source, "status", "--porcelain", "--untracked-files=all").stdout.strip()):
                        try:
                            _ensure_rollback_inputs_unchanged(source, old=candidate, target=old)
                        except UpdateError as rollback_error:
                            raise UpdateError(
                                "post_update_validation_failed_manual_review_required") from rollback_error
                        run_git(source, "reset", "--hard", old)
                        state = {**state, "pending_update": None}
                        raise UpdateError("post_update_validation_failed_rolled_back") from exc
                    raise UpdateError("post_update_validation_failed_manual_review_required") from exc
                result = {"status": "UPDATED", "previous_revision": old,
                          "active_revision": candidate, **info}
            else:
                result = {"status": "UP_TO_DATE", "active_revision": old,
                          "toolkit_version": current_version}

            final_state = {**state, "pending_update": None,
                           "last_attempt_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                           "last_attempt_status": result["status"], "last_success_local_date": day,
                           "active_revision": result["active_revision"],
                           "last_known_revision": candidate,
                           "last_known_toolkit_version": result["toolkit_version"],
                           "previous_good_revision": result.get("previous_revision",
                                                                 state.get("previous_good_revision")),
                           "last_error": None}
            write_state(state_file, final_state)
            _drop_candidate_ref(source)
            return result
        except UpdateError as exc:
            _record_failure(state_file, state, exc)
            raise


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
    try:
        if args.status:
            result = {"status": "STATE", **read_state(args.state_dir / "state.json")}
        elif args.preflight:
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
