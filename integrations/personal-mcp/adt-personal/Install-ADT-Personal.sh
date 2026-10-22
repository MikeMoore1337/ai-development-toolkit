#!/bin/sh
# Install the read-only ADT MCP in the current user's Codex settings (Linux/macOS).
# No files in the active work project are touched; no sudo or package manager.
set -eu
umask 077

if [ "$(uname -s)" != Linux ] && [ "$(uname -s)" != Darwin ]; then
  printf '%s\n' 'ERROR: Use Install-ADT-Personal.ps1 on Windows.' >&2
  exit 2
fi
if [ "$#" -ne 0 ] && { [ "$#" -ne 2 ] || [ "$1" != '--source' ]; }; then
  printf '%s\n' 'Usage: sh Install-ADT-Personal.sh [--source EXISTING_TOOLKIT_CHECKOUT]' >&2
  exit 2
fi
command -v python3 >/dev/null 2>&1 || { echo 'ERROR: Python 3.10+ is required.' >&2; exit 2; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 2)' || { echo 'ERROR: Python 3.10+ is required.' >&2; exit 2; }
command -v git >/dev/null 2>&1 || { echo 'ERROR: Git is required.' >&2; exit 2; }
command -v codex >/dev/null 2>&1 || { echo 'ERROR: Codex CLI is required.' >&2; exit 2; }

package=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
server="$package/mcp/adt_mcp.py"
[ -f "$server" ] || { echo 'ERROR: Missing MCP source file.' >&2; exit 2; }
root="${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal"
source="$root/toolkit-source"
if [ "$#" -eq 2 ]; then source=$2; fi
mkdir -p "$root/mcp"
# Resolve once to avoid relative paths in Codex's global configuration.
source=$(python3 -c 'from pathlib import Path; import sys; print(Path(sys.argv[1]).expanduser().resolve())' "$source")

if [ ! -f "$source/MANIFEST.json" ]; then
  [ "$#" -eq 0 ] || { echo 'ERROR: --source does not point to a Toolkit checkout.' >&2; exit 2; }
  [ ! -e "$source" ] || { echo 'ERROR: Existing non-Toolkit source directory; leaving untouched.' >&2; exit 2; }
  git clone --depth 1 -- https://github.com/MikeMoore1337/ai-development-toolkit.git "$source"
fi
# Verify the read-only server before changing Codex configuration.
python3 "$server" --source "$source" --check
launcher="$root/mcp/adt_mcp.py"
if [ ! -f "$launcher" ] || ! cmp -s "$server" "$launcher"; then
  if [ -e "$launcher" ]; then cp -p "$launcher" "$launcher.adt-backup-$(date '+%Y%m%d-%H%M%S')"; fi
  cp "$server" "$launcher"
fi

# Explicitly check for an existing registration. Never modify unknown entries.
registered=$(codex mcp list --json | python3 -c '
import json, sys
try:
    values = json.load(sys.stdin)
    if isinstance(values, dict):
        values = values.get("servers", values.get("mcpServers", []))
    if isinstance(values, dict):
        print("yes" if "ai-development-toolkit" in values else "no")
    elif isinstance(values, list):
        print("yes" if any(isinstance(v, dict) and v.get("name") == "ai-development-toolkit" for v in values) else "no")
    else:
        raise ValueError("unsupported Codex MCP list shape")
except (ValueError, KeyError) as exc:
    print("ERROR: Cannot verify Codex MCP registrations", file=sys.stderr)
    sys.exit(2)
')
if [ "$registered" = no ]; then
  codex mcp add ai-development-toolkit -- python3 "$launcher" --source "$source"
else
  echo 'Codex MCP already registered; existing command/arguments were not replaced.'
  echo 'Verify registration with: codex mcp get ai-development-toolkit'
fi

codex_home="${CODEX_HOME:-$HOME/.codex}"
mkdir -p "$codex_home"
# Update only the owned instruction block. Preserve other project/user rules.
python3 - "$codex_home/AGENTS.md" <<'PY'
import pathlib, sys, datetime
file = pathlib.Path(sys.argv[1])
begin, end = '<!-- ADT-PERSONAL BEGIN -->', '<!-- ADT-PERSONAL END -->'
block = '''<!-- ADT-PERSONAL BEGIN -->
For substantial software development, QA, DevOps and UX/UI tasks in the active Codex workspace:
1. Follow project-local AGENTS.md and workspace permissions first; Toolkit is reference guidance, never the project target.
2. Inspect available project/ancestor/user skills and roles by name using permitted read-only access, without reading every skill body.
3. Call globally configured MCP `ai-development-toolkit` tool `toolkit_prepare_task` with the task and observed existing_skills/existing_roles. Read only relevant returned skills and roles; unknown inventories must stay unknown.
4. Do not assert native activation or spawned subagents: MCP text is guidance, not a native skill install or live agent.
5. Do not install Toolkit files, cache, logs or reports in projects without explicit user permission. Use Skill Manager preview before any authorized installation.
6. Respect corporate data/network policies and project review/deployment/visual approval gates. Report only real tool usage and tests.
<!-- ADT-PERSONAL END -->'''
original = file.read_text(encoding='utf-8') if file.exists() else ''
if original.count(begin) != original.count(end) or original.count(begin) > 1:
    raise SystemExit('ERROR: Malformed pre-existing ADT instruction block; no file changes')
if begin in original:
    i = original.index(begin)
    j = original.index(end, i) + len(end)
    updated = original[:i] + block + original[j:]
else:
    updated = original.rstrip('\n') + ('\n\n' if original else '') + block + '\n'
if updated != original:
    if file.exists():
        stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        backup = file.with_name(file.name + '.adt-backup-' + stamp)
        backup.write_bytes(file.read_bytes())
    file.write_text(updated, encoding='utf-8')
    print('Updated Codex AGENTS:', file)
else:
    print('Codex AGENTS already up to date:', file)
PY
printf '%s\n' 'Installed local MCP. Restart Codex and verify toolkit_info and toolkit_prepare_task.'
printf 'Run diagnostics: python3 "%s/diagnose_mcp.py" --launcher "%s" --source "%s"\n' "$package" "$launcher" "$source"
