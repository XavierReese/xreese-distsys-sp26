'''
HashTable.py

server-side hash table operations

Author: Xavier Reese
Date: 6 Feb 2026
'''

class HashTable:
    def __init__(self, max_size_bytes=1_000_000):
        self.table = {}
        self.max_size_bytes = max_size_bytes
        self.current_size_bytes = 0

    # Insert
    def insert(self, k, v):
        self.table{k: v}

    # Lookup
    def lookup(self, k):
        if self.table[k]:
            return self.table
        else:
            return None

    # Remove

    # Size

    # Query
