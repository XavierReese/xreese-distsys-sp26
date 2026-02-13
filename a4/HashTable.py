'''
HashTable.py

server-side hash table operations

Author: Xavier Reese
Date: 6 Feb 2026
'''
import json
import os
import uuid
from datetime import datetime

class HashTable:
    def __init__(self):
        self.table = {}
        self.log_length = 0

        if not self._startup():
            raise Exception("Failed on startup")

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
    ## Checkpoint & Log

    def _log(self, m, k=None, v=None, details=None):
        try:
            with open("table.txn", "a", encoding='utf-8') as f:
                log_line = f"{datetime.now()}::{m}::{v}::{details}::{k}\n"
                f.write(log_line)

                self.log_length += 1
                if self.log_length >= 100:              # compact after 100 logs
                    self._compact_log()
            return True

        except Exception as e:
            print(f"Log Error: {e}")
            raise Exception(e)

    def _compact_log(self):
        filename = "table.ckpt"
        tmp = f"{filename}.tmp"
        try:
            with open(tmp, "w", encoding='utf-8') as f:
                for k, v in self.table.items():
                    f.write(f"{v}::{k}\n")        # key & value stored in reverse because key is user controlled

            os.replace(tmp, filename)
            os.remove("table.txn")
            self.log_length = 0
            return True
        except Exception as e:
            if os.path.exists(tmp):
                os.remove(tmp)
            print(f"Compact Log Error: {e}")
            return False

    # TODO flush and sync all over

    def _startup(self):
        # read ckpt and add to hash table
        try:
            with open("table.ckpt", "r", encoding='utf-8') as f:
                for line in f:
                    data = line.strip().split("::")
                    self.table[data[1]] = data[0]
        except FileNotFoundError:
            print("No Checkpoint File Found")
        except Exception as e:
            print(f"Recover Checkpoint Error: {e}")
            return False

        # go through line by line and do the log actions. Remove from log as I go?
        try:
            with open("table.txn", "r", encoding='utf-8') as f:
                for line in f:
                    data = line.strip().split("::")
                    if data[1] == "insert":
                        self.table[data[4]] = data[2]
                    elif data[1] == "remove":
                        del self.table[data[4]]
                    self.log_length += 1

        except FileNotFoundError:
            print("No Log File Found")

        except Exception as e:
            print(f"Recover Log Error: {e}")
            return False

        # check that each value in the table references a real file
        for filename in self.table.values():
            if not os.path.isfile("./data/" + filename):
                print(f"File {filename} does not exist")
                return False

        return True

    #####################

    # Insert
    def insert(self, k, v):
        if not isinstance(k, str):
            raise TypeError("key must be a string")

        k.replace("\n", "")

        filename = f"{uuid.uuid4()}.json"
        if self._save_to_disk(filename, v):
            self.table[k] = filename
            self._log("insert", k, filename)
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
                previous = self.table[k]
                del self.table[k]
                self._log("remove", k, None, f"previous_value={previous}")
                return True

        return False

    # Size
    def size(self):
        return len(self.table)

    # Query
    def query(self, k):
        return (k in self.table)
