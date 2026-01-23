# Test9.py - scan over home dir and stat files

import time
import os

N = 18_000

home_dir = os.path.expanduser("~")

start = time.time()

for _ in range(N):
    for item in os.scandir(home_dir):
        try:
            stat = item.stat()
        except FileNotFoundError:
            pass

end = time.time()

elapsed = end - start

print(f"Total time for {N:,} home directory scan + stat: {elapsed:.4f} seconds")
print(f"Avg time: {elapsed / N * 1000:.2f} ms")
