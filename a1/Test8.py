# Test8.py - import and parse large json file

import time
import json

N = 10_000

start = time.time()

for _ in range(N):
    with open("./large.json") as f:
        data = json.load(f)

end = time.time()

elapsed = end - start

print(f"Total time for {N:,} json file opens + parses: {elapsed:.4f} seconds")
print(f"Avg time: {elapsed / N * 1000:.2f} ms")
