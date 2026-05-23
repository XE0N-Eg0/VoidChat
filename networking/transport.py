# transport.py

# 
# =========================================================
# TRANSPORT LAYER
# =========================================================
# Responsibilities:
# 1. Frame outgoing packets
# 2. Send framed chunks over TCP
# 3. Receive framed chunks
# 4. Reassemble messages
# 5. Emit completed payloads
#
# NOTE:

# It ONLY:
# - transports bytes
# - frames chunks
# - reassembles messages


# ================= SYS IMPORTS ===========================
import struct
import threading
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, Optional

# ================= LOCAL IMPORTS =========================
from networking.connection import ConnectionManager


# =========================================================
# CONFIG
# =========================================================

CHUNK_SIZE = 4096
FRAME_VERSION = 1
CHANNEL_MAP = {
    "txt": 1,
    "file": 2,
    "av": 3,
}

REVERSE_CHANNEL_MAP = {
    value: key
    for key, value in CHANNEL_MAP.items()
}

# =========================================================
# FRAME FORMAT
# =========================================================
#
# HEADER STRUCTURE:
# -----------------
#
# version       -> 1 byte
# channel_id    -> 1 byte
# flags         -> 1 byte
# reserved      -> 1 byte
# message_id    -> 16 bytes (UUID)
# chunk_index   -> 4 bytes
# total_chunks  -> 4 bytes
# payload_size  -> 4 bytes
#
# TOTAL HEADER SIZE = 32 bytes
#
# =========================================================

HEADER_FORMAT = "!BBBB16sIII"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

FINAL_CHUNK_FLAG = 1


# =========================================================
# RECEIVED MESSAGE BUFFER
# =========================================================

@dataclass
class MessageBuffer:
    total_chunks: int
    chunks: Dict[int, bytes]


# =========================================================
# TRANSPORT MANAGER
# =========================================================

