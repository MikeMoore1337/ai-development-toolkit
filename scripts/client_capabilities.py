#!/usr/bin/env python3
"""Offline conversation-client contracts, capability routing and ZIP preflight.

No AI client calls, installation, extraction, network access or project writes.
A source URL is never evidence that a skill was discovered or invoked.
"""
from __future__ import annotations

import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "compatibility" / "conversational_clients.json"
CLIENT_IDS = frozenset({"chatgpt", "claude-ai"})
CLIENT_TYPE = "CONVERSATIONAL_REFERENCE_CLIENT"
CAPABILITIES = frozenset({
    "toolkit_access", "file_read", "file_write", "terminal", "browser",
    "github_access", "attachments", "zip_handling", "skill_installation",
    "skill_discovery", "tool_invocation", "separate_agents", "external_actions",
})
CAP_STATES = frozenset({"AVAILABLE", "UNAVAILABLE", "NOT_TESTED", "UNKNOWN",
                        "REQUIRES_PERMISSION", "NOT_APPLICABLE"})
SUPPORT_STATES = frozenset({"VERIFIED", "PARTIAL", "NOT_TESTED", "UNSUPPORTED",
                            "UNKNOWN", "BLOCKED", "OWNER_REPORTED_PASS",
                            "EVIDENCE_NOT_ATTACHED"})
LEVEL_STATES = SUPPORT_STATES | {"NOT_APPLICABLE", "NOT_MEASURED"}
LEVELS = tuple(f"L{i}" for i in range(1, 7))
SCENARIOS = frozenset({"toolkit_url", "zip_plus_toolkit_url",
                       "chat_only", "hosted_skill_upload"})
REQUIRED = frozenset({
    "client_id", "client_type", "client_version", "client_name", "operating_mode",
    "documentation_url", "secondary_source", "source_contract_status",
    "native_skill_support", "native_skill_mechanism", "capabilities",
    "approval_requirements", "evidence", "scenarios", "historical_evidence",
    "limitations", "limit",
})
# Schema does not repeat filesystem layout or pretend to install hosted Skills.
HOSTS = {"chatgpt": "https://help.openai.com/",
         "claude-ai": "https://support.claude.com/"}
MAX_ENTRIES = 1000
MAX_UNCOMPRESSED = 64 * 1024 * 1024
MAX_RATIO = 80
SECRET_NAMES = re.compile(
    r"(?:^|/)(?:\.env(?:\..*)?|id_rsa|id_ed25519|credentials\.json|"
    r".*\.(?:pem|p12|pfx|key))$", re.IGNORECASE
)


class CapabilityError(ValueError):
    """A capability claim, client contract or ZIP violates a safety boundary."""


def load_conversations(path: Path = REGISTRY) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or set(data) != {
        "schema_version", "registry_kind", "companion_filesystem_registry",
        "reviewed_on", "clients"
    } or data["schema_version"] != 1:
        raise CapabilityError("Invalid conversational registry schema")
    if (data["registry_kind"] != CLIENT_TYPE or
            data["companion_filesystem_registry"] != "compatibility/clients.json" or
            not re.fullmatch(r"20\d\d-\d\d-\d\d", str(data["reviewed_on"]))):
        raise CapabilityError("Invalid conversational registry reference or review date")
    if not isinstance(data["clients"], list) or len(data["clients"]) != 2:
        raise CapabilityError("Conversational clients are missing")
    found = set()
    for row in data["clients"]:
        if not isinstance(row, dict) or set(row) != REQUIRED:
            raise CapabilityError("Invalid conversational client fields")
        client = row["client_id"]
        if client not in CLIENT_IDS or client in found:
            raise CapabilityError(f"Unknown or duplicated conversational client: {client}")
        found.add(client)
        if (row["client_type"] != CLIENT_TYPE or row["operating_mode"] != "GUIDANCE_ONLY" or
                row["client_version"] is not None):
            raise CapabilityError("Conversation client must not impersonate filesystem client")
        if (not row["documentation_url"].startswith(HOSTS[client]) or
                not row["secondary_source"].startswith(HOSTS[client]) or
                row["source_contract_status"] != "VERIFIED"):
            raise CapabilityError("Missing verified official source contract")
        if (row["native_skill_support"] not in SUPPORT_STATES or
                not row["native_skill_mechanism"] or not row["approval_requirements"] or
                not row["limitations"]):
            raise CapabilityError("Missing native skills/approval limitations")
        if (not isinstance(row["capabilities"], dict) or
                set(row["capabilities"]) != CAPABILITIES or
                any(x not in CAP_STATES for x in row["capabilities"].values())):
            raise CapabilityError("Invalid capability contract")
        if any(x == "AVAILABLE" for x in row["capabilities"].values()):
            raise CapabilityError("Generic documentation cannot prove session capability")
        if (not isinstance(row["evidence"], dict) or set(row["evidence"]) != set(LEVELS)
                or any(x not in LEVEL_STATES for x in row["evidence"].values())):
            raise CapabilityError("Invalid L1-L6 evidence contract")
        if (row["evidence"] != {"L1": "NOT_APPLICABLE", "L2": "NOT_APPLICABLE",
                                "L3": "VERIFIED", "L4": "NOT_TESTED",
                                "L5": "NOT_TESTED", "L6": "NOT_MEASURED"}):
            raise CapabilityError("L4-L6 are unmeasured; L1-L2 not applicable to URL guidance")
        if (not isinstance(row["scenarios"], dict) or
                set(row["scenarios"]) != SCENARIOS or
                row["scenarios"]["zip_plus_toolkit_url"] != "OWNER_REPORTED_PASS" or
                any(v not in SUPPORT_STATES for v in row["scenarios"].values())):
            raise CapabilityError("Historical ZIP evidence must remain owner-reported")
    if found != CLIENT_IDS:
        raise CapabilityError("Conversational inventory mismatch")
    return data


