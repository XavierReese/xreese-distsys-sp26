# Test9.py - scan over home dir and stat files

import time
import subprocess, os

N = 3_000

home_dir = os.path.expanduser("~")

start = time.time()

for _ in range(N):
    ls = subprocess.run(["ls", "-l", home_dir], capture_output=True)

end = time.time()

elapsed = end - start

print(f"Total time for {N:,} home directory scan + stat: {elapsed:.4f} seconds")
print(f"Avg time: {elapsed / N * 1000:.2f} ms")
