> Connect device to bluetooth
```bash
# Command lines
bluetoothctl
scan on
pair <device_id>
connect <device_id>
trust <device_id>  # unless it will ask everytime from you to authorize it while your phone try to connect to it
```

> This service must running unless it will throw an error: `File not found`
```bash
sudo bluetoothd --nodetach --debug --compat
```

> Control volume though shell
```bash
# amixer is preinstalled
amixer set 'Master' 80%
```

> Check audio server (pulseaudio | pipewire or any other)
```bash
pactl info
```

> List of input devices
```bash
pactl list short sources
```

> Create virtual sink/source
```bash
pactl load-module module-null-sink sink_name=VirtualMic sink_properties=device.description=VirtualMic
```

> Set default output source
```bash
pactl set-default-sink VirtualMic
```

