#!/bin/sh
# Linux: systemd user timer. macOS: per-user launchd agent.
# Schedules Toolkit reference checkout updates, NOT MCP executable updates.
set -eu
umask 077
kernel=$(uname -s)
case "$kernel" in Linux|Darwin) ;; *) echo 'ERROR: Windows uses Enable-ADT-AutoUpdate.ps1' >&2; exit 2;; esac
command -v python3 >/dev/null 2>&1 || { echo 'ERROR: Python 3.10+ is required' >&2; exit 2; }
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 2)' || { echo 'ERROR: Python 3.10+ is required' >&2; exit 2; }
package=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
root="${XDG_DATA_HOME:-$HOME/.local/share}/adt-personal"
source="$root/toolkit-source"
[ -f "$source/MANIFEST.json" ] || { echo 'ERROR: First install MCP with its dedicated Toolkit checkout.' >&2; exit 2; }
mkdir -p "$root/updater/state"
updater="$root/updater/update_toolkit.py"
if [ ! -f "$updater" ] || ! cmp -s "$package/updater/update_toolkit.py" "$updater"; then
  [ ! -e "$updater" ] || cp -p "$updater" "$updater.adt-backup-$(date '+%Y%m%d-%H%M%S')"
  cp "$package/updater/update_toolkit.py" "$updater"
fi
state="$root/updater/state"
# Run one visible check first. If the candidate is invalid, don't schedule it.
python3 "$updater" --source "$source" --state-dir "$state" --force
if [ "$kernel" = Linux ]; then
  command -v systemctl >/dev/null 2>&1 || { echo 'ERROR: systemd user manager is unavailable. Follow manual cron instructions.' >&2; exit 2; }
  unit="$HOME/.config/systemd/user"
  mkdir -p "$unit"
  python3 - "$unit" "$updater" "$source" "$state" <<'PY'
from pathlib import Path
import sys, shutil, datetime
base, script, source, state = map(Path, sys.argv[1:])
service = base / 'adt-personal-toolkit-update.service'
timer = base / 'adt-personal-toolkit-update.timer'
for item in (service, timer):
    if item.exists():
        backup = item.with_name(item.name + '.adt-backup-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
        shutil.copy2(item, backup)
def q(value):
    # systemd ExecStart argument quoting; ignore '%' expansion in inherited paths.
    value = str(value)
    if any(x in value for x in ('\n', '\r', '%', '"', '\\')):
        raise SystemExit('Unsupported special character in updater path')
    return '"' + value + '"'
service.write_text('[Unit]\nDescription=Check AI Development Toolkit source\n\n[Service]\nType=oneshot\nExecStart=' + ' '.join(q(x) for x in (Path(sys.executable), script, '--source', source, '--state-dir', state)) + '\n', encoding='utf-8')
timer.write_text('[Unit]\nDescription=Daily AI Development Toolkit source refresh\n\n[Timer]\nOnCalendar=*-*-* 10:35:00\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n', encoding='utf-8')
PY
  systemctl --user daemon-reload
  systemctl --user enable --now adt-personal-toolkit-update.timer
  systemctl --user list-timers adt-personal-toolkit-update.timer --no-pager
else
  # launchd cannot safely interpolate shell escaping; use plistlib argument arrays.
  agent="$HOME/Library/LaunchAgents/com.ai-development-toolkit.personal-updater.plist"
  mkdir -p "$(dirname "$agent")"
  python3 - "$agent" "$updater" "$source" "$state" <<'PY'
from pathlib import Path
import datetime, plistlib, shutil, sys
file, updater, source, state = map(Path, sys.argv[1:])
if file.exists():
    backup = file.with_name(file.name + '.adt-backup-' + datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    shutil.copy2(file, backup)
conf = {'Label': 'com.ai-development-toolkit.personal-updater',
        'ProgramArguments': [sys.executable, str(updater), '--source', str(source), '--state-dir', str(state)],
        'StartCalendarInterval': {'Hour': 10, 'Minute': 35},
        'RunAtLoad': True,
        'StandardOutPath': str(state.parent / 'launchd.out.log'),
        'StandardErrorPath': str(state.parent / 'launchd.err.log')}
file.write_bytes(plistlib.dumps(conf, sort_keys=True))
PY
  uid=$(id -u)
  launchctl bootout "gui/$uid" "$agent" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$uid" "$agent"
  launchctl print "gui/$uid/com.ai-development-toolkit.personal-updater" >/dev/null
  echo 'launchd agent installed. It runs at login and at 10:35 local time.'
fi
printf 'Status: python3 "%s" --source "%s" --state-dir "%s" --status\n' "$updater" "$source" "$state"