class TransportManager:

    def __init__(self,connection_manager: ConnectionManager):

        self.connection_manager = connection_manager

        # message_id -> MessageBuffer
        self.receive_buffers = {}

        # packet handlers
        self.handlers = []

        self.running = False

        # peer/channel receive threads
        self.receive_threads = {}

    # =====================================================
    # START
    # =====================================================

    def start(self):

        if self.running:
            return

        print("\n[INFO] Starting transport layer...")

        self.running = True

        self._start_receive_workers()

    # =====================================================
    # STOP
    # =====================================================

    def stop(self):

        if not self.running:
            return

        print("\n[INFO] Stopping transport layer...")

        self.running = False

    # =====================================================
    # REGISTER HANDLER
    # =====================================================

    def register_handler(
        self,
        callback: Callable
    ):

        self.handlers.append(callback)

    # =====================================================
    # SEND
    # =====================================================

    def send(
        self,
        peer_ip: str,
        channel: str,
        encrypted_data: bytes,
        message_id: Optional[str] = None
    ):

        if channel not in CHANNEL_MAP:
            raise ValueError(
                f"Unknown channel: {channel}"
            )

        sock = self.connection_manager.get_socket(
            peer_ip,
            channel
        )

        if not sock:
            raise ConnectionError(
                f"No active socket for {peer_ip}"
            )

        # ================================================
        # MESSAGE ID
        # ================================================

        if message_id is None:
            message_id = str(uuid.uuid4())

        message_uuid = uuid.UUID(message_id)

        # ================================================
        # CHUNKING
        # ================================================

        chunks = self._chunk_data(
            encrypted_data
        )

        total_chunks = len(chunks)

        # ================================================
        # SEND CHUNKS
        # ================================================

        for chunk_index, chunk in enumerate(chunks):

            is_final = (
                chunk_index == total_chunks - 1
            )

            frame = self._build_frame(
                channel=channel,
                message_uuid=message_uuid,
                chunk_index=chunk_index,
                total_chunks=total_chunks,
                payload=chunk,
                final=is_final
            )

            sock.sendall(frame)

    # =====================================================
    # CHUNK DATA
    # =====================================================

    def _chunk_data(
        self,
        data: bytes
    ):

        return [
            data[i:i + CHUNK_SIZE]
            for i in range(
                0,
                len(data),
                CHUNK_SIZE
            )
        ]

    # =====================================================
    # BUILD FRAME
    # =====================================================

    def _build_frame(
        self,
        channel,
        message_uuid,
        chunk_index,
        total_chunks,
        payload,
        final=False
    ):

        version = FRAME_VERSION

        channel_id = CHANNEL_MAP[channel]

        flags = 0

        if final:
            flags |= FINAL_CHUNK_FLAG

        reserved = 0

        payload_size = len(payload)

        header = struct.pack(
            HEADER_FORMAT,
            version,
            channel_id,
            flags,
            reserved,
            message_uuid.bytes,
            chunk_index,
            total_chunks,
            payload_size
        )

        return header + payload

    # =====================================================
    # START RECEIVE WORKERS
    # =====================================================

    def _start_receive_workers(self):

        connections = (
            self.connection_manager.connections
        )

        for peer_ip, peer_channels in (
            connections.items()
        ):

            for channel_name in CHANNEL_MAP.keys():

                sock = getattr(
                    peer_channels,
                    channel_name
                )

                if not sock:
                    continue

                thread_key = (
                    peer_ip,
                    channel_name
                )

                if thread_key in self.receive_threads:
                    continue

                thread = threading.Thread(
                    target=self._receive_loop,
                    args=(
                        peer_ip,
                        channel_name,
                        sock
                    ),
                    daemon=True
                )

                thread.start()

                self.receive_threads[
                    thread_key
                ] = thread

    # =====================================================
    # RECEIVE LOOP
    # =====================================================

    def _receive_loop(
        self,
        peer_ip,
        channel_name,
        sock
    ):

        print(
            f"[TRANSPORT]"
            f" Receiving {channel_name}"
            f" from {peer_ip}"
        )

        while self.running:

            try:

                # ========================================
                # READ HEADER
                # ========================================

                header = self._recv_exact(
                    sock,
                    HEADER_SIZE
                )

                if not header:
                    break

                (
                    version,
                    channel_id,
                    flags,
                    reserved,
                    message_uuid_bytes,
                    chunk_index,
                    total_chunks,
                    payload_size
                ) = struct.unpack(
                    HEADER_FORMAT,
                    header
                )

                # ========================================
                # READ PAYLOAD
                # ========================================

                payload = self._recv_exact(
                    sock,
                    payload_size
                )

                if payload is None:
                    break

                # ========================================
                # MESSAGE ID
                # ========================================

                message_id = str(
                    uuid.UUID(
                        bytes=message_uuid_bytes
                    )
                )

                # ========================================
                # STORE CHUNK
                # ========================================

                self._store_chunk(
                    message_id=message_id,
                    total_chunks=total_chunks,
                    chunk_index=chunk_index,
                    payload=payload,
                    peer_ip=peer_ip,
                    channel=channel_name
                )

            except Exception as e:

                print(
                    f"[TRANSPORT ERROR]"
                    f" {peer_ip}: {e}"
                )

                break

    # =====================================================
    # STORE CHUNK
    # =====================================================

    def _store_chunk(
        self,
        message_id,
        total_chunks,
        chunk_index,
        payload,
        peer_ip,
        channel
    ):

        if message_id not in self.receive_buffers:

            self.receive_buffers[
                message_id
            ] = MessageBuffer(
                total_chunks=total_chunks,
                chunks={}
            )

        buffer = self.receive_buffers[
            message_id
        ]

        buffer.chunks[
            chunk_index
        ] = payload

        # ================================================
        # CHECK COMPLETE
        # ================================================

        if len(buffer.chunks) != buffer.total_chunks:
            return

        # ================================================
        # REASSEMBLE
        # ================================================

        ordered_chunks = [
            buffer.chunks[i]
            for i in range(buffer.total_chunks)
        ]

        full_payload = b"".join(
            ordered_chunks
        )

        # cleanup
        del self.receive_buffers[message_id]

        # ================================================
        # EMIT
        # ================================================

        self._emit_message(
            peer_ip=peer_ip,
            channel=channel,
            message_id=message_id,
            payload=full_payload
        )

    # =====================================================
    # EMIT MESSAGE
    # =====================================================

    def _emit_message(
        self,
        peer_ip,
        channel,
        message_id,
        payload
    ):

        for handler in self.handlers:

            try:

                handler({
                    "peer_ip": peer_ip,
                    "channel": channel,
                    "message_id": message_id,
                    "payload": payload,
                })

            except Exception as e:

                print(
                    f"[HANDLER ERROR] {e}"
                )

    # =====================================================
    # RECEIVE EXACT
    # =====================================================

    def _recv_exact(
        self,
        sock,
        size
    ):

        data = b""

        while len(data) < size:

            chunk = sock.recv(
                size - len(data)
            )

            if not chunk:
                return None

            data += chunk

        return data


