#!/usr/bin/env bash
# Read-only local prerequisites for ORIGINAL pinned Harness2 under Ubuntu/WSL2.
# Invoked by acceptance.ps1 as a path, never through a multiline bash -c argument.
set -Eeuo pipefail

[[ "$(id -u)" != 0 ]] || { echo 'HARNESS2_REFUSED_ROOT' >&2; exit 2; }
grep -qi microsoft /proc/sys/kernel/osrelease || { echo 'HARNESS2_NOT_WSL2' >&2; exit 2; }
command -v git >/dev/null || { echo 'HARNESS2_GIT_MISSING' >&2; exit 2; }
command -v python3.12 >/dev/null || { echo 'HARNESS2_PYTHON312_MISSING' >&2; exit 2; }
python3.12 -c 'import sys; assert sys.version_info[:2] == (3, 12)' ||
    { echo 'HARNESS2_PYTHON312_INVALID' >&2; exit 2; }
printf 'HARNESS2_WSL2=READY\nPYTHON=3.12\n'
if command -v uv >/dev/null; then
    printf 'UV=PRESENT\n'
else
    printf 'UV=MISSING_FOR_SETUP\n'
fi
# WSL may inherit Windows npm from /mnt/c even if Linux Node.js is absent.
# Only report setup readiness for a runnable native Linux Node.js 20+ / npm pair.
node_path="$(command -v node 2>/dev/null || true)"
npm_path="$(command -v npm 2>/dev/null || true)"
node_ver="$(node --version 2>/dev/null || true)"
if [[ "$node_path" == /* && "$node_path" != /mnt/* &&
      "$npm_path" == /* && "$npm_path" != /mnt/* &&
      "$node_ver" =~ ^v(2[0-9]|[3-9][0-9])\.[0-9]+\.[0-9]+$ ]]; then
    printf 'NPM=PRESENT\n'
else
    printf 'NPM=MISSING_FOR_SETUP\n'
fi
printf 'MODEL_EXECUTION=DISABLED\n'