def select_route(client_type: str, capabilities: dict, *,
                 installed_skill: bool = False, toolkit_url: bool = False,
                 toolkit_attachment: bool = False, project_archive: bool = False) -> dict:
    """Choose a route using observed in-session capabilities, not product branding.

    Source/project read access is separate from installing, changing or testing.
    """
    if client_type not in {"FILESYSTEM_SKILL_CLIENT", CLIENT_TYPE}:
        raise CapabilityError("Unknown client type")
    if set(capabilities) != CAPABILITIES or any(
            value not in CAP_STATES for value in capabilities.values()):
        raise CapabilityError("Invalid runtime capabilities")
    available = lambda key: capabilities[key] == "AVAILABLE"
    if (client_type == "FILESYSTEM_SKILL_CLIENT" and installed_skill
            and available("skill_discovery") and available("file_read")):
        route = "NATIVE_FILESYSTEM_SKILL"
    elif toolkit_url and available("toolkit_access") and available("file_read"):
        route = "TOOLKIT_REFERENCE"
    elif toolkit_attachment and available("attachments") and available("file_read"):
        route = "ATTACHMENT_GUIDANCE"
    else:
        route = "MANUAL_FALLBACK"
    return {
        "route": route,
        "guidance_status": ("GUIDANCE_ONLY" if route in
                            {"TOOLKIT_REFERENCE", "ATTACHMENT_GUIDANCE"} else
                            "NOT_VERIFIED"),
        "project_archive_status": ("ATTACHMENT_AVAILABLE" if project_archive and
                                   available("attachments") and available("zip_handling")
                                   and available("file_read") else "ATTACHMENT_UNAVAILABLE"),
        "file_write": available("file_write"),
        "tests_executed": False,
        "skill_invoked": False,
    }


