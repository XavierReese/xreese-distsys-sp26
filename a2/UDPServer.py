# UDPServer.py

import socket
import sys

port = int(sys.argv[1])

BUF = 4096

DATA_SIZE = 10 * 1024 * 1024

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    s.bind((socket.gethostname(), port))
    print(f"UDP server listening on {socket.gethostname()}:{port}")
    while True:
        total_recv = 0
        tot_packets = 0
        while total_recv < DATA_SIZE:
            data, addr = s.recvfrom(BUF)
            total_recv += len(data)
            tot_packets += 1
        s.sendto(b'OK', addr)
        print(f"recv: {total_recv/(1024**2):.2f} MB in {tot_packets} packets")

