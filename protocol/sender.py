# ========================================
#               sender.py
# ========================================

# =========== SYS IMPORTS ================
import json
import time
import uuid
import os

from typing import Generator, Dict

# =========== LOCAL IMPORTS ================
"""
Local project imports will go here

Example:
from protocol.common import serialize_packet
"""

# =========== CONFIG ======================

# Chat message chunk size
MSG_CHUNK_SIZE = 4096         # 4 KB

# File transfer chunk size
FILE_CHUNK_SIZE = 262144      # 256 KB

# ========================================
#           MESSAGE FUNCTIONS
# ========================================

def create_message(text: str, sender: str) -> dict:
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
    json_data = json.dumps(msg)
    byte_data = json_data.encode("utf-8")
    return byte_data
# ========================================
#           CHAT CHUNKING
# ========================================

def chat_chunking(
    data: bytes,
    chunk_size: int = MSG_CHUNK_SIZE
) -> list:
    """
    Purpose:
        Splits serialized message into chunks
    """

    chunks = []

    total_chunks = (len(data) + chunk_size - 1) // chunk_size

    for index in range(total_chunks):
        start = index * chunk_size
        end = start + chunk_size
        chunk = data[start:end]
        packet = {
            "type": "chat_chunk",
            "chunk_index": index,
            "total_chunks": total_chunks,
            "payload": chunk
        }
        chunks.append(packet)
    return chunks

# ========================================
#           FILE FUNCTIONS
# ========================================
def create_file_packet(file_path: str,sender: str) -> dict:
    """
    Purpose:
        Creates file metadata packet
    """
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    return {
        "type": "file",
        "file_id": str(uuid.uuid4()),
        "sender": sender,
        # Full file path
        "file_path": file_path,
        # File name only
        "file_name": file_name,
        # File size in bytes
        "file_size": file_size,
        # Machine timestamp
        "unix_timestamp": time.time(),
        # Human readable timestamp
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
def read_file(file_path: str) -> bytes:
    """
    Purpose:
        Reads file as bytes
    """

    with open(file_path, "rb") as file:
        data = file.read()
    return data
# ========================================
#         FILE STREAMING CLASS
# ========================================
class FileStreamer:
    @staticmethod
    def serialize_metadata(file_path: str) -> bytes:
        """
        Extracts and serializes ONLY
        the metadata of the file.

        Sent BEFORE actual file chunks.
        """

        filename = os.path.basename(file_path)

        filesize = os.path.getsize(file_path)

        metadata: Dict = {"filename": filename,"filesize": filesize,"type": "file_transfer_init"}

        # Serialize metadata dict to JSON bytes
        return json.dumps(metadata).encode("utf-8")

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
#         FILE CHUNK GENERATOR
# ========================================
def file_chunk_generator(file_path,chunk_size=FILE_CHUNK_SIZE):
    """
    Reads a file lazily from disk,
    yielding one chunk at a time.
    """

    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


def file_chunking(file_data: bytes,chunk_size: int = FILE_CHUNK_SIZE) -> list:
    """
    Purpose:
        Splits large file into chunks
    """

    chunks = []

    total_chunks = (len(file_data) + chunk_size - 1) // chunk_size

    for index in range(total_chunks):
        start = index * chunk_size
        end = start + chunk_size
        chunk = file_data[start:end]

        packet = {
            "type": "file_chunk",
            "chunk_index": index,
            "total_chunks": total_chunks,
            "payload": chunk
        }
        chunks.append(packet)
    return chunks
# ========================================
#              DEMO TEST
# ========================================
def main():
    # ====================================
    # CHAT MESSAGE DEMO
    # ====================================
    msg = create_message(text="hi, i am sender",sender="Partha")
    print("\n========== MESSAGE ==========")
    print(msg)
    # Serialize message
    serialized = serialize_message(msg)
    print("\n========== SERIALIZED ==========")
    print(serialized)
    # Chunk chat message
    packets = chat_chunking(serialized)
    print("\n========== CHAT CHUNKS ==========")
    for packet in packets:
        print(packet)
    # ====================================
    # FILE DEMO
    # ====================================
    # User selects file path
    file_path = input("\nEnter file path: ")
    # Check file exists
    if not os.path.exists(file_path):
        print("\n[ERROR] File not found")
        return
    # Create file metadata packet
    file_packet = create_file_packet(file_path=file_path,sender="Partha")

    print("\n========== FILE PACKET ==========")
    print(file_packet)

    # Read full file
    file_data = read_file(file_path)

    print("\n========== FILE SIZE ==========")

    print(len(file_data), "bytes")

    # Chunk full file
    file_packets = file_chunking(file_data)

    print("\n========== FILE CHUNKS ==========")

    # Print first 3 chunks only
    for packet in file_packets[:3]:
        print(packet)

    print(f"\n[INFO] Total File Chunks: "
        f"{len(file_packets)}"
    )

    # ====================================
    # STREAMING DEMO
    # ====================================

    print("\n========== STREAMING DEMO ==========")

    metadata = FileStreamer.serialize_metadata(
        file_path
    )

    print("\nMetadata:")
    print(metadata)

    print("\nStreaming chunks:")

    for index, chunk in enumerate(FileStreamer.chunk_generator(file_path)):

        print(f"Chunk {index} -> "f"{len(chunk)} bytes")
        # Print first 3 chunks only
        if index >= 2:
            break
# ========================================
#               ENTRY
# ========================================
if __name__ == "__main__":
    print("\n[INFO] Running sender.py")
    main()