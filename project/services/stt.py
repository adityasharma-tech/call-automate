from .microphone_stream import *

class STT:
    
    def __init__(self):
        self.client = speech.SpeechClient()
        self.config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=SAMPLE_RATE,
                language_code='en-US',
                max_alternatives=1,

        )

        self.streaming_config = speech.StreamingRecognitionConfig(
                config=self.config, interim_results=True
        )

    def listen(self):
        mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
        print(mic_manager.chunk_size)
        sys.stdout.write(YELLOW)
        sys.stdout.write('\nListening, say "Quit" or "Exit" to stop.\n\n')
        sys.stdout.write("End (ms)       Transcript Results/Status\n")
        sys.stdout.write("=====================================================\n")

        with mic_manager as stream:
            while not stream.closed:
                sys.stdout.write(YELLOW)
                sys.stdout.write(
                        "\n" + str(STREAMING_LIMIT * stream.restart_counter) + ": NEW REQUEST\n"
                )

                stream.audio_input = []
                audio_generator = stream.generator()

                requests = (
                    speech.StreamingRecognizeRequest(audio_context=content)
                    for content in audio_generator
                )

                responses = self.client.streaming_recognize(self.streaming_config, requests)

                listen_print_loop(responses, stream)

                if stream.result_end_time > 0:
                    stream.final_request_end_time = stream.is_final_end_time

                stream.result_end_time = 0
                stream.last_audio_input = []
                stream.last_audio_input = stream.audio_input
                stream.audio_input = []
                stream.restart_counter = stream.restart_counter + 1

                if not stream.last_transcript_was_final:
                    sys.stdout.write("\n")
                stream.new_stream = True
