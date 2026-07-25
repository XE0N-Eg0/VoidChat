# src/main.py

import os
import sys
import json
import uuid
import random
import threading
import time
from typing import Dict, List, Any, Optional, Callable

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from networking.connection import ConnectionManager, ConnectionType
from networking.transport import TransportManager
from networking.discovery import DiscoveryService
from database.core import DatabaseManager

from src.send_pipeline import process_chat, process_and_send_file
from src.receive_pipeline import process_incoming_chat, initialize_file_transfer, stream_incoming_file_chunk

STAGING_AES_KEY = b"7Yv9Wp2Rk5Nx4Qt8Fm3Gj6Hk1Dx7Mp9B"
CONN_TYPE_TO_CHANNEL = {
    ConnectionType.CONTROL: "control",
    ConnectionType.CHAT: "text",
    ConnectionType.FILE: "file",
}

def load_user_identity() -> Dict[str, str]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    config_path = os.path.join(data_dir, "user_config.json")
    os.makedirs(data_dir, exist_ok=True)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                if "peer_id" in config and "username" in config:
                    return config
        except Exception:
            pass

    print("\n" + "="*60)
    print("🌌 INITIAL SETUP: CONFIGURING SECURE LOCAL IDENTITY NODE")
    print("="*60)
    username = input("Enter your public chat alias: ").strip()
    if not username:
        username = f"VoidUser_{random.randint(1000, 9999)}"
        
    config = {"peer_id": str(uuid.uuid4()), "username": username}
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
        f.flush()
        os.fsync(f.fileno())
    print(f"[SUCCESS] Identity bound securely: {username} ({config['peer_id'][:8]})")
    return config

