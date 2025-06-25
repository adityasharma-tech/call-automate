#!/bin/bash

cd ../project || exit 1

sudo systemctl stop bluetooth
sudo nohup bluetoothd --nodetach --debug --compat 2>&1 &

echo "Waiting for bluetoothd to initialize..."

sleep 1

bluetoothctl << EOF
power on
agent on
default-agent
discoverable on
quit
EOF

sleep 1

sudo python3 main.py