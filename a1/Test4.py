# Test4.py - get wall clock time

import time

N = 5_500_000

start = time.time()
for _ in range(N):
    wall_time = time.ctime()
end = time.time()

elapsed = end - start

print(f"Total time for {N:,} times getting wall clock time: {elapsed:.4f} seconds")
print(f"Avg time: {elapsed / N * 1e9:.2f} ns")
