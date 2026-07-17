#!/bin/bash
# ==============================================================================
# LimboOS Update Checker (cron-friendly)
# Checks for updates and optionally notifies the user
# Usage: bash update_checker.sh [--notify]
# ==============================================================================

VERSION_FILE="/etc/limboos/version.json"
GITHUB_API="https://api.github.com/repos/GlomGing85/LimboOS.Repo/releases/latest"
NOTIFY_FILE="/tmp/limboos_update_notify"

# Get current version
CURRENT="0.0.0"
if [ -f "$VERSION_FILE" ]; then
    CURRENT=$(python3 -c "import json; print(json.load(open('$VERSION_FILE'))['version'])" 2>/dev/null || echo "0.0.0")
fi

# Fetch latest from GitHub
LATEST=$(curl -s "$GITHUB_API" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('tag_name','v0.0.0').lstrip('v'))" 2>/dev/null || echo "0.0.0")

echo "LimboOS Update Check"
echo "  Current: $CURRENT"
echo "  Latest:  $LATEST"

if [ "$LATEST" != "0.0.0" ] && [ "$LATEST" != "$CURRENT" ]; then
    echo "  Status:  UPDATE AVAILABLE!"
    echo "  Run 'limboos-update --apply' to update."

    if [ "${1:-}" = "--notify" ]; then
        echo "UPDATE_AVAILABLE $CURRENT -> $LATEST" > "$NOTIFY_FILE"
        # Desktop can check this file on startup
    fi
else
    echo "  Status:  Up to date ✓"
    rm -f "$NOTIFY_FILE" 2>/dev/null
fi
