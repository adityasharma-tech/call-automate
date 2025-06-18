import sounddevice as sd

# Load an audio file (must match the sink's format: 48000 Hz, 2 channels)
# filename = "audio.wav"
# data, fs = sf.read(filename)

# List output devices and find the one matching 'virtual-mic-sink'
for idx, device in enumerate(sd.query_devices()):
    print(idx, device)
    # if 'virtual-mic-sink' in device['name']:
    #     sink_index = idx
    #     break
else:
    raise RuntimeError("virtual-mic-sink not found in output devices")

# # Play to the virtual mic
# sd.play(data, samplerate=fs, device=sink_index)
# sd.wait()
