#!/usr/bin/env bash

TARGET_BLUETOOTH_MAC="EC:30:B3:2F:0E:FD"
CHECK_INTERVAL=1
export PYTHONPATH=/home/friday/.local/lib/python3.12/site-packages:$PYTHONPATH

PYTHON_CMD="/usr/bin/python3 src/server.py"
PYTHON_PID=""

export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

source /home/friday/.bashrc

is_connected() {
    bluetoothctl info "$TARGET_BLUETOOTH_MAC" 2>/dev/null | grep -q "Connected: yes"
}

is_python_running() {
    [[ -n "$PYTHON_PID" ]] && kill -0 "$PYTHON_PID" 2>/dev/null
}

echo "Monitoring Bluetooth device: $TARGET_BLUETOOTH_MAC"
env > /tmp/service.env
while true; do
    if is_connected; then
        if ! is_python_running; then
            echo "[INFO] Bluetooth connected. Starting main.py..."
            $PYTHON_CMD &
            PYTHON_PID=$!
            echo "[INFO] Started with PID $PYTHON_PID"
        fi
    else
        if is_python_running; then
            echo "[INFO] Bluetooth disconnected. Stopping main.py..."
            kill "$PYTHON_PID"
            wait "$PYTHON_PID" 2>/dev/null
            PYTHON_PID=""
        fi
    fi

    sleep "$CHECK_INTERVAL"
done
