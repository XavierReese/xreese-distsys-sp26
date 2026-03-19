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
import random
from HashTableServer import HashTableServer
from HashTableClient import HashTableClient


class Peer:
    def __init__(self, project_name, peer_name):
        self.peer_name = peer_name
        self.project_name = project_name
        self.sel = selectors.DefaultSelector()

        # Each peer registers under a unique name: project_name-peer_name
        unique_proj = f"{project_name}-{peer_name}"

        # Start our server with the unique project name
        self.server = HashTableServer(proj=unique_proj, peer_id=peer_name)

        # Register the master socket with the selector for accept events
        self.master_socket = self.server.get_socket()
        self.master_socket.setblocking(False)
        self.sel.register(self.master_socket, selectors.EVENT_READ, data="accept")

        # Start catalog heartbeat thread
        self.server.start_catalog_updates()

        # Client will be created after discovering target peer
        self.client = None
        self.target_peer_info = None

        # Store the base project_name for discovery
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

    ########################
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

    ###################################
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
        """Connect to ALL peers and download any keys we don't have, balancing the load"""
        peers = self._get_all_peers()
        if not peers:
            print(f"[{self.peer_name}] no other peers found to sync with")
            return

        for p in peers:
            host = p.get("host")
            port = p.get("port")
            label = p.get("project", "unknown")

            if self.dead_peers.get(label, 0) >= 3:
                print(f"[{self.peer_name}] Skipping likely-dead peer '{label}'")
                continue

            client = HashTableClient(host, port)
            client.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.s.settimeout(2) # give up quickly on dead peers
            try:
                client.s.connect((host, port))
            except Exception:
                print(f"[{self.peer_name}] Peer '{label}' unreachable, skipping.")
                self.dead_peers[label] = self.dead_peers.get(label, 0) + 1
                client.s = None
                continue

            try:
                remote_files, _ = client.get_description()
                if not remote_files:
                    client.close()
                    continue

                local_keys = set(self.server.get_keys())
                new_keys = [k for k in remote_files if not in local_keys]

                if not new_keys:
                    print(f"[{self.peer_name}] Already up to date with '{label}'.")
                    self.dead_peers[label] = 0
                    client.close()
                    continue

                # Shuffle keys for diversity of replications
                random.shuffle(new_keys)

                share = max(1, len(new_keys) // len(peers)) # split new keys amongst peers
                keys_to_fetch = new_keys[:share]

            print(f"[{self.peer_name}] Fetching {len(keys_to_fetch)}/{len(new_keys)} keys from '{label}'")
            for key in keys_to_fetch:
                data = client.lookup(key)
                if data is not None:
                    if not isinstance(data, str):
                        data = json.dumps(data)
                    self.server.insert(key, data)
                    print(f"[{self.peer_name}] Stored '{key}' from '{label}'")

            self.dead_peers[label] = 0

        except Exception as e:
            print(f"[{self.peer_name}] Sync with '{label}' failed: {e}")
            self.dead_peers[label] = self.dead_peers.get(label, 0) + 1

        finally:
            client.close()

    def _get_all_peers(self):
        """ Query the catalog and return all peers in this project except ourselves. """
        print(f"[{self.peer_name}] Querying catalog for peers in '{self.base_project_name}'...")
        catalog_url = "http://catalog.cse.nd.edu:9097/query.json"
        try:
            response = requests.get(catalog_url, timeout=10)
            response.raise_for_status()
            services = response.json()
 
            our_project = f"{self.base_project_name}-{self.peer_name}"
            peers = [
                e for e in services
                if (e.get("type") == "hashtable"
                    and e.get("project", "").startswith(self.base_project_name + "-")
                    and e.get("project") != our_project)
            ]
            print(f"[{self.peer_name}] Found {len(peers)} peer(s) in catalog.")
            return peers
 
        except Exception as e:
            print(f"[{self.peer_name}] Catalog query failed: {e}")
            return []

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python Peer.py <project_name> <peer_name>")
        sys.exit(1)

    p = Peer(sys.argv[1], sys.argv[2])
    p.run()

