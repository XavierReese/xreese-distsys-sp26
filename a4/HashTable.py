'''
HashTable.py

server-side hash table operations

Author: Xavier Reese
Date: 6 Feb 2026
'''

class HashTable:
    def __init__(self):
        self.table = {}

    # Insert
    def insert(self, k, v):
        if not isinstance(k, str):
            raise TypeError("key must be a string")

        self.table[k] = v

    # Lookup
    def lookup(self, k):
        return self.table.get(k, None)

    # Remove
    def remove(self, k):
        if k in self.table:
            del self.table[k]
            return True
        else:
            return False

    # Size
    def size(self):
        return len(self.table)

    # Query
    def query(self, k):
        return (k in self.table)
