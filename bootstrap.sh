#!/usr/bin/env bash
# Set up ai-reg-watch-bok on this Mac. Safe to re-run: each step skips what's already done.
#
#   ./bootstrap.sh                 full setup, including the daily 07:00 schedule
#   ./bootstrap.sh --no-schedule   everything except the schedule
#   ./bootstrap.sh --unschedule    remove the schedule only (e.g. before retiring this Mac)
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
LOCAL="$(dirname "$REPO")/$(basename "$REPO").local"
VAULT="${REGWATCH_VAULT:-$HOME/Documents/vaults/ai-audit-bok}"
VAULT_REPO="maxStephen/ai-audit-bok"
KEY_FILE="$LOCAL/secrets/anthropic_api_key"
LABEL="com.maxstephen.regwatch"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
HOUR=7
MINUTE=0

step() { printf '\n==> %s\n' "$*"; }
note() { printf '    %s\n' "$*"; }
warn() { printf '    WARNING: %s\n' "$*"; }

unschedule() {
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  if [ -f "$PLIST" ]; then
    mv "$PLIST" "$PLIST.disabled"
    note "Schedule removed (plist kept as $PLIST.disabled)"
  else
    note "No schedule installed"
  fi
}

SCHEDULE=1
case "${1:-}" in
  --no-schedule) SCHEDULE=0 ;;
  --unschedule) step "Removing daily schedule"; unschedule; exit 0 ;;
  "") ;;
  *) echo "Unknown option: $1" >&2; exit 2 ;;
esac

step "Homebrew packages"
command -v brew >/dev/null || { echo "Homebrew is required first; see MIGRATION.md step 1." >&2; exit 1; }
for pkg in python git gh terminal-notifier; do
  if brew list --formula "$pkg" >/dev/null 2>&1; then note "$pkg: installed"
  else note "$pkg: installing"; brew install --quiet "$pkg"; fi
done

step "Obsidian vault"
if [ -d "$VAULT/.git" ]; then
  note "Found $VAULT"
elif [ -e "$VAULT" ]; then
  warn "$VAULT exists but is not a git repository; notes will be written but not backed up"
elif gh auth status >/dev/null 2>&1; then
  note "Cloning $VAULT_REPO to $VAULT"
  mkdir -p "$(dirname "$VAULT")"
  gh repo clone "$VAULT_REPO" "$VAULT"
  note "Copy the local-only Reference/ files manually (see MIGRATION.md)"
else
  warn "Vault missing and gh is not logged in. Run 'gh auth login', then re-run this script."
fi

step "Python environment"
[ -x "$REPO/.venv/bin/python" ] || python3 -m venv "$REPO/.venv"
"$REPO/.venv/bin/pip" install --quiet --disable-pip-version-check -e "$REPO"
note "Installed regwatch into $REPO/.venv"

step "Local data folder (outside the repo)"
mkdir -p "$LOCAL/logs" "$LOCAL/state/snapshots" "$LOCAL/secrets"
chmod 700 "$LOCAL/secrets"
note "$LOCAL"

step "Anthropic API key"
if [ -s "$KEY_FILE" ]; then
  chmod 600 "$KEY_FILE"
  note "Present: $KEY_FILE"
else
  read -rs -p "    Paste API key (input hidden; Enter to skip): " key; echo
  if [ -n "$key" ]; then
    (umask 077; printf '%s' "$key" > "$KEY_FILE")
    note "Saved to $KEY_FILE (readable only by you)"
  else
    warn "Skipped. Summaries are disabled until $KEY_FILE exists."
  fi
  unset key
fi
note "Keep ~/Documents out of iCloud sync (System Settings > iCloud > iCloud Drive >"
note "Desktop & Documents Folders) so this key file stays on this Mac."

step "Time zone"
tz="$(readlink /etc/localtime | sed 's|.*/zoneinfo/||')"
if [ "$tz" = "America/New_York" ]; then
  note "$tz: the run is at $(printf '%02d:%02d' $HOUR $MINUTE) Eastern"
else
  warn "Mac time zone is $tz; the run happens at $(printf '%02d:%02d' $HOUR $MINUTE) in that zone, not Eastern"
fi

if [ "$SCHEDULE" = 1 ]; then
  step "Daily schedule (launchd)"
  mkdir -p "$(dirname "$PLIST")"
  cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$REPO/.venv/bin/regwatch</string>
    <string>run</string>
  </array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>$HOUR</integer><key>Minute</key><integer>$MINUTE</integer></dict>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    <key>REGWATCH_VAULT</key><string>$VAULT</string>
  </dict>
  <key>StandardOutPath</key><string>$LOCAL/logs/launchd.log</string>
  <key>StandardErrorPath</key><string>$LOCAL/logs/launchd.log</string>
</dict>
</plist>
EOF
  plutil -lint -s "$PLIST"
  launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST"
  note "Installed $PLIST: daily at $(printf '%02d:%02d' $HOUR $MINUTE); a run missed during sleep happens on wake"
else
  note "Schedule skipped (--no-schedule)"
fi

step "Smoke test (dry run: nothing saved, no notes, no notification)"
"$REPO/.venv/bin/regwatch" run --dry-run | tail -3

step "Done"
note "Run once now:      $REPO/.venv/bin/regwatch run"
note "Logs:              $LOCAL/logs/"
note "Remove schedule:   $REPO/bootstrap.sh --unschedule"
