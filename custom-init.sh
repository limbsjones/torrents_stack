#!/usr/bin/with-contenv bash
# Custom init: Start socat proxy for Deluge daemon port
# This runs before deluged starts (init-custom-files phase)

SOCAT_BIN="/usr/bin/socat"

# Install socat if missing
if ! command -v socat &>/dev/null; then
    echo "[custom-init] Installing socat..."
    apk add --quiet socat 2>&1
fi

# Kill existing socat on our port if any
pkill -f "socat.*TCP-LISTEN:48846" 2>/dev/null || true

# Start socat proxy: 0.0.0.0:48846 -> 127.0.0.1:58846
# This runs in background (not blocking init)
socat TCP-LISTEN:48846,reuseaddr,fork TCP:127.0.0.1:58846 &
SOCAT_PID=$!
echo "[custom-init] socat started (PID: $SOCAT_PID) on 0.0.0.0:48846 -> 127.0.0.1:58846"
