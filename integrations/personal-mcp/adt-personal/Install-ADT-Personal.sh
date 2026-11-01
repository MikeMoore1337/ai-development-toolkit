#!/bin/sh
# Install the read-only ADT MCP in the current user's Codex settings (Linux/macOS).
# No files in the active work project are touched; no sudo or package manager.
set -eu
umask 077

if [ "$(uname -s)" != Linux ] && [ "$(uname -s)" != Darwin ]; then
  printf '%s\n' 'ERROR: Use Install-ADT-Personal.ps1 on Windows.' >&2
  exit 2
fi
skip_global_instructions=0
if [ "${1:-}" = "--skip-global-instructions" ]; then
  skip_global_instructions=1
  shift
fi
if [ "$#" -ne 0 ] && { [ "$#" -ne 2 ] || [ "$1" != '--source' ]; }; then
  printf '%s\n' 'Usage: sh Install-ADT-Personal.sh [--skip-global-instructions] [--source EXISTING_TOOLKIT_CHECKOUT]' >&2
  exit 2
fi
command -v python3 >/dev/null 2>&1 || { echo 'ERROR: Python 3.10+ is required.' >&2; exit 2; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 2)' || { echo 'ERROR: Python 3.10+ is required.' >&2; exit 2; }
command -v git >/dev/null 2>&1 || { echo 'ERROR: Git is required.' >&2; exit 2; }
command -v codex >/dev/null 2>&1 || { echo 'ERROR: Codex CLI is required.' >&2; exit 2; }

package=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
server="$package/mcp/adt_mcp.py"
discovery="$package/mcp/adt_discovery.py"
[ -f "$server" ] && [ -f "$discovery" ] || {
  echo 'ERROR: Incomplete MCP source bundle (adt_mcp.py + adt_discovery.py required).' >&2
  exit 2
}
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
installed_discovery="$root/mcp/adt_discovery.py"
# Never follow user-owned links when replacing files in the persistent launcher.
if [ -L "$launcher" ] || [ -L "$installed_discovery" ]; then
  echo 'ERROR: Linked MCP installation destination is unsafe.' >&2
  exit 2
fi
# Both Python modules must be from the same package revision. Existing
# single-file installs are transparently upgraded without re-registering MCP.
if [ ! -f "$launcher" ] || ! cmp -s "$server" "$launcher" ||
   [ ! -f "$installed_discovery" ] || ! cmp -s "$discovery" "$installed_discovery"; then
  stage=$(mktemp -d "$root/mcp/.adt-stage.XXXXXXXX") || exit 2
  # Stage and validate both files before touching an existing installation.
  cp "$server" "$stage/adt_mcp.py"
  cp "$discovery" "$stage/adt_discovery.py"
  if ! python3 "$stage/adt_mcp.py" --source "$source" --check; then
    rm -rf -- "$stage"
    echo 'ERROR: Staged MCP bundle failed validation; previous installation preserved.' >&2
    exit 2
  fi
  had_launcher=no
  had_discovery=no
  stamp=$(date '+%Y%m%d-%H%M%S')
  if [ -f "$launcher" ]; then
    cp -p "$launcher" "$stage/old_launcher"
    cp -p "$launcher" "$launcher.adt-backup-$stamp"
    had_launcher=yes
  fi
  if [ -f "$installed_discovery" ]; then
    cp -p "$installed_discovery" "$stage/old_discovery"
    cp -p "$installed_discovery" "$installed_discovery.adt-backup-$stamp"
    had_discovery=yes
  fi
  if mv -f "$stage/adt_discovery.py" "$installed_discovery" &&
     mv -f "$stage/adt_mcp.py" "$launcher" &&
     python3 "$launcher" --source "$source" --check; then
    rm -rf -- "$stage"
  else
    # Only restore files owned by this installer. Preserve previous backups.
    if [ "$had_launcher" = yes ]; then
      cp -p "$stage/old_launcher" "$launcher"
    else
      rm -f -- "$launcher"
    fi
    if [ "$had_discovery" = yes ]; then
      cp -p "$stage/old_discovery" "$installed_discovery"
    else
      rm -f -- "$installed_discovery"
    fi
    rm -rf -- "$stage"
    echo 'ERROR: MCP upgrade failed; previous files restored.' >&2
    exit 2
  fi
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
if [ "$skip_global_instructions" -eq 0 ]; then
python3 - "$codex_home/AGENTS.md" <<'PY'
import pathlib, sys, datetime
file = pathlib.Path(sys.argv[1])
begin, end = '<!-- ADT-PERSONAL BEGIN -->', '<!-- ADT-PERSONAL END -->'
block = '''<!-- ADT-PERSONAL BEGIN -->
0. NATIVE UPSTREAM BOUNDARY: If the user explicitly selects an original external tool, agent, skill, plugin or MCP as task controller, do not call Toolkit routing, inject Toolkit skills/roles/controllers or change upstream modes and hooks. Mentioning a tool is not selection. If routing was accidentally invoked, send its client-observed identifier as external_controller and respect NATIVE_UPSTREAM_PASSTHROUGH. A separate explicit request may obtain focused read-only Toolkit references, but never a second controller. Host/system safety, project rules, permissions, cost consent and release gates remain binding.
For substantial software development, QA, DevOps and UX/UI tasks in the active Codex workspace:
1. Follow project-local AGENTS.md and workspace permissions first; Toolkit is reference guidance, never the project target.
2. Inspect available project/ancestor/user skills and roles by name using permitted read-only access, without reading every skill body.
3. Call globally configured MCP `ai-development-toolkit` tool `toolkit_prepare_task` with the task and observed existing_skills/existing_roles. Read only relevant returned skills and roles; unknown inventories must stay unknown.
   Reassess meaningful stage changes with `toolkit_prepare_stage` when available: supply the original task, stage, justified skill names, relevant fully read instruction digests, exclusions and active controller. Use bounded batches only as needed. Installed names are not proof of reading; do not loop on no progress. Otherwise use targeted reads and report the limitation.
4. Do not assert native activation or spawned subagents: MCP text is guidance, not a native skill install or live agent.
5. A request to work with Toolkit includes installing missing task-required skills and tools within existing host/project permissions. Verify actual absence and source/license/pinned files first; prefer user scope. For bundled skills use Skill Manager `ensure` preview, then `--apply` without asking again for already authorized setup. Review external originals and their necessary dependencies before using their native installer. Preserve existing skills; never overwrite or adopt unmanaged files. Honor explicit reference-only/no-install requests. If setup cannot run, report the concrete BLOCKED reason instead of claiming the required tool ran. Verify files, client discovery and invocation separately. Keep project reports and caches outside Toolkit; project-scoped installation follows project approval rules.
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
fi
printf '%s\n' 'Installed local MCP. Restart Codex and verify toolkit_info and toolkit_prepare_task.'
printf 'Run diagnostics: python3 "%s/diagnose_mcp.py" --launcher "%s" --source "%s"\n' "$package" "$launcher" "$source"
