import time
import asyncio
import subprocess
from services.bluetooth import BluetoothService
from services.phonebook import PhonebookService
from services.audio import AudioService
from services.commandline import CommandLineService
from services.transformer import TransformerService

BL_MAC="EC:30:B3:2F:0E:FD"

audio_service = AudioService()
transformer_service = TransformerService()
bluetooth_service = BluetoothService(BL_MAC)
commandline_service = CommandLineService(BL_MAC)

async def listen_callback(callpath, props): 
    if props['State'] == "incoming":
        time.sleep(5)
        try:
            print(f"[info] answering the call")
            bluetooth_service.answer_call(callpath)
            
            commandline_service.remove_loopbacks()
            commandline_service.set_default()

            # await transformer_service.start()
            time.sleep(2)
            audio_service.play("leave_a_message")
            time.sleep(5)
            blt_service.hangup_active_call(callpath)
            

        except Exception as e:
            print("Exception occured: ", e)
            audio_service.play("leave_a_message")
            time.sleep(5)
            bluetooth_service.hangup_call(callpath)

asyncio.run(bluetooth_service.listen_call_events(listen_callback))

# blt_service.listen_call_events()
# blt_service.dial_number('+91842233')
# blt_service.set_speaker_volume(50)
# blt_service.hangup_active_call()
# phonebook = PhonebookService("../contacts.csv")
# phonebook.list_entries()
# num = phonebook.find_by_name("ram")[0]

# blt_service.dial_number(num)

#stt = STT()
#stt.listen()                       


# [info] Name : 
# [info] Multiparty : 0
# [info] RemoteHeld : 0
# [info] RemoteMultiparty : 0
# [info] Emergency : 0
# [info] State : incoming
# [info] LineIdentification : +91xxxxxxxx