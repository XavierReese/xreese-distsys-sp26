#!/usr/bin/env python3
'''
HashTableServer.py

server-side RPC main program
default port = 9246

Usage: HashTableServer.py PROJECT_NAME

Author: Xavier Reese
Date: 6 Feb 2026
'''

import socket
import json
import time
from HashTable import HashTable
import threading
from HashTableClient import HashTableClient

BUFSIZE = 1024

CATALOG_HOST = "catalog.cse.nd.edu"
CATALOG_PORT = 9097

class HashTableServer:
    def __init__(self, proj, host=socket.gethostname(), port=0, peer_id=None):
        self.host = host
        self.port = port
        self.peer_id = peer_id
        self.project_name = proj

        self.ht = HashTable(peer_id=self.peer_id)

        self.peers = set()

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((self.host, self.port))
        self.s.listen(1)                                                 # single client for now
        _, self.port = self.s.getsockname()
        print(f"Server {f"{peer_id} " if peer_id else ""}listening on {self.host}:{self.port}")

    def get_socket(self):
        return self.s

    def get_keys(self):
        return self.ht.get_keys()

    def start_catalog_updates(self):
        threading.Thread(target=self.update, daemon=True).start()

    def insert(self, k, v):
        self.ht.insert(k, v)

    def handle_one_request(self, conn):
        """
        Handle a single request from a non-blocking socket (used by event loop).
        Returns False if the connection was closed, True otherwise.
        """
        try:
            msg = self._recv(conn)
            if not msg:
                return False

            try:
                req = json.loads(msg.decode('utf-8'))
            except Exception as e:
                self._send(conn, {"status": "failure", "message": f"error decoding message: {str(e)}"})
                return True

            ok, err_msg = self._check_schema(req)
            if not ok:
                self._send(conn, {"ok": False, "error": "Invalid Params", "message": err_msg})
                return True

            # get host/port so we can reverse-sync
            try:
                caller_host = conn.getpeername()[0]
            except Exception:
                caller_host = None

            res = self.execute(req, caller_host=caller_host)
            self._send(conn, res)
            return True

        except BlockingIOError:
            return True

    def serve(self):
        threading.Thread(target=self.update, daemon=True).start()
        while True:
            conn, addr = self.s.accept()
            print(f"Client Connected: {addr}")
            self.peers.add(f"{addr[0]}:{addr[1]}")

            try:
                self.handle(conn)
            except Exception as e:
                print(f"Error handling connection: {e}")
            finally:
                conn.close()
                print(f"Client Disconnected: {addr}")

    def update(self):
        self.catalog_s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.catalog_s.connect((CATALOG_HOST, CATALOG_PORT))

        while True:
            u = {
                    "type": "hashtable",
                    "port": self.port,
                    "owner": "xreese",
                    "project": self.project_name
                }
            
            try:
                msg = json.dumps(u).encode('utf-8')
                self.catalog_s.sendto(msg, (CATALOG_HOST, CATALOG_PORT))
                print("Update Sent")
            except Exception as e:
                print(f"Failed to send update: {e}")
            time.sleep(60)

    def _lookup_server_port(self, caller_host):
        try:
            catalog_url = "http://catalog.cse.nd.edu:9097/query.json"
            response = requests.get(catalog_url, timeout=5)
            response.raise_for_status()
            services = response.json()
 
            best = None
            for entry in services:
                if (entry.get("type") == "hashtable"
                        and entry.get("name") == caller_host
                        and entry.get("project", "").startswith(self.base_project_name + "-")
                        and entry.get("project") != self.project_name):
                    if best is None or entry.get("lastheardfrom", 0) > best.get("lastheardfrom", 0):
                        best = entry
 
            if best:
                return best.get("name"), int(best.get("port"))
            return None
        except Exception as e:
            print(f"[Server {self.peer_id}] Catalog lookup failed: {e}")
            return None

    def _reverse_sync(self, caller_host):
        """
        After receiving a get_description, this function is called to reverse sync with that peer
        """
        result = self._lookup_server_port(caller_host)
        if not result:
            print(f"[Server {self.peer_id}] Could not find server port for {caller_host}, skipping reverse sync.")
            return

        host, port = result
        print(f"[Server {self.peer_id}] Reverse syncing to {host}:{port}")
        try:
            from HashTableClient import HashTableClient
            client = HashTableClient(host, port)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((host, port))
            sock.settimeout(10)
            client.s = sock

            remote_files, _ = client.get_description()
            if not remote_files:
                client.close()
                return

            local_keys = set(self.ht.get_keys())
            new_keys = [k for k in remote_files if k not in local_keys]
            random.shuffle(new_keys)

            share = max(1, len(new_keys) // 2)
            for key in new_keys[:share]:
                data = client.lookup(key)
                if data is not None:
                    if not isinstance(data, str):
                        import json as _json
                        data = _json.dumps(data)
                    self.ht.insert(key, data)
                    print(f"[Server {self.peer_id}] Reverse sync: stored '{key}' from {host}:{port}")

            client.close()
        except Exception as e:
            print(f"[Server {self.peer_id}] Reverse sync to {host}:{port} failed: {e}")



    ###### SEND/RECEIVE
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

    def _check_schema(self, msg):
        method = msg.get("method")
        key = msg.get("key")

        match method:
            case "insert":
                if type(key) is not str:
                    return False, "invalid key - must be a string"
                if type(msg.get("value")) is not str:
                    return False, "invalid value - must be a string"

            case "lookup":
                if type(key) is not str:
                    return False, "invalid key - must be a string"
            
            case "remove":
                if type(key) is not str:
                    return False, "invalid key - must be a string"

            case "query":
                if type(key) is not str:
                    return False, "invalid key - must be a string"

            case "size":
                return True, None

            case "desc":
                return True, None

            case _:
                return False, f"unknown method: {method}"

        return True, None

                

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

            ok, err_msg = self._check_schema(req)
            if not ok:
                self._send(conn, {"ok": False, "error": "Invalid Params", "message": err_msg})
                continue

            res = self.execute(req)

            self._send(conn, res)

    def execute(self, req, caller_addr=None):
        k = req.get("key")
        v = req.get("value")
        method = req.get("method")

        try:
            match method:
                case "insert":
                    self.ht.insert(k, v)
                    return {"ok": True}

                case "lookup":
                    return {"ok": True, "data": { "value": self.ht.lookup(k)}}

                case "remove":
                    if self.ht.remove(k):
                        return {"ok": True}
                    else:
                        return {"ok": False, "error": "Not Found", "message": f"key {k} does not exist"}

                case "size":
                    size = self.ht.size()
                    if size is not None:
                        return {"ok": True, "data": { "value": size}}
                    else:
                        return {"ok": False, "error": "Internal Error", "message": "Error getting size"}

                case "query":
                    return {"ok": True, "data": { "value": self.ht.query(k)}}

                case "desc":
                    result = {
                            "ok": True, 
                            "data": { "files": self.ht.files(), "peers": list(self.peers)}
                    }

                    # If we know who asked, go back and sync in reverse with them
                    if caller_host:
                        threading.Thread(
                            target=self._reverse_sync,
                            args=(caller_host,),
                            daemon=True
                        ).start()

                    return result

                case _:
                    return {"ok": False, "error": "Invalid Params", "message": f"method \"{method}\" does not exist"}

        except Exception as e:
            return {"ok": False, "error": "Internal Error", "message": str(e)}

###################

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: HashTableServer.py <project_name>")
        exit(1)
    project_name = sys.argv[1]

    # host = socket.gethostname()

    if len(sys.argv) > 2:
        port = int(sys.argv[2])
        ht_server = HashTableServer(proj=project_name, port=port)
    else:
        ht_server = HashTableServer(proj=project_name)
    ht_server.serve()
