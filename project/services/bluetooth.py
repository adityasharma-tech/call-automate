import dbus
import time

class BluetoothService:
    def __init__(self, address: str):
        self.bus = dbus.SystemBus()
        self.manager = dbus.Interface(self.bus.get_object('org.ofono', '/'), 'org.ofono.Manager')
        modems = self.manager.GetModems()

        self.target_modem_path = None

        for path, properties in modems:
            if properties[dbus.String('Serial')] == dbus.String(address):

                if "org.ofono.VoiceCallManager" not in properties["Interfaces"]:
                    print(f"[error] Failed to get org.ofono.VoiceCallManager for {properties['Name']}")
                    continue

                print(f"[info] Welcome {properties[dbus.String('Name')]} {properties[dbus.String('Serial')]}")
                self.target_modem_path = path
        if not self.target_modem_path:
            raise Exception("[error] No target modem found")
    
    def answer_call(self, path):
        call = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.VoiceCall')
        call.Answer()

    def hangup_call(self, path):
        call = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.VoiceCall')
        call.Hangup()

    def hangup_active_call(self):
        mgr = dbus.Interface(self.bus.get_object('org.ofono', self.target_modem_path), 'org.ofono.VoiceCallManager')
        calls = mgr.GetCalls()
        for path, props in calls:

            if props['State'] != "active":
                continue

            call = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.VoiceCall')

            call.Hangup()
   
    def set_speaker_volume(self, volume: int):

        if volume > 100 or volume < 10:
            raise Exception("[error] volume can only be set within 10..100")

        cv = dbus.Interface(self.bus.get_object('org.ofono', self.target_modem_path), 'org.ofono.CallVolume')
        cv.SetProperty("SpeakerVolume", dbus.Byte(volume))

    def dial_number(self, number: str)->str:
        hide_callerid = "default" # 'default' 'enabled' 'disabled'

        vcm = dbus.Interface(self.bus.get_object('org.ofono', self.target_modem_path), 'org.ofono.VoiceCallManager')
        path = vcm.Dial(number, hide_callerid)

        return path


    def listen_call_events(self):
        print("[info] listening call events for modem ( %s )" % (self.target_modem_path))
        mgr = dbus.Interface(self.bus.get_object('org.ofono', self.target_modem_path), 'org.ofono.VoiceCallManager')

        while True:
            try:
                calls = mgr.GetCalls()

                for path, props in calls:
                    for key in props.keys():
                        print("%s : %s" % (key, props[key]))
                
                    if props['State'] == "incoming":
                        self.answer_call(path)

                    if props['State'] == "active":
                        self.hangup_call(path)

                if len(calls) > 0:
                    break
            
            except KeyboardInterrupt:
                print("[info] stopping listener for modem ( %s )" % (self.target_modem_path))
                break

            time.sleep(0.5)
