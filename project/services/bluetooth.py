import dbus
import time

def error_handler(func):
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"[error] Error occurred: {e}")
    return wrapper

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
    
    @error_handler
    def answer_call(self, path):
        call = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.VoiceCall')
        call.Answer()

    @error_handler
    def hangup_call(self, path):
        call = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.VoiceCall')
        call.Hangup()

    @error_handler
    def hangup_active_call(self):
        mgr = dbus.Interface(self.bus.get_object('org.ofono', self.target_modem_path), 'org.ofono.VoiceCallManager')
        calls = mgr.GetCalls()
        for path, props in calls:

            if props['State'] != "active":
                continue

            call = dbus.Interface(self.bus.get_object('org.ofono', path), 'org.ofono.VoiceCall')

            call.Hangup()
   
    @error_handler
    def set_speaker_volume(self, volume: int):

        if volume > 100 or volume < 10:
            raise Exception("[error] volume can only be set within 10..100")

        cv = dbus.Interface(self.bus.get_object('org.ofono', self.target_modem_path), 'org.ofono.CallVolume')
        cv.SetProperty("SpeakerVolume", dbus.Byte(volume))

    @error_handler
    def dial_number(self, number: str)->str:
        hide_callerid = "default" # 'default' 'enabled' 'disabled'

        vcm = dbus.Interface(self.bus.get_object('org.ofono', self.target_modem_path), 'org.ofono.VoiceCallManager')
        path = vcm.Dial(number, hide_callerid)

        return path

    @error_handler
    def listen_call_events(self, _callback):
        print("[info] listening call events for modem ( %s )" % (self.target_modem_path))
        mgr = dbus.Interface(self.bus.get_object('org.ofono', self.target_modem_path), 'org.ofono.VoiceCallManager')

        while True:
            try:
                calls = mgr.GetCalls()

                for path, props in calls:
                    for key in props.keys():
                        print("[info] %s : %s" % (key, props[key]))
                
                    _callback(path, props)
            
            except KeyboardInterrupt:
                print("[info] stopping listener for modem ( %s )" % (self.target_modem_path))
                break

            time.sleep(0.5)
