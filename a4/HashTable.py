'''
HashTable.py

server-side hash table operations

Author: Xavier Reese
Date: 6 Feb 2026
'''
import json
import os
import uuid

class HashTable:
    def __init__(self):
        self.table = {}

    #####################
    ## Disk Functions

    def _save_to_disk(self, filename: str, data):
        filename = "./data/" + filename
        temp_file = f"{filename}.tmp"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f)

            os.replace(temp_file, filename)
            return True
        
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            print(f"Write Error: {e}")
            return False

    def _load_from_disk(self, filename: str):
        filename = "./data/" + filename
        if not os.path.exists(filename):
            return None

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Read error: {e}")
            return None

    def _delete_from_disk(self, filename: str):
        filename = "./data/" + filename
        try:
            os.remove(filename)
            return True
        except Exception as e:
            print(f"Remove error: {e}")
            return False

    #####################

    # Insert
    def insert(self, k, v):
        if not isinstance(k, str):
            raise TypeError("key must be a string")

        filename = f"{uuid.uuid4()}.json"
        if self._save_to_disk(filename, v):
            self.table[k] = filename
        else:
            raise Exception("Failed saving to disk")

    # Lookup
    def lookup(self, k):
        filename = self.table.get(k, None)
        if filename == None:
            return None

        return self._load_from_disk(filename)

    # Remove
    def remove(self, k):
        if k in self.table:
            filename = self.table.get(k)
            if filename is not None and self._delete_from_disk(filename) is not False:
                del self.table[k]
                return True

        return False

    # Size
    def size(self):
        return len(self.table)

    # Query
    def query(self, k):
        return (k in self.table)
