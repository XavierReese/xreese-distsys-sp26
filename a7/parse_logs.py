#!/usr/bin/env python3
'''
parse_logs.py

After running your tests, this script reads all peer log files and
extracts every connection that occurred. It prints a summary you can
use to draw the connection diagram in your report.

Usage: python3 parse_logs.py <log_directory>

Example: python3 parse_logs.py logs_scale/
'''

import sys
import os
import re
from collections import defaultdict

if len(sys.argv) < 2:
    print("Usage: python3 parse_logs.py <log_directory>")
    sys.exit(1)

log_dir = sys.argv[1]
if not os.path.isdir(log_dir):
    print(f"Error: '{log_dir}' is not a directory.")
    sys.exit(1)

# connections[A][B] = number of times A fetched from B
connections = defaultdict(lambda: defaultdict(int))
# reverse_syncs[A][B] = number of times A reverse-synced to B
reverse_syncs = defaultdict(lambda: defaultdict(int))
# files_stored[peer] = total files stored
files_stored = defaultdict(int)

log_files = sorted(f for f in os.listdir(log_dir) if f.endswith(".log"))
if not log_files:
    print(f"No .log files found in '{log_dir}'.")
    sys.exit(1)

for log_file in log_files:
    # Derive peer name from filename: peerA.log -> peerA
    peer = log_file.replace(".log", "")
    path = os.path.join(log_dir, log_file)

    with open(path, "r") as f:
        for line in f:

            # Client-side fetch: "[peerB] Fetching 10/40 key(s) from 'proj-peerA'"
            m = re.search(r"\[(\w+)\] Fetching \d+/\d+ key\(s\) from '[\w-]+-(\w+)'", line)
            if m:
                src, dst = m.group(1), m.group(2)
                connections[src][dst] += 1

            # File stored: "[peerB] Stored 'file_003' from 'proj-peerA'"
            m = re.search(r"\[(\w+)\] Stored '.+' from '[\w-]+-(\w+)'", line)
            if m:
                files_stored[m.group(1)] += 1

            # Reverse sync (server-side): "[Server] Reverse syncing with <host>:<port>"
            # We can't get the peer name from this line alone — we use the log filename
            m = re.search(r"\[Server\] Reverse sync(?:ing)? with (.+):(\d+)", line)
            if m:
                reverse_syncs[peer][m.group(1) + ":" + m.group(2)] += 1

            # Reverse sync stored: "[Server] Reverse sync: stored 'file_003' from <host>:<port>"
            m = re.search(r"\[Server\] Reverse sync: stored '.+' from (.+):(\d+)", line)
            if m:
                files_stored[peer] += 1

# --- Print summary ---
print("=" * 52)
print(" CONNECTION SUMMARY")
print("=" * 52)

print("\nClient-side fetches (A downloaded from B):")
print(f"  {'FROM':<12} {'TO':<12} {'FETCH ROUNDS'}")
print(f"  {'-'*12} {'-'*12} {'-'*12}")
if connections:
    for src in sorted(connections):
        for dst in sorted(connections[src]):
            print(f"  {src:<12} {dst:<12} {connections[src][dst]}")
else:
    print("  (none found)")

print("\nServer-side reverse syncs (A reached back to B):")
if reverse_syncs:
    for peer in sorted(reverse_syncs):
        for target in sorted(reverse_syncs[peer]):
            print(f"  {peer} -> {target}  ({reverse_syncs[peer][target]} time(s))")
else:
    print("  (none found — check that reverse sync print statements match pattern)")

print("\nTotal files stored per peer:")
for peer in sorted(files_stored):
    print(f"  {peer:<12} {files_stored[peer]} file(s)")

print("\nUse the above to draw directed arrows in your report diagram.")
print("Each 'FROM -> TO' fetch round = one arrow in the diagram.")