def validate_execution_claim(claim: dict) -> None:
    """Independent offline oracle: reject unobserved outcomes, paid calls and fake agents."""
    required = {"route", "read_source", "attachment_read", "files_written", "write_access",
                "tests_run", "test_evidence", "skill_discovered", "discovery_evidence",
                "skill_invoked", "invocation_evidence", "measured_effectiveness",
                "baseline_evidence", "model_called", "model_evidence",
                "separate_agent", "separate_agent_evidence", "paid_api_calls",
                "approved_install", "installed", "owner_report_only"}
    if not isinstance(claim, dict) or set(claim) != required:
        raise CapabilityError("Invalid execution evidence fields")
    if claim["route"] not in {"NATIVE_FILESYSTEM_SKILL", "TOOLKIT_REFERENCE",
                               "ATTACHMENT_GUIDANCE", "MANUAL_FALLBACK"}:
        raise CapabilityError("Unknown route")
    for key in required - {"route", "test_evidence", "discovery_evidence",
                           "invocation_evidence", "baseline_evidence",
                           "model_evidence", "separate_agent_evidence"}:
        if not isinstance(claim[key], bool):
            if key != "paid_api_calls":
                raise CapabilityError("Non-boolean execution claim: " + key)
    if claim["paid_api_calls"] != 0:
        raise CapabilityError("Paid API calls forbidden by Issue #11")
    if claim["installed"] and not claim["approved_install"]:
        raise CapabilityError("Installation without separate approval")
    if claim["route"] == "NATIVE_FILESYSTEM_SKILL" and not (
            claim["installed"] and claim["skill_discovered"]):
        raise CapabilityError("False native discovery")
    if claim["route"] == "TOOLKIT_REFERENCE" and not claim["read_source"]:
        raise CapabilityError("Toolkit source was not read")
    if claim["route"] == "ATTACHMENT_GUIDANCE" and not claim["attachment_read"]:
        raise CapabilityError("Attachment was not accessible")
    if claim["files_written"] and not claim["write_access"]:
        raise CapabilityError("False write access")
    for action, evidence, message in (
        ("tests_run", "test_evidence", "Tests not run"),
        ("skill_discovered", "discovery_evidence", "False skill discovery"),
        ("skill_invoked", "invocation_evidence", "False skill invocation"),
        ("measured_effectiveness", "baseline_evidence", "False model effectiveness"),
        ("model_called", "model_evidence", "False model call"),
        ("separate_agent", "separate_agent_evidence", "Fake subagent"),
    ):
        if claim[action] and not isinstance(claim[evidence], str):
            raise CapabilityError(message)
        if claim[action] and not claim[evidence].strip():
            raise CapabilityError(message)
    if claim["skill_invoked"] and not claim["skill_discovered"]:
        raise CapabilityError("Invocation without discovery evidence")
    if claim["measured_effectiveness"] and not claim["model_called"]:
        raise CapabilityError("Measured effectiveness requires a real model baseline")
    if claim["owner_report_only"] and (
            claim["skill_invoked"] or claim["measured_effectiveness"]):
        raise CapabilityError("Owner report cannot prove L5/L6")
    if claim["route"] != "NATIVE_FILESYSTEM_SKILL" and (
            claim["skill_discovered"] or claim["skill_invoked"]):
        raise CapabilityError("URL/attachment guidance cannot prove native skill invocation")



def inspect_zip(path: Path) -> dict:
    """Read-only ZIP metadata inspection. Never extracts or executes archive contents."""
    if path.suffix.lower() != ".zip" or not path.is_file() or path.is_symlink():
        raise CapabilityError("ATTACHMENT_UNAVAILABLE or unsupported ZIP")
    names = set()
    count = files = total = 0
    try:
        with zipfile.ZipFile(path, "r") as archive:
            for info in archive.infolist():
                count += 1
                if count > MAX_ENTRIES:
                    raise CapabilityError("ZIP file count exceeds safe limit")
                # Inspect the unsanitized original. Windows zipfile normalizes backslashes.
                name = info.orig_filename
                entry = name[:-1] if info.is_dir() and name.endswith("/") else name
                normalized = PurePosixPath(entry)
                if (not entry or entry.startswith("/") or "\\" in entry or
                        re.match(r"^[A-Za-z]:", entry) or
                        any(part in {"", ".", ".."} for part in entry.split("/")) or
                        "\x00" in entry):
                    raise CapabilityError("Unsafe ZIP path traversal/absolute path")
                if normalized.as_posix().casefold() in names:
                    raise CapabilityError("Duplicate or colliding ZIP paths")
                names.add(normalized.as_posix().casefold())
                if SECRET_NAMES.search(entry):
                    raise CapabilityError("ZIP contains possible secrets")
                mode = stat.S_IFMT(info.external_attr >> 16)
                if info.is_dir():
                    if mode not in {0, stat.S_IFDIR}:
                        raise CapabilityError("Linked or non-directory ZIP entry")
                    continue
                files += 1
                if mode not in {0, stat.S_IFREG}:
                    raise CapabilityError("Linked or non-regular ZIP entry")
                if info.flag_bits & 1 or info.compress_type not in {
                        zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}:
                    raise CapabilityError("Encrypted or unsupported ZIP entry")
                if name.casefold().endswith((".zip", ".tar", ".tgz", ".7z", ".rar", ".gz")):
                    raise CapabilityError("Nested archive requires separate approval")
                total += info.file_size
                if total > MAX_UNCOMPRESSED or info.file_size > (
                        max(info.compress_size, 1) * MAX_RATIO):
                    raise CapabilityError("ZIP expansion exceeds safe limit")
            if not files:
                raise CapabilityError("Empty ZIP archive")
            bad = archive.testzip()
            if bad is not None:
                raise CapabilityError("Corrupted ZIP member")
    except (zipfile.BadZipFile, EOFError, OSError, RuntimeError) as exc:
        raise CapabilityError("Corrupted ZIP archive") from exc
    return {"status": "ZIP_PREFLIGHT_PASS", "entries": files,
            "uncompressed_bytes": total, "extracted": False}
