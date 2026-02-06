'''
HashTableClient.py

client-side RPC operations

Author: Xavier Reese
Date: 6 Feb 2026
'''
import socket
import json

class HashTableClient:
    def __init__(self, host="localhost", port=9246):
        self.host = host
        self.port = port
        self.s = None

    def connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.host, self.port))

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

        self._send(req)

        res = json.loads(self._recv().decode())

        if res.get("status") == "failure":
            raise Exception(res.get("message", "Unknown Server Error"))

        return res

    ######################

    def insert(self, k, v):
        self._rpc("insert", k, v)
        return True

    def lookup(self, k):
        return self._rpc("lookup", k).get("result")

    def remove(self, k):
        self._rpc("remove", k)
        return True                                 # treats non-existent k as success

    def size(self):
        return self._rpc("size").get("result")

    def query(self, k):
        res = self._rpc("query", k).get("result")
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
