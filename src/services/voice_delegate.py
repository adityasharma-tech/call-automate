import os
import asyncio
import pyaudio
from google import genai
from .events import events
from google.genai import types


class VoiceDelegateService:
    def __init__(self, bus):
        self.INPUT_RATE = 16000
        self.OUTPUT_RATE = 24000
        self.CHUNK = 1024
        self.audio_queue = asyncio.Queue()
        self.pa = pyaudio.PyAudio()
        self.loop = None
        
        self.mic = None
        self.speaker = None
        self.session = None
        self.send_task = None
        self.recv_task = None

        bus.on(
            events["start_vds"],
            self.start
        )
        bus.on(events["stop_vds"], self.stop)
        bus.on(events["disconnected"], self.stop)

    async def stop(self):
        if self.mic:
            try:
                self.mic.stop_stream()
                self.mic.close()
            except:
                pass
            self.mic = None

        if self.speaker:
            try:
                self.speaker.stop_stream()
                self.speaker.close()
            except:
                pass
            self.speaker = None

        if self.send_task:
            self.send_task.cancel()

        if self.recv_task:
            self.recv_task.cancel()
            
        if self.session:
            asyncio.run_coroutine_threadsafe(
                self.session.close(),
                self.loop
            )
            self.session = None

    def mic_callback(self, in_data, frame_count, time_info, status):
        try:
            self.loop.call_soon_threadsafe(
                self.audio_queue.put_nowait, in_data
            )
        except Exception:
            pass
        return (None, pyaudio.paContinue)

    async def send_audio(self, session):
        try:
            while True:
                chunk = await self.audio_queue.get()

                await session.send_realtime_input(
                    audio=types.Blob(
                        data=chunk,
                        mime_type="audio/pcm;rate=16000",
                    )
                )
        except asyncio.CancelledError:
            pass

    async def receive_audio(self, session):
        self.speaker = self.pa.open(
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
                                self.speaker.write(part.inline_data.data)

                    if server_content.turn_complete:
                        print("\n--- turn complete ---")

                    if server_content.interrupted:
                        print("\n--- interrupted ---")
        except asyncio.CancelledError:
            pass
        finally:
            self.speaker.stop_stream()
            self.speaker.close()

    async def start(self):
        if self.session:
            print("[warn]: Voice Service already running!")
            return
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
            self.session = session

            print("[info]: Connected")
            print("[info]: Talk normally")

            self.mic = self.pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.INPUT_RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
                stream_callback=self.mic_callback,
            )

            self.mic.start_stream()
            self.send_task = asyncio.create_task(
                self.send_audio(session)
            )
            self.recv_task = asyncio.create_task(
                self.receive_audio(session)
            )

            try:
                await asyncio.gather(
                    self.send_task,
                    self.recv_task,
                )
            except asyncio.CancelledError:
                pass
            finally:
                if self.mic:
                    try:
                        self.mic.stop_stream()
                        self.mic.close()
                    except:
                        pass
                    self.mic = None