# Test6.py - open & close TCP

import time
import socket

N = 700

start = time.time()

for _ in range(N):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("example.com", 80))
    s.close()

end = time.time()

elapsed = end - start

print(f"Total time for {N:,} TCP opens/closes: {elapsed:.4f} seconds")
print(f"Avg time: {elapsed / N * 1000:.2f} ms")
