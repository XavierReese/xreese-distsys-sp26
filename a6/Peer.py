#!/usr/bin/env python3
'''
Peer.py

Starts a combined server+client peer node for P2P hash table distribution.

Each peer:
  - Runs an event-driven (selector-based) server to handle requests from other peers
  - Registers itself with the name service under a unique name
  - Discovers another peer already in the project and syncs its keys
  - Periodically checks the discovered peer for new data

Usage: Peer.py <project_name> <peer_name>

Author: Xavier Reese
Date: March 2026
'''

import socket
import selectors
import sys
import time
import json
import requests
from HashTableServer import HashTableServer
from HashTableClient import HashTableClient


class Peer:
    def __init__(self, project_name, peer_name):
        self.peer_name = peer_name
        self.project_name = project_name
        self.sel = selectors.DefaultSelector()

        # Each peer registers under a unique name: project_name-peer_name
        # This avoids conflicts when multiple peers share the same project.
        unique_proj = f"{project_name}-{peer_name}"

        # Start our server with the unique project name so it registers
        # under a name that won't collide with other peers in this project.
        self.server = HashTableServer(proj=unique_proj, peer_id=peer_name)

        # Register the master socket with the selector for accept events
        self.master_socket = self.server.get_socket()
        self.master_socket.setblocking(False)
        self.sel.register(self.master_socket, selectors.EVENT_READ, data="accept")

        # Start catalog heartbeat thread so other peers can discover us
        self.server.start_catalog_updates()

        # We'll create a client once we discover a target peer
        self.client = None
        self.target_peer_info = None

        # Store the base project_name for discovery (find OTHER peers)
        self.base_project_name = project_name

    def run(self):
        print(f"[{self.peer_name}] Peer active on {self.server.host}:{self.server.port}. Serving and polling...")

        # Initial discovery & sync — runs once at startup
        self.find_and_sync()

        last_sync_check = time.time()
        sync_interval = 30  # Re-check for new data every 30s

        try:
            while True:
                events = self.sel.select(timeout=1.0)
                for key, mask in events:
                    if key.data == "accept":
                        self.accept_connection(key.fileobj)
                    else:
                        self.handle_peer_request(key, mask)

                if time.time() - last_sync_check > sync_interval:
                    self.perform_p2p_sync()
                    last_sync_check = time.time()

        except KeyboardInterrupt:
            print(f"[{self.peer_name}] Shutting down...")
        finally:
            self.sel.close()

    # -------------------------
    # Server-side: event loop

    def accept_connection(self, sock):
        conn, addr = sock.accept()
        print(f"[{self.peer_name}] Incoming connection from {addr}")
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, data="service")

    def handle_peer_request(self, key, mask):
        sock = key.fileobj
        try:
            still_open = self.server.handle_one_request(sock)
            if not still_open:
                print(f"[{self.peer_name}] Peer disconnected, closing socket.")
                self.sel.unregister(sock)
                sock.close()
        except (ConnectionResetError, BrokenPipeError, OSError):
            print(f"[{self.peer_name}] Connection lost, cleaning up socket.")
            self.sel.unregister(sock)
            sock.close()

    # -------------------------
    # Client-side: discovery & sync

    def find_peer(self):
        """
        Search the catalog for any peer in this project OTHER than ourselves.
        Returns True if a suitable peer was found.
        """
        print(f"[{self.peer_name}] Querying catalog for peers in project '{self.base_project_name}'...")
        catalog_url = "http://catalog.cse.nd.edu:9097/query.json"
        try:
            response = requests.get(catalog_url, timeout=10)
            response.raise_for_status()
            services = response.json()

            our_project = f"{self.base_project_name}-{self.peer_name}"
            best = None
            for entry in services:
                # Match any hashtable in this project that isn't our own registration
                proj = entry.get("project", "")
                if (entry.get("type") == "hashtable" and
                        proj.startswith(self.base_project_name + "-") and
                        proj != our_project):
                    if best is None or entry.get("lastheardfrom", 0) > best.get("lastheardfrom", 0):
                        best = entry

            if best:
                self.target_peer_info = best
                host = best.get("name")
                port = best.get("port")
                print(f"[{self.peer_name}] Found peer '{best.get('project')}' at {host}:{port}")
                self.client = HashTableClient(host, port)
                return True
            else:
                print(f"[{self.peer_name}] No other peers found yet in '{self.base_project_name}' — will retry later.")
                return False

        except Exception as e:
            print(f"[{self.peer_name}] Catalog query failed: {e}")
            return False

    def find_and_sync(self):
        """Find a peer and immediately perform an initial sync."""
        if self.find_peer():
            self.perform_p2p_sync()

    def perform_p2p_sync(self):
        """Connect to the known peer and download any keys we don't have."""
        if not self.target_peer_info or not self.client:
            self.find_and_sync()
            return

        peer_label = self.target_peer_info.get("project", "unknown")
        print(f"[{self.peer_name}] Syncing with peer '{peer_label}'...")
        try:
            # get_description() returns (files_list, peers_list)
            remote_files, remote_peers = self.client.get_description()

            if remote_files is None:
                print(f"[{self.peer_name}] Got empty description from peer.")
                return

            local_keys = set(self.server.get_keys())
            new_keys = [k for k in remote_files if k not in local_keys]

            if not new_keys:
                print(f"[{self.peer_name}] Already up to date with '{peer_label}'.")
                return

            print(f"[{self.peer_name}] {len(new_keys)} new key(s) to download from '{peer_label}'.")
            for key in new_keys:
                print(f"[{self.peer_name}] Downloading key: '{key}' from '{peer_label}'")
                data = self.client.lookup(key)
                if data is not None:
                    # HashTable.insert expects a string value
                    if not isinstance(data, str):
                        data = json.dumps(data)
                    self.server.insert(key, data)
                    print(f"[{self.peer_name}] Stored key: '{key}'")
                else:
                    print(f"[{self.peer_name}] Key '{key}' returned None from peer, skipping.")

        except Exception as e:
            print(f"[{self.peer_name}] Sync failed: {e}. Will retry next interval.")
            # Reset client so we reconnect fresh on next attempt
            if self.client:
                self.client.close()
                self.client = None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python Peer.py <project_name> <peer_name>")
        sys.exit(1)

    p = Peer(sys.argv[1], sys.argv[2])
    p.run()

