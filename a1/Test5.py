# Test5.py - insert item into python dict

import time

N = 35_000_000

d = {}

start = time.time()
for n in range(N):
    d[n] = "test"
end = time.time()

elapsed = end - start

print(f"Total time for {N:,} inserts into python dict: {elapsed:.4f} seconds")
print(f"Avg time: {elapsed / N * 1e9:.2f} ns")
