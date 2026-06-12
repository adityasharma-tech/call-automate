import os
import random
import subprocess

class AudioService:
    
    def __init__(self, pulse_sink='1'):
        # self.pulse_sink = pulse_sink
        self._env = os.environ.copy()
        # self._env["PULSE_SINK"] = self.pulse_sink

    def play(self, audio_type="greets"): # goodbye | leave_a_message | greets
        match audio_type:
            case "goodbye":
                result = self.make("goodbye")

            case "greets":
                self.make("greets")
            

            case "leave_a_message":
                self.make("leave_a_message")
                
    def make(self, path: str):
        dir_path = os.path.join(os.getcwd(), f"assets/audio_collections", path)        
        random_audio = random.choice(os.listdir(dir_path))
        full_path = os.path.join(dir_path, random_audio)

        wav_path = full_path.replace(".mp3", ".wav")

        print(f"AudioService.make({path}) ", wav_path)


        if not os.path.exists(wav_path):
            subprocess.run(
                [
                    'ffmpeg', '-y',
                    '-i', full_path,
                    '-ar', '8000',
                    '-ac', '1',
                    '-acodec', 'pcm_u8',
                    wav_path
                ],
                check=True
                    )

        try:
            result = subprocess.run(
                ['aplay', wav_path],
                capture_output=True,
                text=True,
                check=True,
                env=self._env
            )

            print("stdout:", result.stdout)
            print("stderr:", result.stderr)

            return result

        except subprocess.CalledProcessError as e:
            print("Return code:", e.returncode)
            print("stdout:", e.stdout)
            print("stderr:", e.stderr)
            print("XDG_RUNTIME_DIR =", os.environ.get("XDG_RUNTIME_DIR"))
            print("PULSE_SERVER    =", os.environ.get("PULSE_SERVER"))
            print("PULSE_SINK      =", os.environ.get("PULSE_SINK"))
            