import time
import subprocess
from services.bluetooth import BluetoothService
from services.phonebook import PhonebookService
from services.stt import STT
from services.audio import AudioService

audio_service = AudioService()
bluetooth_service = BluetoothService("EC:30:B3:2F:0E:FD")

def listen_callback(callpath, props): 
    if props['State'] == "incoming":
        time.sleep(2)
        print(f"[info] answering the call")
        bluetooth_service.answer_call(callpath)
        audio_service.play("leave_a_message")

        bluetooth_service.hangup_call(callpath)

bluetooth_service.listen_call_events(listen_callback)










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
