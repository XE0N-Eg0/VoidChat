# connection.py (Updated for Ephemeral File Connections & Signaling)

import socket
import threading
import time
from enum import Enum
from typing import Dict, Optional, List, Callable

class ConnectionType(Enum):
    CONTROL = "control"
    CHAT = "chat"
    FILE = "file"

class ConnectionState(Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    CLOSED = "closed"
    FAILED = "failed"

class ConnectionManager:
    def __init__(self):
        self.listeners: Dict[ConnectionType, socket.socket] = {}
        self.connections: Dict[ConnectionType, Dict[str, socket.socket]] = {
            ConnectionType.CONTROL: {},
            ConnectionType.CHAT: {},
            ConnectionType.FILE: {},
        }
        self.connection_handlers: List[Callable] = []
        self.running = False
        self.lock = threading.Lock()

    def register_connection_handler(self, callback: Callable):
        self.connection_handlers.append(callback)

    def _notify_handlers(self, peer_ip: str, conn_type: ConnectionType, sock: socket.socket):
        for callback in self.connection_handlers:
            try:
                callback(peer_ip, conn_type, sock)
            except Exception as e:
                print(f"[CALLBACK ERROR] {e}")

    def start(self):
        self.running = True
        # Keep permanent listeners alive so anyone can ask us to chat or send a file at any time
        self._setup_listener(ConnectionType.CONTROL, 5001)
        self._setup_listener(ConnectionType.CHAT, 6000)
        self._setup_listener(ConnectionType.FILE, 6001)

    def _setup_listener(self, conn_type: ConnectionType, port: int):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(("0.0.0.0", port))
            server.listen(10)
            self.listeners[conn_type] = server
            threading.Thread(target=self._listener_loop, args=(conn_type, server), daemon=True).start()
        except Exception as e:
            print(f"[BIND ERROR] Port {port}: {e}")

    def _listener_loop(self, conn_type: ConnectionType, server_socket: socket.socket):
        while self.running:
            try:
                client_socket, address = server_socket.accept()
                peer_ip = address[0]

                # --- ARCHITECTURAL PLUG FOR CONSENT ---
                if conn_type == ConnectionType.FILE:
                    # If an unexpected inbound file socket connects, but we didn't explicitly 
                    # set a state saying "We approved an incoming file from this IP", drop it!
                    if not self._has_user_consented_to_file(peer_ip):
                        print(f"[SECURITY] Denied unauthorized file socket connection from {peer_ip}")
                        client_socket.close()
                        continue

                with self.lock:
                    self.connections[conn_type][peer_ip] = client_socket

                # Inform transport layer to immediately spin up a receiver thread for this socket
                self._notify_handlers(peer_ip, conn_type, client_socket)

            except OSError:
                break

    def open_data_channel(self, peer_ip: str, conn_type: ConnectionType) -> Optional[socket.socket]:
        """
        Dynamically requests an outbound on-demand pipe (e.g., to send a file).
        Called AFTER consent has been secured via the CONTROL/CHAT layer.
        """
        port_map = {ConnectionType.CONTROL: 5001, ConnectionType.CHAT: 6000, ConnectionType.FILE: 6001}
        
        with self.lock:
            # If it's already open, reuse it (like the Chat socket)
            if peer_ip in self.connections[conn_type]:
                return self.connections[conn_type][peer_ip]

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((peer_ip, port_map[conn_type]))
            
            with self.lock:
                self.connections[conn_type][peer_ip] = sock
            
            # Instantly attach transport layer reading logic to it
            self._notify_handlers(peer_ip, conn_type, sock)
            return sock
        except Exception as e:
            print(f"[CONNECT ERROR] Could not open dynamic {conn_type.value} to {peer_ip}: {e}")
            return None

    def close_data_channel(self, peer_ip: str, conn_type: ConnectionType):
        """
        Closes a specific on-demand channel instantly when a transfer concludes.
        """
        with self.lock:
            sock = self.connections[conn_type].pop(peer_ip, None)
            
        if sock:
            try:
                sock.shutdown(socket.SHUT_RDWR)
                sock.close()
                print(f"[CLEANUP] Closed temporary {conn_type.value} pipe for {peer_ip}")
            except Exception:
                pass

    def _has_user_consented_to_file(self, peer_ip: str) -> bool:
        # Hook this up to your Orchestrator/State layer.
        # True if your app received an 'APPROVED' signal from this peer via Chat/Control within the last few minutes.
        return True