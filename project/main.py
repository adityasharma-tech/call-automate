from services.bluetooth import BluetoothService
from services.phonebook import PhonebookService

# blt_service = BluetoothService("EC:30:B3:2F:0E:FD")
# blt_service.listen_call_events()
# blt_service.dial_number('+91xxxxxxxxx')
# blt_service.set_speaker_volume(50)
# blt_service.hangup_active_call()
phonebook = PhonebookService("../contacts.csv")
# phonebook.list_entries()
# print(phonebook.find_by_name("rintu"))
