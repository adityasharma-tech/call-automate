import subprocess
from .events import events

class AudioRoutingService:
    def __init__(self, bus, mac_addr: str):
        print("[info] Class.AudioRoutingService Initialized")
        self.mac_addr = mac_addr.replace(':', '_')
        self.bus = bus
        self.bus.on(events["remove_loopbacks"], lambda: self.remove_loopbacks())
        self.bus.on(events["set_audio_defaults"], lambda: self.set_defaults())

    def remove_loopbacks(self):
        try:
            result = subprocess.run(
                ["pactl", "list", "short", "modules"],
                capture_output=True,
                text=True,
                check=True,
            )

            unloaded = []

            for line in result.stdout.splitlines():
                cols = line.split()

                if len(cols) >= 2 and cols[1] == "module-loopback":
                    module_id = cols[0]

                    subprocess.run(
                        ["pactl", "unload-module", module_id],
                        check=True,
                    )

                    unloaded.append(module_id)

            print(
                f"[output]: AudioRoutingService.remove_loopbacks<0> "
                f"unloaded={unloaded}"
            )

        except subprocess.CalledProcessError as e:
            print(
                f"[output]: AudioRoutingService.remove_loopbacks<{e.returncode}> "
                f"{e.stderr}"
            )
    def set_defaults(self):

        print(f"[info]: \"bluez_sink.{self.mac_addr}.handsfree_audio_gateway\"")
        print(f"[info]: \"bluez_source.{self.mac_addr}.handsfree_audio_gateway\"")
        res = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True)
        print(f"[output]: AudioRoutingService.list.sinks<{res.returncode}> ", res.stdout, res.stderr)
        
        sink_result = subprocess.run(["pactl", "set-default-sink", f"bluez_sink.{self.mac_addr}.handsfree_audio_gateway"], capture_output=True, text=True)
        source_result = subprocess.run(["pactl", "set-default-source", f"bluez_source.{self.mac_addr}.handsfree_audio_gateway"], capture_output=True, text=True)

        print(f"[output]: AudioRoutingService.set_default.sink_result<{sink_result.returncode}> ", sink_result.stdout, sink_result.stderr)
        print(f"[output]: AudioRoutingService.set_default.source_result<{source_result.returncode}> ", source_result.stdout, source_result.stderr)


if __name__ == "__main__":
    audio_router = AudioRoutingService("EC:30:B3:2F:0E:FD")
    audio_router.remove_loopbacks()