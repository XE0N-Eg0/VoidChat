# networking/transport.py
#FIXME: Visual code changes
# ================= RESPONSIBILITIES ======================
# 1. Frame outgoing payloads (Unified Packetized Dictionary method)
# 2. Send framed payloads
# 3. Receive framed payloads
# 4. Parse frame headers (Upgraded to 32-byte layout)
# 5. Emit raw frames matching upper-layer specifications
# 6. Differentiate chunk_index 0 (Metadata chunk) for files
# =========================================================

import struct
import threading
import uuid
from typing import Callable, Dict, Tuple, Optional

# Enums are imported directly to interact with your connection layer boundaries safely
from networking.connection import ConnectionManager, ConnectionType


# =========================================================
# CONFIG & PROTOCOL CONSTANTS
# =========================================================

FRAME_VERSION = 1

# Protocol tokens that travel across the wire network card
CHANNEL_MAP = {
    "text": 1,
    "file": 2,
    "av": 3,
}

REVERSE_CHANNEL_MAP = {
    value: key
    for key, value in CHANNEL_MAP.items()
}

FINAL_CHUNK_FLAG = 1


# =========================================================
# FRAME STRUCTURE (UPGRADED TO 32-BYTES) 
# =========================================================
#NOTE: DO NOT REMOVE THIS FORM CODE
# HEADER FORMAT (!BBBB16sIII):
#
# version       -> 1 byte   (B)
# channel_id    -> 1 byte   (B)
# flags         -> 1 byte   (B)
# reserved      -> 1 byte   (B)
# packet_id     -> 16 bytes UUID (16s)
# chunk_index   -> 4 bytes  (I)
# total_chunks  -> 4 bytes  (I)
# payload_size  -> 4 bytes  (I)
#
# TOTAL = 32 bytes
# =========================================================

HEADER_FORMAT = "!BBBB16sIII"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)


# =========================================================
# TRANSPORT MANAGER
# =========================================================

