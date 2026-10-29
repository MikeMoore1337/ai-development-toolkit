# Toolkit MCP security scan - Cisco adapter (#359)

[Русская версия](ru/MCP_SECURITY_SCAN.md)

Toolkit supports a separate **optional** Cisco MCP Scanner check for MCP
tool descriptions. It does not install anything into client projects or
automatically authorize an MCP connection.

## First-party scope

- `personal`: the declared `TOOLS` in
  `integrations/personal-mcp/adt-personal/mcp/adt_mcp.py`.
- `project`: `_tool_defs()` in `scripts/toolkit_mcp.py`.

The exporter reads first-party Python declarations in-process. It never
starts `serve()`, invokes `tools/call`, resolves a remote server URL,
uses credentials, or reads private user files. Scanner input is an
ephemeral `{"tools":[...]}` JSON snapshot. Server instructions, prompts,
resources and **runtime effects** are outside this tool-only scan scope
and retain their separate security review requirements.

## Run an explicit static scan

Install `uv` (`uvx`), then in the Toolkit repository:

```bash
python scripts/cisco_mcp_gate.py --scope personal
python scripts/cisco_mcp_gate.py --scope project
```

Adapter uses Cisco open-source scanner [mcp-scanner](https://github.com/cisco-ai-defense/mcp-scanner)
at pinned commit `4dd0caae7b0d3a80c8c09ed7e4680a9911b0a86e`
(Apache-2.0) via a separate `uvx` process, with
`--analyzers yara,schema --format raw static --tools <temporary-json>`.
Only YARA and schema analyzers are requested. No paid API, LLM analysis,
live MCP RPC, Cisco account or Codex CLI is required.

**Network boundary:** initial pinned scanner/package installation may
download dependencies. A static scan does not use a remote MCP server;
no credential variables are intentionally passed to the analyzer.
The tool itself and `uv` may use the network to obtain dependencies.
For an offline environment, provision pinned dependencies separately.

## Results and limitations

`PASS`: every declared tool and requested analyzer reported complete and
safe. `REVIEW_REQUIRED`: completed findings with informational/moderate
severity; manual triage required. `BLOCKED`: critical/high finding,
missing/partial coverage, mismatched scanner output, tool error or timeout.
No result grants a runtime permission or installation.

Tests use synthetic RU/EN descriptions and mocked scanner findings to
check orchestration and fail-closed mapping. These **do not prove** the
upstream YARA rules detect every malicious Russian or English example.
Real upstream scanner smoke is separate from test fixtures. Static
descriptions do not prove `readOnlyHint` truth or prevent malicious
implementation-side effects; source and operating-system policies remain
mandatory. Use [Security Gate](EXTERNAL_SKILL_GATE.md) separately for skills.

```bash
python -m unittest tests.test_cisco_mcp_gate -v
```

## Native offline heuristic (ECC uplift #432)

For **basic first-party description injection checks without installing Cisco or ECC**, run:

```sh
python scripts/cisco_mcp_gate.py --scope personal --native
python scripts/cisco_mcp_gate.py --scope project --native
```

This flag uses the existing static declaration `snapshot()` and a small Toolkit-native rule set. It checks the descriptions of declared tools and nested input schemas for RU/EN instruction override, fake system roles, credential exfiltration instructions and collection domains. Duplicate names, malformed schemas, missing descriptions and oversized data fail closed. Results name only the tool, rule and severity - never echo the untrusted phrase or secret. The operation is offline, read-only, and runs no Cisco scanner, MCP methods, hooks, CLI agents or model APIs.

`PASS` means **no match among these limited heuristic patterns**, not that a tool or implementation is secure. `REVIEW_REQUIRED` covers collector domains; `BLOCKED` covers injection-like findings or invalid data. Existing Cisco `--scope` behavior without `--native` is unchanged, remains optional and provides independent YARA/schema checks. No real model/tool poisoning adversarial trial, client-side enforcement, production activation or measured AgentShield parity is claimed.

Comparison source: [AgentShield pinned `b0891303bdcd6037376a94263d45cfd2ff3dfb98`](https://github.com/affaan-m/agentshield/tree/b0891303bdcd6037376a94263d45cfd2ff3dfb98) (MIT). Toolkit code is original and does not copy AgentShield modules. Rollback is a normal revision revert; no client configuration changes.

### Reproducible synthetic benchmark (#432)

Run the **diagnostic-only** 16-case bilingual labeled challenge set:

\`\`\`sh
python scripts/cisco_mcp_gate.py --benchmark-native
python -m unittest tests.test_cisco_mcp_gate -v
\`\`\`

The JSON contains a stable SHA-256 of the 8 attack-like and 8 benign synthetic descriptions, confusion matrix (\`tp\`, \`fp\`, \`tn\`, \`fn\`), precision and recall, and case IDs for false positives and missed attacks. \`REVIEW_REQUIRED\` counts as an alert, not a confirmed exploit. No case contents, secret-like strings or session data are emitted; no Cisco, AgentShield, model, network or MCP server is run. The command returns zero for a **completed diagnostic** even if the scanner misses attacks; it is *not* a security-release gate.

Initial native rule baseline deliberately exposes both missed instruction variants and false alarms on explanatory or negated language; do **not** claim 100% precision, production-world accuracy, or superiority over AgentShield. \`upstream_agentshield_comparison=NOT_RUN\` means no head-to-head comparison was executed. This synthetic score is suitable for detecting regressions under future rule changes, not an estimate of unseen real-world attacks. Separate pinned upstream comparison, representative independent holdouts and real client enforcement remain open under #432.

### Native heuristic calibration (#432)

The native gate now recognizes narrowly defined **whole-description** defensive examples and direct English/Russian instructions to override safety policies. A generic `example:` prefix or benign-sounding disclaimer appended to a malicious instruction never grants exemption. This reduces known synthetic false positives and false negatives, but **does not** guarantee injection resistance: variants, obfuscation and multilingual attacks outside the static patterns can still be missed. Run `python scripts/cisco_mcp_gate.py --benchmark-native` to inspect current **synthetic** confusion metrics; only the full output of that exact code version is evidence. Upstream AgentShield comparison and real-client enforcement remain NOT_RUN/NOT_VERIFIED.
