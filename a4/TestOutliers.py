#!/usr/bin/env python3
'''
TestOutliers

Find latency outliers in hash table operations

Author: Xavier Reese
Date: 12 Feb 2026
'''
import time
import uuid
from HashTableClient import HashTableClient

def run_test(client, iterations=1000):
    stats = {
                #      min       max
        "insert": [float('inf'), 0.0],
        "remove": [float('inf'), 0.0]
    }

    print(f"Starting {iterations} iterations...")

    for i in range(iterations):
        key = f"key_{i}_{uuid.uuid4().hex[:8]}"
        val = f"val_{i}"

        # --- Time Insert ---
        start = time.perf_counter()
        client.insert(key, val)
        end = time.perf_counter()
        
        duration = end - start
        stats["insert"][0] = min(stats["insert"][0], duration)
        stats["insert"][1] = max(stats["insert"][1], duration)

        # --- Time Remove ---
        start = time.perf_counter()
        client.remove(key)
        end = time.perf_counter()

        duration = end - start
        stats["remove"][0] = min(stats["remove"][0], duration)
        stats["remove"][1] = max(stats["remove"][1], duration)

        if i % 100 == 0:
            print(f"Progress: {i}/{iterations}...")

    return stats

def print_results(stats):
    print("\n--- Latency Outliers (Seconds) ---")
    for op, times in stats.items():
        print(f"Operation: {op.upper()}")
        print(f"  Fastest: {times[0]:.6f}s")
        print(f"  Slowest: {times[1]:.6f}s")
        print(f"  Spread:  {times[1] / times[0]:.1f}x slower")
    print("----------------------------------")


def main(host, port):

    client = HashTableClient(host, port)

    client.connect()

    print_results(run_test(client))

    print("\nAll tests complete.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: TestOutliers.py hostname port")
        exit(0)
    host = sys.argv[1]
    port = int(sys.argv[2])
    main(host, port)
