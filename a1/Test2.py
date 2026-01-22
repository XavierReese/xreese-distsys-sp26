# Test2.py - create/delete file in home directory

import time
import os

file_path = os.path.join(os.path.expanduser("~"), "temp_test_file.txt")

def create_delete_function():
    with open(file_path, "w") as f:
        f.write("test")

    os.remove(file_path)

N = 90_000_000

start = time.time()
for _ in range(N):
    create_delete_function
end = time.time()

elapsed = end - start

print(f"Total time for {N:,} create/deletes in home directory: {elapsed:.4f} seconds")
print(f"Avg time: {elapsed / N * 1e9:.2f} ns")
