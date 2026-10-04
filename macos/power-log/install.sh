#!/bin/bash
# Runs power-log every 5 minutes through a LaunchAgent. Re-running updates it.
#   ./install.sh              install or update
#   ./install.sh --uninstall  remove the LaunchAgent and the log
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd -P)"
label=toybox.power-log
plist="$HOME/Library/LaunchAgents/$label.plist"
domain="gui/$(id -u)"

launchctl bootout "$domain/$label" 2>/dev/null || true
if [ "${1:-}" = "--uninstall" ]; then
  rm -f "$plist" "$HOME/Library/Logs/power-log.log"
  echo "Removed power-log."
  exit 0
fi

chmod +x "$here/power-log"
mkdir -p "$(dirname "$plist")"
cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>            <string>$label</string>
    <key>ProgramArguments</key> <array><string>$here/power-log</string></array>
    <key>StartInterval</key>    <integer>300</integer>
    <key>RunAtLoad</key>        <true/>
    <key>ProcessType</key>      <string>Background</string>
</dict>
</plist>
EOF
launchctl bootstrap "$domain" "$plist"
echo "power-log runs every 5 minutes; read ~/Library/Logs/power-log.log"
