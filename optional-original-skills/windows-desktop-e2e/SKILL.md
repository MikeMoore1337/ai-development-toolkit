---
name: windows-desktop-e2e
description: Design, implement, and diagnose end-to-end tests for real native Windows desktop applications (WPF, WinForms, Win32/MFC, WinUI, or Qt) using Windows UI Automation and pywinauto. Use only when the requested target is a Windows native GUI; not for websites, browser-based Electron/WebView2 content, mobile, or pure API tests.
compatibility: Windows interactive user session required for actual UIA execution; all other systems support documentation and offline checks only.
metadata:
  origin: ECC 2.2.3, native Toolkit port
  source-revision: 25278e7d7b6cf6e6a4e7a6c8e10f14ff22f0eb5b
---

# Windows desktop UIA end-to-end tests

Toolkit-native guidance. No ECC installation, CLI, MCP, plugin, service, agent runtime, or provider API is required. For additional examples consult the [unchanged original reference](references/ORIGINAL_SKILL.md) only when relevant. The MIT notice is distributed separately as `LICENSE` with a selective installation. Source: affaan-m/ECC, Copyright (c) 2026 Affaan Mustafa.

## Activation and scope

- Activate for an explicitly authorized **native Windows GUI** test task on WPF, WinForms, Win32/MFC, WinUI, or Qt. Use `pywinauto` with the Windows UI Automation (`uia`) backend; inspect the UIA tree before selecting controls.
- For web interfaces, Electron / CEF / WebView2 HTML, mobile, or pure API tests, use the existing Toolkit browser, mobile, or API skills instead. Do not assert UIA support for inaccessible surfaces.
- A skill selection or an offline validation is **not** evidence that Windows UI automation ran.

## Workflow

1. Confirm the target executable and repository, permitted test account, Windows interactive session, test data, and owner-approved command/process scope. Do not launch or modify a real user application, workstation, or external service without permission.
2. Agree on observable E2E outcomes before actions: window identity, accessible control identifiers, state changes, application logs, and independent assertions. Prefer stable `AutomationId` / accessible names to coordinates or translated labels.
3. Inspect application technology, UIA support and session permissions. For Qt 5, review the relevant accessibility configuration; for Qt 6, verify accessible widgets rather than assuming full coverage.
4. Use page objects, bounded explicit waits, per-test isolated `APPDATA`, `LOCALAPPDATA` and `TEMP`, deterministic teardown, and isolated synthetic credentials. Never target a personal user profile or a production data store.
5. Capture minimum necessary diagnostics (failed step, safe logs and optional screenshots). Redact secrets, credentials and private data. Opt-in text traces can expose entered values; default to OFF.
6. Run negative paths (missing controls, broken permissions, unexpected dialogs, app exit, timeouts), check failure containment, and report blocked/unverified environments truthfully.
7. For CI use an approved interactive Windows runner and explicitly verify the desktop session. Hosted `windows-latest` source tests alone do not prove real GUI E2E. Do not claim a run based only on green structural tests.

## Owner boundaries

- Do not install `pywinauto`, run a GUI test binary, enable recording, download third-party scripts, invoke shell commands, start an untrusted app, modify global Windows configuration, or use Windows Sandbox without explicit owner authorization.
- Never turn a reference example into an automatically executing hook or script. No elevated privileges, CLI agent invocation, paid API, or additional subscription is part of this skill.
- Use a distinct rollback/cleanup plan for application files, processes, registry state, data and artifacts. Windows Job Objects only bound process lifetime; filesystem isolation does not isolate registry or network.
- For Electron/CEF/WebView2 native shells, test shell-only UIA elements separately and route embedded HTML content to Playwright; no unsupported cross-surface claims.

**Evidence:** target and framework, approved scope, UIA accessibility evidence, tested outcome and negative oracles, exact run environment, CI/check identifiers, redacted artifact locations, cleanup result, and `PASS`/`FAIL`/`BLOCKED`/`NOT_VERIFIED` per result.

## Reference index

The [complete unchanged ECC v2.2.3 reference](references/ORIGINAL_SKILL.md) includes framework-specific AutomationId setup; pytest / page-object examples; locator and wait strategies; screenshots, recording, per-step trace; flaky-test handling; three tiers of isolation; Windows CI; Qt details. Read only sections needed for the current native GUI task, with the permissions above taking precedence.
