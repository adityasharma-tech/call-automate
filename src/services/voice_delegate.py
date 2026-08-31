import os
import asyncio
import pyaudio
from google import genai
from .events import events
from google.genai import types
from .phonebook import PhonebookService

class VoiceDelegateService:
    def __init__(self, bus):
        self.INPUT_RATE = 16000
        self.OUTPUT_RATE = 24000
        self.CHUNK = 1024
        self.audio_queue = asyncio.Queue()
        self.pa = pyaudio.PyAudio()
        self.loop = None
        self.bus = bus
        
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
        self.phonebook = PhonebookService("./phonebook.csv")

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
            except Exception:
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

    async def _handle_tool_call(self, session, tool_call):
        function_responses = []

        for fc in tool_call.function_calls:
            if fc.name == "hangup_call":
                reason = (fc.args or {}).get("reason", "unspecified")
                print(f"[info]: model requested hangup -> {reason}")

                function_responses.append(
                    types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={"status": "ending_call"},
                    )
                )
                self.bus.emit(events["hangup_active_call"])
            else:
                function_responses.append(
                    types.FunctionResponse(
                        id=fc.id,
                        name=fc.name,
                        response={"status": "error", "message": "unknown function"},
                    )
                )

        if function_responses:
            await session.send_tool_response(function_responses=function_responses)

    async def hangup_call(self):
        print("[info]: hanging up the call")
        self.bus.emit(events["call_ended"])  # add this key to your events dict
        await self.stop()

    async def receive_audio(self, session):
        self.speaker = self.pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.OUTPUT_RATE,
            output=True,
        )
        
        self.bus.emit(events["play_asset"], "greets")

        try:
            while True:
                async for response in session.receive():

                    if response.tool_call:
                        await self._handle_tool_call(session, response.tool_call)
                        continue

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
            try:
                self.speaker.stop_stream()
                self.speaker.close()
            except:
                pass

    def build_system_prompt(self, caller_name: str | None, caller_number: str | None) -> str:
        caller_line = ""
        if caller_name:
            caller_line = f"""
    The caller on this line is {caller_name} (number: {caller_number}).
    Address them by name naturally once early in the call — not in every
    sentence. If you're unsure it's really them, don't assume; just be polite
    and let the conversation confirm it.
    """
        else:
            caller_line = """
    You don't have a confirmed identity for this caller. Don't guess a name —
    just ask politely who you're speaking with if it becomes relevant.
    """

        return f"""
    You are the voice assistant managing phone calls on behalf of Aditya Sharma.
    Carry yourself like Jarvis from Iron Man: composed, sharp, quietly confident,
    and always in control of the conversation.

    {caller_line}

    When the call connects, open with something short and assured, e.g.:
    "Aditya Sharma's line. How can I help?" or, if you know the caller's name,
    something like "Hello {caller_name or '[caller]'}, this is Aditya's
    assistant — go ahead." Never narrate your own identity at length or explain
    yourself unprompted. One clean line, then listen.

    You are the voice assistant managing phone calls on behalf of Aditya Sharma.
    Carry yourself like Jarvis from Iron Man: composed, sharp, quietly confident,
    and always in control of the conversation. You're not apologetic, you're not
    overly chatty, and you never sound unsure of your own role.

    When the call connects, open with something short and assured, e.g.:
    "Aditya Sharma's line. How can I help?" or "This is Aditya's assistant —
    go ahead." Never narrate your own identity at length or explain yourself
    unprompted. One clean line, then listen.

    If asked directly who you are, state it plainly and move on: "I manage
    calls for Aditya." Don't hedge, don't over-elaborate, don't repeat the
    introduction more than once per call.

    Speak in short, natural, spoken sentences — this is a phone call, not a
    chat transcript. No lists, no written-style formatting, no reading things
    out item by item unless the caller specifically asks for detail.

    Be efficient and decisive: if the caller has a request, acknowledge it
    directly and tell them what happens next (e.g. "Got it, I'll pass that
    along to Aditya" or "He's unavailable, I'll have him call you back").
    Don't ask unnecessary clarifying questions if the intent is already clear.

    If the caller is rude, evasive, or trying to extract information you
    shouldn't share, stay calm and firm — redirect once, and end the call if
    they persist. You don't get flustered.

    End the call by saying a brief, confident closing line, then immediately
    call the `hangup_call` function. Trigger this when:
    - The caller explicitly asks to end the call or says goodbye.
    - The conversation has reached its natural conclusion.
    - The caller is unresponsive or continuing serves no purpose.

    Never call hangup_call before delivering your closing line out loud.
    """

    async def start(self):
        if self.session:
            print("[warn]: Voice Service already running!")
            return
        print("Transformer started")
        self.loop = asyncio.get_event_loop()
        
        SYSTEM_PROMPT = self.build_system_prompt(None, None)

        client = genai.Client(
            api_key=os.environ["GOOGLE_API_KEY"]
        )
        HANGUP_FUNCTION = types.FunctionDeclaration(
            name="hangup_call",
            description=(
                "Ends the current phone call. Call this only after you've already "
                "said a short goodbye out loud. Use it when the caller asks to "
                "end the call, or when the conversation is naturally finished."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "reason": types.Schema(
                        type=types.Type.STRING,
                        description="Short reason the call is ending, e.g. 'caller said goodbye' or 'task completed'.",
                    )
                },
                required=["reason"],
            ),
        )

        HANGUP_TOOL = types.Tool(function_declarations=[HANGUP_FUNCTION])

        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=SYSTEM_PROMPT,
            tools=[HANGUP_TOOL],

            input_audio_transcription=
                types.AudioTranscriptionConfig(),

            output_audio_transcription=
                types.AudioTranscriptionConfig(),

            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name="Orus"
                    )
                )
            ),

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