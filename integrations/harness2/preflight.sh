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
if command -v npm >/dev/null; then
    printf 'NPM=PRESENT\n'
else
    printf 'NPM=MISSING_FOR_SETUP\n'
fi
printf 'MODEL_EXECUTION=DISABLED\n'
