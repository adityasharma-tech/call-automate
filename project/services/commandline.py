import subprocess

class CommandLineService:
    def __init__(self, bl_mac: str):
        print("[info] Class.CommandLineService Initialized")
        self.bl_mac = bl_mac.replace(':', '_')

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
                f"[output]: CommandLineService.remove_loopbacks<0> "
                f"unloaded={unloaded}"
            )

        except subprocess.CalledProcessError as e:
            print(
                f"[output]: CommandLineService.remove_loopbacks<{e.returncode}> "
                f"{e.stderr}"
            )
    def set_default(self):

        print(f"[info]: \"bluez_sink.{self.bl_mac}.handsfree_audio_gateway\"")
        print(f"[info]: \"bluez_source.{self.bl_mac}.handsfree_audio_gateway\"")
        res = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True)
        print(f"[output]: CommandLineService.list.sinks<{res.returncode}> ", res.stdout, res.stderr)
        
        sink_result = subprocess.run(["pactl", "set-default-sink", f"bluez_sink.{self.bl_mac}.handsfree_audio_gateway"], capture_output=True, text=True)
        source_result = subprocess.run(["pactl", "set-default-source", f"bluez_source.{self.bl_mac}.handsfree_audio_gateway"], capture_output=True, text=True)

        print(f"[output]: CommandLineService.set_default.sink_result<{sink_result.returncode}> ", sink_result.stdout, sink_result.stderr)
        print(f"[output]: CommandLineService.set_default.source_result<{source_result.returncode}> ", source_result.stdout, source_result.stderr)


if __name__ == "__main__":
    commandline_service = CommandLineService("EC:30:B3:2F:0E:FD")
    commandline_service.set_default()