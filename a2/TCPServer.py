# TCPServer.py

import socket
import sys

port = int(sys.argv[1])

BUF = 4096

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((socket.gethostname(), port))

    s.listen(5)

    print(f"Server listening on {socket.gethostname()}:{port}")

    while True:
        client_socket, addr = s.accept()

        with client_socket:
            print(f"\nConnected at {addr}")

            total_recv = 0
            total_packets = 0

            while True:
                data = client_socket.recv(BUF)
                if not data:
                    break
                total_recv += len(data)
                total_packets += 1
                client_socket.send(b'OK')

            print(f"recv: {total_recv/(1024**2):.3f} MB in {total_packets} packets")
