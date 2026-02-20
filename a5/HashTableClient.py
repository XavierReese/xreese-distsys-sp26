'''
HashTableClient.py

client-side RPC operations

Author: Xavier Reese
Date: 6 Feb 2026
'''
import socket
import json
import requests
import time

class HashTableClient:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.s = None

    @classmethod
    def from_project_name(cls, project_name):
        catalog_url = "http://catalog.cse.nd.edu:9097/query.json"

        delay = 1
        while True:
            try:
                response = requests.get(catalog_url)
                response.raise_for_status()
                services = response.json()

                # Find the matching entry
                for entry in services:
                    if (entry.get("type") == "hashtable" and
                        entry.get("project") == project_name):

                        host = entry.get("name")
                        port = entry.get("port")
                        print(f"Discovered {project_name} at {host}:{port}")
                        return cls(host, port)

                raise Exception(f"Project '{project_name}' not found in catalog.")

            except Exception as e:
                print(f"DEBUG ONLY: Discovery Error: {e}, trying again in {delay}s")
                time.sleep(delay)
                delay = min(delay * 2, 128)

    def connect(self, debug=True):
        if debug:
            print(f"Connecting to {self.host}:{self.port}")
        delay = 1
        while True:
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if not self.s:
                    raise Exception(f"Trouble creating socket")
                self.s.settimeout(5)
                self.s.connect((self.host, self.port))

            except Exception as e:
                print(f"DEBUG ONLY: Connection Error: {e}, trying again in {delay}s")
                time.sleep(delay)
                delay = min(delay * 2, 128)
            else:
                return

    def close(self):
        if self.s:
            self.s.close()
            self.s = None

    ##### HELPER FUNCTIONS

    def _send(self, msg):
        if not self.s:
            raise ConnectionError("Not Connected")
        data = json.dumps(msg).encode('utf-8')
        length = len(data)
        prefix = f"{length:010}".encode('utf-8')

        self.s.sendall(prefix + data)

    def _recv_exact(self, length):
        buf = b''
        while len(buf) < length:
            chunk = self.s.recv(length - len(buf))
            if not chunk:
                raise ConnectionError("Connection closed")
            buf += chunk
        return buf

    def _recv(self):
        if not self.s:
            raise ConnectionError("Not Connected")
        prefix = self._recv_exact(10)
        length = int(prefix.decode('utf-8'))
        return self._recv_exact(length)

    def _rpc(self, m, k=None, v=None):
        req = {
            "method": m,
            "key": k,
            "value": v
        }

        delay = 1
        while True:
            try:
                if not self.s:
                    self.connect(False)

                self._send(req)

                res = json.loads(self._recv().decode())

                if not res:
                    raise Exception("No Response Received")

                if not res.get("ok"):
                    print(f"{res.get("error", "Unknown Error")} : {res.get("message", "Unknown Server Error")}")
                    return res

                return res.get("data")
            except Exception as e:
                print(f"DEBUG ONLY: RPC Request Error: {e}, trying again in {delay}s")
                self.s = None
                time.sleep(delay)
                delay = min(delay * 2, 128)


    ######################

    def insert(self, k, v):
        self._rpc("insert", k, v)
        return True

    def lookup(self, k):
        return self._rpc("lookup", k).get("value")

    def remove(self, k):
        self._rpc("remove", k)
        return True                                 # treats non-existent k as success

    def size(self):
        return self._rpc("size").get("value")

    def query(self, k):
        res = self._rpc("query", k).get("value")
        return res

    def get_description(self):
        res = self._rpc("desc")
        return (res.get("files"), res.get("peers"))

    #######################
    ### File Functions

    def insert_file(self, key, filename):
        with open(filename, "rb") as f:
            data = f.read()

        value = data.decode('latin-1')

        return self.insert(key, value)

    def lookup_file(self, key, filename):
        value = self.lookup(key)

        if value is None:
            return False

        data = value.encode('latin-1')

        with open(filename, "wb") as f:
            f.write(data)

        return True
