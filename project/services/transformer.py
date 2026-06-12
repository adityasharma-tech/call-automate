import asyncio
import os
import queue

import sounddevice as sd
from google import genai
from google.genai import types

class TransformerService:
    def __init__(self):
        self.INPUT_RATE = 16000
        self.OUTPUT_RATE = 24000
        self.audio_queue = asyncio.Queue()


    def mic_callback(self, indata, frames, time_info, status):
        if status:
            print(status)

        try:
            self.audio_queue.put_nowait(bytes(indata))
        except Exception:
            pass


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
        speaker = sd.RawOutputStream(
            samplerate=self.OUTPUT_RATE,
            channels=1,
            dtype="int16",
        )

        speaker.start()

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


    async def start(self):
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

            mic = sd.RawInputStream(
                samplerate=self.INPUT_RATE,
                blocksize=1024,
                channels=1,
                dtype="int16",
                callback=self.mic_callback,
            )

            mic.start()

            await asyncio.gather(
                self.send_audio(session),
                self.receive_audio(session),
            )