# =========================================================
# TESTING / DEBUG
# =========================================================

if __name__ == "__main__":

    import json
    import time

    from networking.discovery import (
        DiscoveryService
    )

    username = input("Username: ")

    # =====================================================
    # DISCOVERY
    # =====================================================

    discovery = DiscoveryService(username)

    discovery.start()

    # =====================================================
    # CONNECTIONS
    # =====================================================

    connection_manager = ConnectionManager(
        username
    )

    connection_manager.start()

    # =====================================================
    # TRANSPORT
    # =====================================================

    transport = TransportManager(
        connection_manager
    )

    # =====================================================
    # HANDLER
    # =====================================================

    def on_message(data):

        print("\n========== MESSAGE ==========")

        print(f"Peer      : {data['peer_ip']}")
        print(f"Channel   : {data['channel']}")
        print(f"MessageID : {data['message_id']}")
        print(f"Payload   : {data['payload']}")

    transport.register_handler(
        on_message
    )

    transport.start()

    # =====================================================
    # CLI LOOP
    # =====================================================

    print("""
Commands:
---------
peers
connect <ip>
send <ip> <message>
exit
    """)

    try:

        while True:

            command = input("\n> ").strip()

            # =============================================
            # PEERS
            # =============================================

            if command == "peers":

                peers = discovery.get_peers()

                print(
                    "\n========== PEERS =========="
                )

                for peer_id, data in peers.items():

                    print(f"""
Peer ID : {peer_id}
Username: {data['username']}
IP      : {data['ip']}
                    """)

            # =============================================
            # CONNECT
            # =============================================

            elif command.startswith("connect"):

                parts = command.split()

                if len(parts) != 2:
                    print(
                        "Usage: connect <ip>"
                    )
                    continue

                _, ip = parts

                connection_manager.connect_to_peer(
                    ip
                )

                time.sleep(1)

                transport._start_receive_workers()

            # =============================================
            # SEND
            # =============================================

            elif command.startswith("send"):

                parts = command.split(
                    maxsplit=2
                )

                if len(parts) != 3:
                    print(
                        "Usage: send <ip> <message>"
                    )
                    continue

                _, ip, message = parts

                payload = {
                    "type": "chat",
                    "message": message
                }

                encoded = json.dumps(
                    payload
                ).encode()

                # fake encrypted bytes for now
                encrypted = encoded

                transport.send(
                    peer_ip=ip,
                    channel="txt",
                    encrypted_data=encrypted
                )

            # =============================================
            # EXIT
            # =============================================

            elif command == "exit":
                break

            else:
                print("Unknown command")

    except KeyboardInterrupt:
        pass

    finally:

        transport.stop()

        connection_manager.stop()

        discovery.stop()

        print("\n[INFO] Shutdown complete.")
