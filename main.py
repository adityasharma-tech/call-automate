import bluetooth

server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
port = 5


try:
    server_sock.bind(("", port))
    server_sock.listen(1)

    print(f"[*] Listening for RFCOMM connection on port {port}...")

    client_sock, client_info = server_sock.accept()
    print(f"[+] Connection accepted from {client_info}")

    while True:
        data = client_sock.recv(1024)
        if not data:
            break
        print(f"[AT COMMAND] {data.decode('utf-8', errors='ignore').strip()}")

except Exception as e:
    print(f"[!] Error: {e}")

finally:
    client_sock.close()
    server_sock.close()
    print("[*] Sockets closed.")