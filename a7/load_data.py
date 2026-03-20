#!/usr/bin/env python3
'''
load_data.py

Pre-loads test keys into a running peer so that subsequent peers
have observable data to sync during testing.

Usage: python load_data.py <project_name> <peer_name> <num_files>

Example: python load_data.py myproject peerA 40

The peer must already be running and registered with the catalog
before you run this. Wait at least 5 seconds after starting the peer.
'''

import sys
import time
from HashTableClient import HashTableClient

if len(sys.argv) < 4:
    print("Usage: python load_data.py <project_name> <peer_name> <num_files>")
    sys.exit(1)

project = sys.argv[1]
peer    = sys.argv[2]
n       = int(sys.argv[3])

# The peer registers under "project-peername" in the catalog
full_name = f"{project}-{peer}"
print(f"Discovering '{full_name}' from catalog...")
client = HashTableClient.from_project_name(full_name)

print(f"Inserting {n} test keys into '{full_name}'...")
for i in range(n):
    key   = f"file_{i:03}"
    value = f"content of file {i:03}"
    client.insert(key, value)
    print(f"  [+] {key}")
    time.sleep(0.1)   # small delay so inserts are visible in peer logs

print(f"\nDone. {n} keys inserted into '{full_name}'.")
client.close()
