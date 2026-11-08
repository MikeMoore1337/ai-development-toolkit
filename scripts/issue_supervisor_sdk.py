#!/usr/bin/env python3
"""Isolated worker for the official OpenAI Codex Python SDK.

The SDK internally installs its own pinned Codex runtime. This is NOT a
Codex Desktop UI control and it is never installed or invoked implicitly.
The owner must acknowledge that runtime before enabling the supervisor.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

API_KEYS = ("OPENAI_API_KEY", "CODEX_API_KEY", "AZURE_OPENAI_API_KEY",
            "OPENAI_BASE_URL", "OPENAI_API_BASE", "ACCESS_TOKEN")


class SDKDenied(ValueError):
    pass


def verify_environment() -> None:
    if any(os.environ.get(name) for name in API_KEYS):
        raise SDKDenied("PAID_OR_EXTERNAL_API_ENVIRONMENT_REFUSED")


def account_kind(account_response: Any) -> str:
    account = getattr(account_response, "account", None)
    account = getattr(account, "root", account)
    kind = getattr(account, "type", None)
    # The official SDK uses a discriminated union for the account protocol.
    if hasattr(kind, "value"):
        kind = kind.value
    return str(kind) if kind is not None else ""


def account_is_chatgpt(account_response: Any) -> bool:
    return account_kind(account_response) == "chatgpt"


def execute_worker(payload: dict[str, Any]) -> dict[str, Any]:
    verify_environment()
    if not isinstance(payload, dict) or payload.get("action") not in ("preflight", "turn"):
        raise SDKDenied("INVALID_WORKER_REQUEST")
    if payload.get("runtime_acknowledged") is not True:
        raise SDKDenied("BUNDLED_RUNTIME_NOT_ACKNOWLEDGED")
    if payload.get("included_usage_confirmed") is not True:
        raise SDKDenied("INCLUDED_PLAN_USAGE_NOT_CONFIRMED")
    try:
        from openai_codex import Codex, ApprovalMode, Sandbox
    except ImportError as exc:
        raise SDKDenied("OFFICIAL_CODEX_SDK_NOT_INSTALLED") from exc
    with Codex() as sdk:
        response = sdk.account()
        if not account_is_chatgpt(response):
            raise SDKDenied("AUTH_NOT_VERIFIED_CHATGPT_PLAN")
        if payload["action"] == "preflight":
            return {"status": "PREFLIGHT_PASS", "auth": "CHATGPT", "api_billing": "NOT_VERIFIED"}
        cwd = payload.get("cwd")
        if not isinstance(cwd, str) or not Path(cwd).is_dir() or not Path(cwd).is_absolute():
            raise SDKDenied("INVALID_WORKTREE")
        prompt = payload.get("prompt")
        if not isinstance(prompt, str) or not 20 <= len(prompt) <= 6000:
            raise SDKDenied("INVALID_PROMPT")
        previous = payload.get("thread_id")
        if previous is not None and (not isinstance(previous, str) or len(previous) > 300):
            raise SDKDenied("INVALID_THREAD_ID")
        kwargs = {"cwd": cwd, "sandbox": Sandbox.workspace_write,
                  "approval_mode": ApprovalMode.auto_review}
        thread = sdk.thread_resume(previous, **kwargs) if previous else sdk.thread_start(**kwargs)
        # Running a turn may have side effects in the isolated worktree.
        # The parent process persists the charged attempt BEFORE launching us.
        result = thread.run(prompt)
        status = getattr(result, "status", None)
        status = getattr(status, "value", status)
        if status != "completed":
            return {"status": "failed", "thread_id": thread.id}
        return {"status": "completed", "thread_id": thread.id}


class CodexSDKRunner:
    """Boundary: no Codex subprocess invocation by the supervisor itself."""

    def __init__(self, policy: dict[str, Any]):
        self.policy = policy
        self.script = str(Path(__file__).resolve())

    def verify_isolation(self) -> None:
        """Refuse until an independent, privilege-separated worker is attested.

        A same-user Windows child can potentially read the owner's gh token
        from Credential Manager even when GH_TOKEN is removed from the
        environment. Prompt-level restrictions cannot prevent this.
        A safe isolated launcher must use an OS identity that cannot access
        the publisher's keyring or home directory; merely setting a Boolean
        in the policy is not proof. No SDK turn is allowed in this revision.
        """
        raise SDKDenied("OS_SEPARATED_WORKER_NOT_ATTESTED")

    def _invoke(self, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
        payload = {"runtime_acknowledged": self.policy["sdk_runtime_acknowledged"],
                   "included_usage_confirmed": self.policy["chatgpt_included_usage_confirmed"],
                   **payload}
        try:
            process = subprocess.run([sys.executable, self.script, "--worker"],
                                     input=json.dumps(payload), text=True,
                                     capture_output=True, encoding="utf-8",
                                     errors="replace", timeout=timeout, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SDKDenied("SDK_PROCESS_TIMEOUT_OR_UNAVAILABLE") from exc
        if process.returncode != 0:
            # Deliberately discard stderr/unknown stdout: SDK traces may include secrets.
            try:
                reply = json.loads(process.stdout)
                reason = reply.get("reason", "")
            except (ValueError, AttributeError):
                reason = ""
            known = ("AUTH_NOT_VERIFIED_CHATGPT_PLAN", "OFFICIAL_CODEX_SDK_NOT_INSTALLED",
                     "PAID_OR_EXTERNAL_API_ENVIRONMENT_REFUSED",
                     "BUNDLED_RUNTIME_NOT_ACKNOWLEDGED",
                     "INCLUDED_PLAN_USAGE_NOT_CONFIRMED")
            raise SDKDenied(reason if reason in known else "SDK_WORKER_FAILED")
        try:
            response = json.loads(process.stdout)
        except ValueError as exc:
            raise SDKDenied("SDK_INVALID_WORKER_RESPONSE") from exc
        if not isinstance(response, dict):
            raise SDKDenied("SDK_INVALID_WORKER_RESPONSE")
        return response

    def preflight(self) -> None:
        r = self._invoke({"action": "preflight"}, timeout=40)
        if r.get("status") != "PREFLIGHT_PASS":
            raise SDKDenied("SDK_PREFLIGHT_FAILED")

    def turn(self, number: int, prompt: str, thread_id: str | None,
             timeout: int, worktree: str) -> dict[str, Any]:
        return self._invoke({"action": "turn", "issue": number, "prompt": prompt,
                             "thread_id": thread_id, "cwd": worktree},
                            timeout=timeout)


def main() -> int:
    if sys.argv[1:] != ["--worker"]:
        return 2
    try:
        request = json.loads(sys.stdin.read(8192))
        result = execute_worker(request)
        print(json.dumps(result))
        return 0 if result.get("status") in ("completed", "PREFLIGHT_PASS") else 2
    except (SDKDenied, ValueError, OSError) as exc:
        # Do not echo the request, account response, prompt, tokens or runtime traces.
        reason = str(exc)
        if reason not in (
            "INVALID_WORKER_REQUEST", "BUNDLED_RUNTIME_NOT_ACKNOWLEDGED",
            "INCLUDED_PLAN_USAGE_NOT_CONFIRMED", "OFFICIAL_CODEX_SDK_NOT_INSTALLED",
            "AUTH_NOT_VERIFIED_CHATGPT_PLAN", "PAID_OR_EXTERNAL_API_ENVIRONMENT_REFUSED",
            "INVALID_WORKTREE", "INVALID_PROMPT", "INVALID_THREAD_ID"):
            reason = "SDK_WORKER_FAILED"
        print(json.dumps({"status": "REFUSED", "reason": reason}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
