# UDPClient.py

import socket
import os
import sys
import time

hostname = sys.argv[1]
port = int(sys.argv[2])

BYTES = 10 * 1024 * 1024

for i in [1]:
    BUF = 2**i
    data = os.urandom(BYTES)

    start = time.time()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect((hostname, port))

        total_sent = 0
        total_packets = 0
        while total_sent < BYTES:
            chunk = data[total_sent : total_sent + BUF]
            total_sent += s.sendto(chunk, (hostname, port))
            total_packets += 1
        ok, _ = s.recvfrom(BUF)

    tot_time = time.time() - start
    print(f"Method: UDP bufsize: {(2**i):>4} packets: {total_packets:7} time: {tot_time:10.4f} seconds")
