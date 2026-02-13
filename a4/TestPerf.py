#!/usr/bin/env python3
'''
TestPerf.py

test throughput of hashtable RPCs

Author: Xavier Reese
Date: 6 Feb 2026
'''

import os
import sys
import time
from HashTableClient import HashTableClient


DATA_DIR = "testdata"


# ---------- Helpers ----------

def get_file_list():
    files = sorted(os.listdir(DATA_DIR))
    return files


def full_path(filename):
    return os.path.join(DATA_DIR, filename)


def print_stage_header(name):
    print(f"\n{name}")
    print("-" * 40)


def measure(operation_name, func, items):

    print_stage_header(operation_name)

    start = time.perf_counter()

    for item in items:
        func(item)

    end = time.perf_counter()

    total_time = end - start
    count = len(items)

    throughput = count / total_time
    latency = total_time / count

    print(f"Operations:  {count}")
    print(f"Total time:  {total_time:.4f} sec")
    print(f"Throughput:  {throughput:.2f} ops/sec")
    print(f"Latency:     {latency*1000:.4f} ms/op")

    return throughput, latency


# ---------- Main ----------

def main():

    if len(sys.argv) != 3:
        print("Usage: python TestPerf.py <server_host> <server_port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])

    client = HashTableClient(host, port)

    client.connect()

    files = get_file_list()

    print(f"\nFound {len(files)} test files")
    print(f"Data directory: {DATA_DIR}")


    # ---------- Stage 1: INSERT ----------

    def insert_func(filename):
        key = filename
        path = full_path(filename)
        client.insert_file(key, path)

    measure("INSERT", insert_func, files)


    # ---------- Stage 2: LOOKUP ----------

    def lookup_func(filename):
        key = filename
        client.lookup(key)

    measure("LOOKUP", lookup_func, files)


    # ---------- Stage 3: QUERY ----------

    def query_func(filename):
        key = filename
        client.query(key)

    measure("QUERY", query_func, files)


    # ---------- Stage 4: REMOVE ----------

    def remove_func(filename):
        key = filename
        client.remove(key)

    measure("REMOVE", remove_func, files)


    print("\nPerformance test complete.")


if __name__ == "__main__":
    main()

