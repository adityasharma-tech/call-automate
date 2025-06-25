import os
import time
import subprocess

# to make it advertisable
subprocess.run(['bluetoothctl'], input=b'discoverable on\nquit\n', check=True)

