# Test1.py

import time

def trivial_function():
    return 42

N = 70_000_000

start = time.time()
for _ in range(N):
    trivial_function()
end = time.time()

elapsed = end - start

print(f"Total time for {N:,} trivial calls: {elapsed:.4f} seconds")
print(f"Avg time/call: {elapsed / N * 1e9:.2f} ns")