class TransportManager:

    def __init__(self, connection_manager: ConnectionManager):
        self.connection_manager = connection_manager
        self.running = False

        # Event-driven application handlers (e.g., hooks registered by main.py)
        self.handlers = []

        # Thread & resource synchronization tracking
        self.receive_threads: Dict[Tuple[str, str], threading.Thread] = {}
        self.thread_lock = threading.Lock()

    # =====================================================
    # ENGINE LIFECYCLE MANAGEMENT
    # =====================================================

    def start(self):
        if self.running:
            return

        print("\n[INFO] Starting transport layer...")
        self.running = True

        # Scan and retroactively bind to anything currently tracking inside connection registry
        with self.connection_manager.lock:
            for conn_type, type_map in self.connection_manager.connections.items():
                # Map ConnectionType Enum back to our transport string labels
                if conn_type == ConnectionType.CHAT:
                    channel_str = "text"
                elif conn_type == ConnectionType.FILE:
                    channel_str = "file"
                else:
                    channel_str = "control"

                for peer_ip, raw_socket in type_map.items():
                    if raw_socket:
                        self.bind_socket(peer_ip, channel_str, raw_socket)

    def stop(self):
        if not self.running:
            return

        print("\n[INFO] Stopping transport layer...")
        self.running = False
        
        with self.thread_lock:
            self.receive_threads.clear()

    def register_handler(self, callback: Callable):
        """Registers upper-layer callback handlers to process emitted raw frames."""
        self.handlers.append(callback)

    # =====================================================
    # DYNAMIC SOCKET REGISTRATION API
    # =====================================================

    def bind_socket(self, peer_ip: str, channel_name: str, sock):
        """
        Public endpoint meant to be called dynamically by ConnectionManager or main.py
        whenever a new connection drops or finishes shaking hands.
        """
        if not self.running:
            return

        thread_key = (peer_ip, channel_name)

        with self.thread_lock:
            # Check if an active thread is already managing this identity pipe
            if thread_key in self.receive_threads and self.receive_threads[thread_key].is_alive():
                return

            thread = threading.Thread(
                target=self._receive_loop,
                args=(peer_ip, channel_name, sock),
                daemon=True
            )
            self.receive_threads[thread_key] = thread
            thread.start()
            print(f"[TRANSPORT] Dynamically bound receiver worker for {peer_ip} [{channel_name}]")

    # =====================================================
    # UNIFIED PACKETIZED SENDING LOGIC
    # =====================================================

    def send_packetized_frame(self, peer_ip: str, packet: dict):
        """
        Accepts your standardized intermediate dictionary structures from both 
        chat and file generators, fills in the binary headers, and sends them.
        """
        channel = packet.get("channel")  # Expected: "text" or "file"
        if channel not in CHANNEL_MAP:
            raise ValueError(f"Unknown channel routing: {channel}")

        # Map channel string to your connection manager's expected Enum type
        enum_type = ConnectionType.CHAT if channel == "text" else ConnectionType.FILE

        # Interrogate connection.py safely
        sock = self.connection_manager.open_data_channel(peer_ip, enum_type)
        if not sock:
            raise ConnectionError(f"No active channel socket route for {peer_ip} ({channel})")

        raw_uuid = packet.get("message_id")
        if not raw_uuid:
            raise KeyError("Packet dictionary is missing a unique tracking identifier (message_id)")
        packet_uuid = uuid.UUID(raw_uuid)

        chunk_index = packet.get("chunk_index")
        total_chunks = packet.get("total_chunks")
        payload = packet.get("payload", b"")

        if chunk_index is None or total_chunks is None:
            raise ValueError("Packet must include valid integer tracking indicators for chunk_index and total_chunks")

        # Automatically compute final chunk flag state logic safely
        is_final = (chunk_index == total_chunks - 1)
        flags = FINAL_CHUNK_FLAG if is_final else 0

        # Construct safe binary wire layout envelope (32 bytes total)
        header = struct.pack(
            HEADER_FORMAT,
            FRAME_VERSION,
            CHANNEL_MAP[channel],
            flags,
            0,  # Reserved space field
            packet_uuid.bytes,
            chunk_index,
            total_chunks,
            len(payload)
        )

        try:
            sock.sendall(header + payload)
        except Exception as e:
            print(f"[TRANSPORT WRITE ERROR] Failed transmission to {peer_ip}: {e}")
            self._cleanup_resources(peer_ip, channel, sock)
            raise e

    # =====================================================
    # RECEIVE LOOP WITH INDEX 0 LOGIC DISTINCTION
    # =====================================================

    def _receive_loop(self, peer_ip: str, channel_name: str, sock):
        print(f"[TRANSPORT] Receiving loop initialized for {channel_name} from {peer_ip}")

        while self.running:
            try:
                # 1. Extract exactly 32 bytes required for the updated binary header frame
                header = self._recv_exact(sock, HEADER_SIZE)
                
                # Detect graceful peer closure properly and end loop immediately
                if not header:
                    print(f"[TRANSPORT] Connection closed gracefully by remote peer: {peer_ip}")
                    break

                (
                    version,
                    channel_id,
                    flags,
                    reserved,
                    packet_uuid_bytes,
                    chunk_index,
                    total_chunks,
                    payload_size
                ) = struct.unpack(HEADER_FORMAT, header)

                # Handle malicious/unmapped raw channel values safely
                resolved_channel = REVERSE_CHANNEL_MAP.get(channel_id, None)
                if not resolved_channel:
                    print(f"[PROTOCOL WARNING] Received illegal Channel ID: {channel_id}. Dropping data payload.")
                    self._recv_exact(sock, payload_size)
                    continue

                # 2. Extract the exact binary data payload allocation size
                payload = self._recv_exact(sock, payload_size)
                if payload is None:
                    print(f"[TRANSPORT ERROR] Connection disconnected mid-payload stream from {peer_ip}")
                    break

                # Translate parsed UUID bytes back to standard string representation
                packet_id = str(uuid.UUID(bytes=packet_uuid_bytes))
                is_final = bool(flags & FINAL_CHUNK_FLAG)

                # Emit back out matching upper layer properties exactly
                frame_data = {
                    "peer_ip": peer_ip,
                    "channel": resolved_channel,
                    "chunk_index": chunk_index,
                    "total_chunks": total_chunks,
                    "final": is_final,
                    "payload": payload,
                    "message_id": packet_id
                }

                # -------------------------------------------------------------
                # SPECIAL CASE DISTINCTION: FILE METADATA PACKET (CHUNK 0)
                # -------------------------------------------------------------
                if resolved_channel == "file" and chunk_index == 0:
                    frame_data["is_metadata"] = True  #NOTE: this says upper layer to parse this differntly

                self._emit_frame(frame_data)

            except Exception as e:
                print(f"[TRANSPORT INTERRUPT] Exception in worker loop from {peer_ip}: {e}")
                break

        # Always trigger cleanup when exiting the connection context loop
        self._cleanup_resources(peer_ip, channel_name, sock)

    def _emit_frame(self, frame_data: dict):
        for handler in self.handlers:
            try:
                handler(frame_data)
            except Exception as e:
                print(f"[APPLICATION LAYER HANDLER ERROR] Crash during callback handling: {e}")

    # =====================================================
    # HELPERS & STATE CLEANUP NOTE: this was done by ai so might break 
    # =====================================================

    def _cleanup_resources(self, peer_ip: str, channel_name: str, sock):

        thread_key = (peer_ip, channel_name)
        
        with self.thread_lock:
            if thread_key in self.receive_threads:
                del self.receive_threads[thread_key]

        try:
            sock.shutdown(2)  # SHUT_RDWR
            sock.close()
        except Exception:
            pass

        print(f"[CLEANUP COMPLETE] System cleaned up all transport tracking metrics for {peer_ip} [{channel_name}]")

    def _recv_exact(self, sock, size: int) -> Optional[bytes]:

        data = b""
        while len(data) < size:
            try:
                chunk = sock.recv(size - len(data))
                if not chunk:
                    return None 
                data += chunk
            except (ConnectionResetError, OSError):
                return None  
        return data