class VoidChatOrchestrator:
    def __init__(self, username: str, peer_id: str):
        self.username = username
        self.peer_id = peer_id
        self.running = False
        self.lock = threading.RLock()
        self.aes_key = STAGING_AES_KEY
        
        self.db = DatabaseManager()
        self.conn_mgr = ConnectionManager()
        self.transport_mgr = TransportManager(self.conn_mgr)
        self.discovery = DiscoveryService(self.username, self.peer_id)
        
        self.known_peers: Dict[str, Dict[str, Any]] = {}
        self.pending_file_consents: Dict[str, bool] = {}
        self.pending_file_transfers: Dict[str, str] = {}
        self.ui_event_callback: Optional[Callable] = None
        
        self.conn_mgr.register_connection_handler(self._handle_new_connection_stream)
        self.transport_mgr.register_handler(self._route_incoming_network_packet)
        self.conn_mgr.set_consent_callback(self._has_file_consent)

    def start(self) -> None:
        with self.lock:
            if self.running: return
            self.running = True
        print("[KERNEL] Booting backend engine layers...")
        self._load_known_peers()
        self.conn_mgr.start()
        self.transport_mgr.start()
        self.discovery.start()
        
        threading.Thread(target=self._connection_manager_loop, daemon=True).start()
        print("[KERNEL] Core system operational. Sockets open and listening.")

    def stop(self) -> None:
        with self.lock:
            if not self.running: return
            self.running = False
        print("\n[SHUTDOWN] Severing network sockets and stopping daemons...")
        self.discovery.stop()
        self.transport_mgr.stop()
        self.conn_mgr.stop()
        print("[SHUTDOWN] Backend core closed down safely.")

    def set_ui_event_callback(self, callback: Callable):
        self.ui_event_callback = callback

    def _load_known_peers(self):
        peers = self.db.get_all_known_peers()
        for p in peers:
            self.known_peers[p["peer_id"]] = p

    def _connection_manager_loop(self):
        while self.running:
            time.sleep(10)
            discovered = self.discovery.get_peers()
            for peer_id, data in discovered.items():
                if peer_id in self.known_peers:
                    known_data = self.known_peers[peer_id]
                    if (known_data.get("ip_address") != data.get("ip") or 
                        known_data.get("username") != data.get("username")):
                        new_ip = data.get("ip")
                        new_username = data.get("username", known_data.get("username"))
                        self._sync_peer_metadata(peer_id, new_username, new_ip)
                    self._ensure_chat_connection(data.get("ip"))
            for peer_id, data in list(self.known_peers.items()):
                if peer_id not in discovered:
                    self._ensure_chat_connection(data.get("ip_address"))

    def _ensure_chat_connection(self, peer_ip: str):
        if not peer_ip: return
        with self.conn_mgr.lock:
            sock = self.conn_mgr.connections[ConnectionType.CHAT].get(peer_ip)
        if not sock:
            try:
                self.conn_mgr.open_data_channel(peer_ip, ConnectionType.CHAT)
            except Exception:
                pass

    def _sync_peer_metadata(self, peer_id: str, username: str, ip: str):
        self.known_peers[peer_id] = {"peer_id": peer_id, "username": username, "ip_address": ip}
        self.db.save_or_update_peer(peer_id, username, ip)

    def _establish_friendship(self, peer_id: str, username: str, ip: str):
        self._sync_peer_metadata(peer_id, username, ip)
        self._ensure_chat_connection(ip)

    def _handle_new_connection_stream(self, peer_ip: str, conn_type: ConnectionType, sock) -> None:
        if not self.running:
            try: sock.close()
            except: pass
            return
        channel_name = CONN_TYPE_TO_CHANNEL.get(conn_type)
        if not channel_name:
            sock.close()
            return
        self.transport_mgr.bind_socket(peer_ip, channel_name, sock)

    def _route_incoming_network_packet(self, frame: Dict[str, Any]) -> None:
        if not self.running: return
        channel = frame.get("channel")
        peer_ip = frame.get("peer_ip", "Unknown")
        
        if channel == "control":
            self._handle_control_signal(frame)
            return

        peer_id = self._resolve_peer_id_by_ip(peer_ip)
        if peer_id not in self.known_peers:
            print(f"[SECURITY] Dropped {channel} packet from unknown peer {peer_ip}")
            return

        if channel == "text":
            msg_dict = process_incoming_chat(frame, self.aes_key, peer_id, self.db)
            if msg_dict and self.ui_event_callback:
                self.ui_event_callback("text_received", {"peer_id": peer_id, "data": msg_dict})
                
        elif channel == "file":
            if frame.get("chunk_index") == 0 or frame.get("is_metadata"):
                initialize_file_transfer(frame)
            else:
                result = stream_incoming_file_chunk(frame, self.aes_key, peer_id, self.db)
                if isinstance(result, dict) and result.get("status") == "complete":
                    if self.ui_event_callback:
                        self.ui_event_callback("file_received", {
                            "peer_id": peer_id,
                            "data": {
                                "sender_name": result["sender_name"],
                                "payload": result["file_name"],
                                "file_path": result["file_path"],
                                "timestamp": time.time(),
                                "message_type": "file"
                            }
                        })

    def _handle_control_signal(self, frame: Dict[str, Any]) -> None:
        try:
            payload_bytes = frame.get("payload", b"")
            if len(payload_bytes) > 4096: return
            data = json.loads(payload_bytes.decode("utf-8"))
            
            msg_type = data.get("type")
            peer_ip = frame.get("peer_ip")
            remote_peer_id = data.get("peer_id")
            remote_username = data.get("username", "Unknown")
            
            if msg_type == "conn_req":
                if self.ui_event_callback:
                    self.ui_event_callback("conn_req", {"username": remote_username, "peer_id": remote_peer_id, "ip": peer_ip})
            elif msg_type == "conn_resp":
                if data.get("status") == "accepted":
                    self._establish_friendship(remote_peer_id, remote_username, peer_ip)
            elif msg_type == "file_req":
                filename = data.get("filename")
                size = data.get("size")
                session_id = data.get("session_id")
                if self.ui_event_callback:
                    self.ui_event_callback("file_req", {"username": remote_username, "filename": filename, "size": size, "ip": peer_ip, "session_id": session_id})
            elif msg_type == "file_resp":
                if data.get("status") == "accepted":
                    session_id = data.get("session_id")
                    if session_id in self.pending_file_transfers:
                        file_path = self.pending_file_transfers.pop(session_id)
                        self._execute_file_transfer(peer_ip, remote_peer_id, file_path)
        except Exception as e:
            print(f"[KERNEL CONTROL ERROR] {e}")

    def _send_control_packet(self, peer_ip: str, payload: dict):
        packet = {
            "channel": "control", "message_id": str(uuid.uuid4()),
            "chunk_index": 0, "total_chunks": 1, "payload": json.dumps(payload).encode("utf-8")
        }
        
        # FIX: Send asynchronously with 3 retries to bypass Windows Firewall initial blocks
        def _async_send():
            for attempt in range(3):
                try:
                    self.transport_mgr.send_packetized_frame(peer_ip, packet)
                    return # Success
                except Exception as e:
                    print(f"[KERNEL] Send attempt {attempt+1} failed to {peer_ip}: {e}")
                    time.sleep(1) # Wait 1 second before retrying
            
            # If all 3 attempts fail, notify the UI
            if self.ui_event_callback:
                self.ui_event_callback("conn_error", {
                    "ip": peer_ip, 
                    "error": "Peer unreachable or firewall blocked the connection."
                })
                    
        threading.Thread(target=_async_send, daemon=True).start()

    def send_connection_request(self, peer_ip: str, peer_id: str):
        payload = {"type": "conn_req", "peer_id": self.peer_id, "username": self.username}
        self._send_control_packet(peer_ip, payload)

    def accept_connection_request(self, peer_id: str, username: str, ip: str):
        self._establish_friendship(peer_id, username, ip)
        payload = {"type": "conn_resp", "status": "accepted", "peer_id": self.peer_id, "username": self.username}
        self._send_control_packet(ip, payload)

    def send_file_request(self, peer_ip: str, peer_id: str, file_path: str):
        session_id = str(uuid.uuid4())
        self.pending_file_transfers[session_id] = file_path
        size = os.path.getsize(file_path)
        payload = {
            "type": "file_req", "session_id": session_id, "filename": os.path.basename(file_path), 
            "size": size, "peer_id": self.peer_id, "username": self.username
        }
        self._send_control_packet(peer_ip, payload)

    def accept_file_request(self, peer_ip: str, session_id: str):
        self.pending_file_consents[peer_ip] = True
        payload = {"type": "file_resp", "session_id": session_id, "status": "accepted"}
        self._send_control_packet(peer_ip, payload)

    def _has_file_consent(self, peer_ip: str) -> bool:
        if self.pending_file_consents.get(peer_ip):
            self.pending_file_consents.pop(peer_ip, None)
            return True
        return False

    def _execute_file_transfer(self, peer_ip: str, peer_id: str, file_path: str):
        success = process_and_send_file(peer_id, peer_ip, file_path, self.username, self.transport_mgr, self.db, self.aes_key)
        if success and self.ui_event_callback:
            self.ui_event_callback("file_sent", {
                "peer_id": peer_id,
                "data": {
                    "sender_name": self.username,
                    "payload": os.path.basename(file_path),
                    "timestamp": time.time(),
                    "message_type": "file"
                }
            })

    def transmit_text_message(self, peer_ip: str, peer_id: str, text: str) -> bool:
        if peer_id not in self.known_peers: return False
        try:
            meta_packet, data_packets = process_chat(text, self.username, self.aes_key)
            for packet in data_packets:
                self.transport_mgr.send_packetized_frame(peer_ip, packet)
            self.db.log_message(peer_id, self.username, "text", text)
            return True
        except Exception as e:
            print(f"[KERNEL ERROR] Text transmission failed: {e}")
            return False

    def _resolve_peer_id_by_ip(self, ip: str) -> str:
        for peer_id, data in self.discovery.get_peers().items():
            if data.get("ip") == ip: return peer_id
        for peer_id, data in self.known_peers.items():
            if data.get("ip_address") == ip: return peer_id
        return f"UNKNOWN_{ip}"

    def discover_nearby(self):
        self.discovery.discover_now()

    def get_online_peers(self) -> Dict[str, Dict[str, Any]]:
        peers = {}
        for peer_id, data in self.known_peers.items():
            ip = data.get("ip_address")
            is_online = self.conn_mgr.is_peer_connected(ip, ConnectionType.CHAT)
            peers[peer_id] = {
                "peer_id": peer_id, "username": data.get("username", "Unknown"),
                "ip": ip, "status": "Online" if is_online else "Offline", "is_friend": True
            }
        for peer_id, data in self.discovery.get_peers().items():
            if peer_id not in peers:
                peers[peer_id] = {
                    "peer_id": peer_id, "username": data.get("username", "Unknown"),
                    "ip": data.get("ip"), "status": "Discovered", "is_friend": False
                }
        return peers

    def get_chat_history(self, target_peer_id: str) -> List[Dict[str, Any]]:
        return self.db.fetch_conversation_history(peer_id=target_peer_id, limit=50)

if __name__ == "__main__":
    user_config = load_user_identity()
    orchestrator = VoidChatOrchestrator(username=user_config["username"], peer_id=user_config["peer_id"])
    orchestrator.start()
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        orchestrator.stop()