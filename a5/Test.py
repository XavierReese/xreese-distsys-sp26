#!/usr/bin/env python3
'''
Test.py
'''
import os
import sys
from HashTableClient import HashTableClient
import json
import time

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test.py <project_name>")
        sys.exit(1)

    project_name = sys.argv[1]
    
    client = HashTableClient.from_project_name(project_name)

    print(f"--- Starting Tests for project: {project_name} ---")

    desc = client.get_description()
    
    if not desc:
        print("Failed to get description from server.")
        return

    files, peers = desc
    print(f"Server contains {len(files)} files.")
    print(f"Known peers: {peers}")

    if not os.path.exists("./downloads"):
        os.makedirs("./downloads")

    countdown = 10

    for filename in files:
        start_time = time.perf_counter()

        file_data = client.lookup(filename)

        end_time = time.perf_counter()
        duration = end_time - start_time
        print(f"Fetched {filename} in {duration:.4f}s")

        if file_data:
            countdown -= 1
            try:
                with open(f"./downloads/{filename}", "w") as f:
                    f.write(json.dumps(file_data))

            except Exception as e:
                print(f"Write Error")
        else:
            print(f"Failed (File {filename} not found on server).")

        if countdown == 0:
            print("\n\nKill & Restart Server Now (4 second delay)\n\n")
            time.sleep(4)

    print("--- Test Complete ---")

if __name__ == "__main__":
    main()
