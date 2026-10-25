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
