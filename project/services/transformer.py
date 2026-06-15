import asyncio
import os
import pyaudio
from google import genai
from google.genai import types


class TransformerService:
    def __init__(self):
        self.INPUT_RATE = 16000
        self.OUTPUT_RATE = 24000
        self.CHUNK = 1024
        self.audio_queue = asyncio.Queue()
        self.pa = pyaudio.PyAudio()
        self.loop = None

    def mic_callback(self, in_data, frame_count, time_info, status):
        try:
            self.loop.call_soon_threadsafe(
                self.audio_queue.put_nowait, in_data
            )
        except Exception:
            pass
        return (None, pyaudio.paContinue)

    async def send_audio(self, session):
        while True:
            chunk = await self.audio_queue.get()

            await session.send_realtime_input(
                audio=types.Blob(
                    data=chunk,
                    mime_type="audio/pcm;rate=16000",
                )
            )

    async def receive_audio(self, session):
        speaker = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.OUTPUT_RATE,
            output=True,
        )

        try:
            while True:
                async for response in session.receive():

                    server_content = response.server_content

                    if not server_content:
                        continue

                    if server_content.input_transcription:
                        text = server_content.input_transcription.text
                        if text:
                            print(f"\n[transformer]: YOU: {text}")

                    if server_content.output_transcription:
                        text = server_content.output_transcription.text
                        if text:
                            print(f"\n[transfomer]: {text}")

                    if server_content.model_turn:
                        for part in server_content.model_turn.parts:
                            if part.inline_data:
                                speaker.write(part.inline_data.data)

                    if server_content.turn_complete:
                        print("\n--- turn complete ---")

                    if server_content.interrupted:
                        print("\n--- interrupted ---")
        finally:
            speaker.stop_stream()
            speaker.close()

    async def start(self):
        print("Transformer started")
        self.loop = asyncio.get_event_loop()

        client = genai.Client(
            api_key=os.environ["GOOGLE_API_KEY"]
        )

        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],

            input_audio_transcription=
                types.AudioTranscriptionConfig(),

            output_audio_transcription=
                types.AudioTranscriptionConfig(),

            realtime_input_config=
                types.RealtimeInputConfig(
                    turn_coverage="TURN_INCLUDES_ONLY_ACTIVITY"
                ),
        )

        async with client.aio.live.connect(
            model="gemini-3.1-flash-live-preview",
            config=config,
        ) as session:

            print("[info]: Connected")
            print("[info]: Talk normally")

            mic = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.INPUT_RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=self.mic_callback,
            )

            mic.start_stream()

            try:
                await asyncio.gather(
                    self.send_audio(session),
                    self.receive_audio(session),
                )
            finally:
                mic.stop_stream()
                mic.close()
                self.pa.terminate()