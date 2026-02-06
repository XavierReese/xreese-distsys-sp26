#!/usr/bin/env python3
'''
HashTableServer.py

server-side RPC main program
default port = 9246

Usage: HashTableServer.py port_number

Author: Xavier Reese
Date: 6 Feb 2026
'''

import socket
import json
from HashTable import HashTable

BUFSIZE = 1024

class HashTableServer:
    def __init__(self, host=socket.gethostname(), port=9246):
        self.host = host
        self.port = port

        self.ht = HashTable()

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.host, self.port))
        self.s.listen(1)                                                 # single client for now
        print(f"Server listening on {self.host}:{self.port}")

    def serve(self):
        while True:
            conn, addr = self.s.accept()
            print(f"Client Connected: {addr}")

            try:
                self.handle(conn)
            except Exception as e:
                print(f"Error handling connection: {e}")
            finally:
                conn.close()
                print(f"Client Disconnected: {addr}")

    ###### HELPER FUNCTIONS
    def _send(self, conn, msg):
        data = json.dumps(msg).encode('utf-8')
        length = len(data)
        prefix = f"{length:010}".encode('utf-8')

        conn.sendall(prefix + data)

    def _recv_exact(self, conn, length):
        buf = b''
        while len(buf) < length:
            chunk = conn.recv(min(BUFSIZE, length))
            if not chunk:
                return chunk
            buf += chunk
        return buf

    def _recv(self, conn):
        prefix = self._recv_exact(conn, 10)
        if not prefix: 
            return prefix
        length = int(prefix.decode('utf-8'))
        return self._recv_exact(conn, length)
    #########################

    def handle(self, conn):
        while True:
            msg = self._recv(conn)

            if not msg:
                break

            try:
                req = json.loads(msg.decode('utf-8'))          # bytes -> JSON str -> python obj
            except Exception as e:
                print(f"Error decoding message: {e}")
                self._send(conn, {"status": "failure", "message": f"error decoding message: {str(e)}"})
                continue

            res = self.execute(req)

            self._send(conn, res)

    def execute(self, req):
        k = req.get("key")
        v = req.get("value")
        method = req.get("method")

        try:
            match method:
                case "insert":
                    self.ht.insert(k, v)
                    return {"status": "success"}

                case "lookup":
                    return {"status": "success", "result": self.ht.lookup(k)}

                case "remove":
                    if self.ht.remove(k):
                        return {"status": "success"}
                    else:
                        return {"status": "success", "message": f"key {k} not found in table"}

                case "size":
                    return {"status": "success", "result": self.ht.size()}

                case "query":
                    return {"status": "success", "result": self.ht.query(k)}

                case _:
                    return {"status": "failure", "message": f"method \"{method}\" does not exist"}

        except Exception as e:
            return {"status": "failure", "message": str(e)}

###################

if __name__ == "__main__":
    import sys
    host = socket.gethostname()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9246
    ht_server = HashTableServer(host=host, port=port)
    ht_server.serve()
