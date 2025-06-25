import bluetooth as blt

class BluetoothService:
    
    def __init__(self):
        server_sock = blt.BluetoothSocket(blt.RFCOMM)
        server_sock.bind(("", PORT_ANY))
        server_sock.listen(1)