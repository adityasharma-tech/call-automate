from time import sleep
from bluetooth import advertise_service, BluetoothSocket, \
    RFCOMM, PORT_ANY, SERIAL_PORT_CLASS, SERIAL_PORT_PROFILE, OBEX_UUID


class BluetoothService:
    
    def __init__(self):
        self.client_info = None
        self.client_sock = None
        self.server_sock = None
        self.port = None

        self.uuid = "94f39d29-7d6d-437d-973b-fba39e49d4ee"

    def initialize(self):
        self.server_sock = BluetoothSocket(RFCOMM)
        self.server_sock.bind(("", PORT_ANY))
        self.server_sock.listen(1)

        self.port = self.server_sock.getsockname()[1]


    def start_service(self):
        advertise_service(
            self.server_sock,
            "Jarvis",
            service_id=self.uuid,
            service_classes=[ self.uuid, SERIAL_PORT_CLASS ],
            profiles=[ SERIAL_PORT_PROFILE ],
            # protocols=[ OBEX_UUID ]
        )

        print("Waiting for connection on RFCOMM channel %d" % self.port)
        self.client_sock, self.client_info = self.server_sock.accept()
        print("Accepted connection from ", self.client_info)

    def run(self):
        while True:
            try:
                self.start_service()

                while True:
                    request = self.client_sock.recv(1024)
                    if len(request) == 0:
                        continue

                    data = "{\"event\":\"call.accept\",\"payload\":{}}"

                    if data:
                        print("sending [%s]" % data)
                        self.client_sock.send(data)

            except IOError as e:
                print("IOError:", e)
                if self.client_sock:
                    self.client_sock.close()
                    self.client_sock = None
                if self.server_sock:
                    self.server_sock.close()

                sleep(0.5)

                self.initialize()
                continue

            except KeyboardInterrupt:
                print("disconnecting")
                if self.client_sock:
                    self.client_sock.close()
                if self.server_sock:
                    self.server_sock.close()
                break