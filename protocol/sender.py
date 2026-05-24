#protocol/sender.py

# =========== SYS IMPORTS ================
import json
import time
import uuid
import os
from typing import Generator


# =========== CONFIG ======================

# Chat message chunk size
MSG_CHUNK_SIZE = 4096         # 4 KB

# File transfer chunk size
FILE_CHUNK_SIZE = 262144      # 256 KB

# ========================================
#           MESSAGE FUNCTIONS
# ========================================

def create_chat_packet(text: str, sender: str) -> dict:
    """
    Purpose:
        Creates a chat message packet
    """

    message = {
        "type": "chat",
        "message_id": str(uuid.uuid4()),
        "sender": sender,
        # Machine timestamp
        "unix_timestamp": time.time(),
        # Human readable timestamp
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "payload": text
    }
    return message

def serialize_message(msg: dict) -> bytes:
    """
    Purpose:
        Converts message dictionary into bytes
    """
    json_data = json.dumps(msg, separators=(",", ":"))
    byte_data = json_data.encode("utf-8")

    return byte_data


# ========================================
#           CHAT CHUNKING
# ========================================

def chunk_encrypted_message(
        encrypted_blob: bytes,
        message_id: str = None,
        chunk_size: int = MSG_CHUNK_SIZE,
        protocol_version: str = "1.0") -> list:
    """
    Purpose:
        Splits encrypted message into protocol-safe chunks.

    Architecture:
        serialize → encrypt → chunk (THIS LAYER ONLY HANDLES ENCRYPTED DATA)
    """

    if message_id is None:
        message_id = str(uuid.uuid4())

    chunks = []
    total_chunks = (len(encrypted_blob) + chunk_size - 1) // chunk_size

    for index in range(total_chunks):
        start = index * chunk_size
        end = start + chunk_size

        chunk = encrypted_blob[start:end]

        packet = {
            "type": "chat_chunk",
            "protocol_version": protocol_version,
            "message_id": message_id,
            "chunk_index": index,
            "total_chunks": total_chunks,
            "payload": chunk
        }
        chunks.append(packet)

    return chunks
# ========================================
#         FILE STREAMING CLASS
# ========================================
#           FILE FUNCTIONS
# ========================================

class FileStreamer:

    @staticmethod
    def create_file_packet(file_path: str,sender: str) -> dict:
        """
        Purpose:
            Creates file metadata packet
            for network transfer.
        """

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        metadata = {
            "type": "file_transfer_init",
            "file_id": str(uuid.uuid4()),
            "sender": sender,
            # SAFE METADATA ONLY
            "file_name": file_name,
            "file_size": file_size,
            # TIMESTAMPS
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return metadata

    @staticmethod
    def serialize_metadata(metadata: dict) -> bytes:
        """
        Serializes metadata packet
        into bytes.
        """
        serialized_metadata = json.dumps(metadata).encode("utf-8")
        return serialized_metadata

    @staticmethod
    def chunk_generator(file_path: str,chunk_size: int = 65536) -> Generator[bytes, None, None]:
        """
        Lazily reads a file from disk
        and yields chunks.

        Default:
            64 KB chunks
        """

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

# ========================================
#              DEMO TEST
# ========================================

def main():

    # ====================================
    # CHAT MESSAGE DEMO
    # ====================================

    msg = create_chat_packet(text="hi, i am sender",sender="Partha")

    print("\n========== MESSAGE ==========")
    print(msg)

    serialized = serialize_message(msg)

    print("\n========== SERIALIZED ==========")
    print(serialized)

    packets = chunk_encrypted_message(serialized)

    print("\n========== CHAT CHUNKS ==========")

    for packet in packets:
        print(packet)

    # ====================================
    # FILE DEMO
    # ====================================

    file_path = input("\nEnter file path: ")

    if not os.path.exists(file_path):
        print("\n[ERROR] File not found")
        return

    file_packet = FileStreamer.create_file_packet(file_path=file_path,sender="Partha")

    print("\n========== FILE PACKET ==========")
    print(file_packet)

    print("\n========== FILE SIZE ==========")
    print(os.path.getsize(file_path), "bytes")

    print("\n========== STREAMING DEMO ==========")

    metadata = FileStreamer.serialize_metadata(file_packet)

    print("\nMetadata:")
    print(metadata)

    print("\nStreaming chunks:")

    for index, chunk in enumerate(FileStreamer.chunk_generator(file_path)):
        print(f"Chunk {index} -> {len(chunk)} bytes")
        if index >= 2:
            break
if __name__ == "__main__":
    main()