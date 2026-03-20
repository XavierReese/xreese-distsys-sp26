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
    def __init__(self, host, port, project_name=None):
        self.host = host
        self.port = port
        self.project_name = project_name
        self.s = None

    @staticmethod
    def get_most_recent(project_name):
        catalog_url = "http://catalog.cse.nd.edu:9097/query.json"

        delay = 1
        while True:
            try:
                response = requests.get(catalog_url)
                response.raise_for_status()
                services = response.json()

                # Find the matching entry
                most_recent = None
                for entry in services:
                    if (entry.get("type") == "hashtable" and
                        entry.get("project") == project_name):
                            if (not most_recent or 
                            entry.get("lastheardfrom") > most_recent.get("lastheardfrom")):
                                most_recent = entry

                if most_recent:
                    return most_recent

                raise Exception(f"Project '{project_name}' not found in catalog.")

            except Exception as e:
                print(f"DEBUG ONLY: Discovery Error: {e}, trying again in {delay}s")
                time.sleep(delay)
                delay = min(delay * 2, 128)


    @classmethod
    def from_project_name(cls, project_name):
        most_recent = cls.get_most_recent(project_name)
        print(f"MOST RECENT: {most_recent}")
        host = most_recent.get("name")
        port = most_recent.get("port")
        print(f"Discovered {project_name} at {host}:{port}")
        return cls(host, port, project_name=project_name)


    def discover(self):
        most_recent = HashTableClient.get_most_recent(self.project_name)
        self.host = most_recent.get("name")
        self.port = most_recent.get("port")


    def connect(self, debug=True):
        if debug:
            print(f"Connecting to {self.host}:{self.port}")

        delay = 1
        while True:
            if not self.port or not self.host:
                self.discover()
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if not self.s:
                    raise Exception(f"Trouble creating socket")
                self.s.settimeout(5)
                self.s.connect((self.host, self.port))
                print(f"DEBUG ONLY: Connected to {self.host}:{self.port}")

            except Exception as e:
                print(f"DEBUG ONLY: Connection Error: {e}, trying again in {delay}s")
                # If theres a project name, try to rediscover
                if self.project_name != None:
                    self.port = None
                    self.host = None
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

    def _rpc(self, m, k=None, v=None, no_retry=False):
        req = {
            "method": m,
            "key": k,
            "value": v
        }

        delay = 1
        while True:
            try:
                if not self.s:
                    if no_retry:
                        raise ConnectionError("Socket not connected")
                    self.connect(False)

                self._send(req)

                res = json.loads(self._recv().decode())

                if not res:
                    raise Exception("No Response Received")

                if not res.get("ok"):
                    print(f"{res.get('error', 'Unknown Error')} : {res.get('message', 'Unknown Server Error')}")
                    return res

                return res.get("data")
            except Exception as e:
                if no_retry:
                    raise
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

    def lookup_direct(self, k):
        """Like lookup() but raises on failure instead of retrying.
        Use this when you've manually set client.s in a sync context."""
        return self._rpc("lookup", k, no_retry=True).get("value")

    def get_description(self, my_project=None):
        """
        Fetch the remote peer's file list.
        Pass my_project so the server knows our project name and can
        reverse-sync back to us by catalog lookup rather than by IP.
        Does not retry — callers manage their own error handling.
        """
        req = {"method": "desc", "key": None, "value": None}
        if my_project:
            req["project"] = my_project
        self._send(req)
        res = json.loads(self._recv().decode())
        if not res or not res.get("ok"):
            raise Exception(f"get_description failed: {res}")
        data = res.get("data")
        return data.get("files"), data.get("peers")

    def size(self):
        return self._rpc("size").get("value")

    def query(self, k):
        res = self._rpc("query", k).get("value")
        return res

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
