#!/bin/bash
# ==============================================================================
# LimboOS Auto-start Script
# Launches the custom desktop environment from init / login
# ==============================================================================

export DISPLAY=:0
export HOME="${HOME:-/home/user}"
export PATH="/usr/bin:/bin:/usr/local/bin:/opt/limboos/bin:$PATH"
export XDG_RUNTIME_DIR="/tmp/limboos-runtime"

mkdir -p "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"

echo "=== LimboOS Auto-start ==="
echo "Starting X11 display server..."

# Try to start Xorg or Xvfb
if command -v Xorg &>/dev/null; then
    Xorg :0 -nolisten tcp &
    X_PID=$!
    sleep 2
elif command -v Xvfb &>/dev/null; then
    Xvfb :0 -screen 0 1024x768x24 &
    X_PID=$!
    sleep 1
else
    echo "No X server found. Starting desktop in framebuffer mode..."
fi

# Launch the LimboOS desktop
echo "Starting LimboOS Desktop Environment..."
exec python3 /usr/lib/limboos/limboos_desktop.py

# Cleanup on exit
if [[ -n "${X_PID:-}" ]]; then
    kill "$X_PID" 2>/dev/null
fi
