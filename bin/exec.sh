#!/usr/bin/bash

TARGET_BLUETOOTH_MAC="EC:30:B3:2F:0E:FD"

CHECK_INTERVAL=1

is_connected() {
	bluetoothctl info "$TARGET_BLUETOOTH_MAC" | grep -q "Connected: yes"
}

echo "Waiting for Bluetooth device $TARGET_BLUETOOTH_MAC to connect!"

while true; do
	if is_connected; then
		echo "[info] device $TARGET_BLUETOOTH_MAC is now connected."
		break
	else
		echo "[info] not connected. Checking again in $CHECK_INTERVAL seconds..."
		sleep "$CHECK_INTERVAL"
	fi
done

python3 project/main.py
