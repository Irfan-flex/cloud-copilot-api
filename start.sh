#!/bin/bash
set -e

# === Start Write Session ===
osascript <<EOF
tell application "Terminal"
    do script "aws ssm start-session \
      --target i-i-021ade7cee6045df8 \
      --document-name AWS-StartPortForwardingSessionToRemoteHost \
      --parameters '{\"host\":[\"csaaurora-manual.cluster-cdycmm4aio24.us-east-1.rds.amazonaws.com\"],\"portNumber\":[\"5432\"],\"localPortNumber\":[\"5454\"]}'"
end tell
EOF

echo "[✔] Launched Terminal window for WRITE session (port 5454)"
