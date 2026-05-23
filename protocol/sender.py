# ========================================
#               sender.py
# ========================================

# =========== SYS IMPORTS ================

import json
import time
import uuid
import os

# =========== LOCAL IMPORTS ================
"""
Local project imports will go here

Example:
from protocol.common import serialize_packet
"""

# =========== CONFIG ======================

# Chat message chunk size
MSG_CHUNK_SIZE = 4096

# File transfer chunk size
FILE_CHUNK_SIZE = 262144      # 256 KB

# ========================================
#           MESSAGE FUNCTIONS
# ========================================

def create_message(
    text: str,
    sender: str
) -> dict:
    """
    Purpose:
        Creates a chat message packet
    """

    return {

        "type": "chat",

        "message_id": str(
            uuid.uuid4()
        ),

        "sender": sender,

        # Machine timestamp
        "unix_timestamp": time.time(),

        # Human readable timestamp
        "timestamp": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        "payload": text
    }

def serialize_message(
    msg: dict
) -> bytes:
    """
    Purpose:
        Converts message dictionary into bytes
    """

    json_data = json.dumps(
        msg
    )

    byte_data = json_data.encode()

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

    total_chunks = (
        len(data) + chunk_size - 1
    ) // chunk_size

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

def create_file_packet(
    file_path: str,
    sender: str
) -> dict:
    """
    Purpose:
        Creates file metadata packet
    """

    file_size = os.path.getsize(
        file_path
    )

    file_name = os.path.basename(
        file_path
    )

    return {

        "type": "file",
        "file_id": str(
            uuid.uuid4()
        ),

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
        "timestamp": time.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    }


def read_file(
    file_path: str
) -> bytes:
    """
    Purpose:
        Reads file as bytes
    """

    with open(
        file_path,
        "rb"
    ) as file:

        data = file.read()

    return data


def file_chunking(
    file_data: bytes,
    chunk_size: int = FILE_CHUNK_SIZE
) -> list:
    """
    Purpose:
        Splits large file into chunks
    """

    chunks = []

    total_chunks = (
        len(file_data) + chunk_size - 1
    ) // chunk_size

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

    msg = create_message(
        text="hi, i am sender",
        sender="Partha"
    )

    print("\n========== MESSAGE ==========")

    print(msg)

    # Serialize message
    serialized = serialize_message(
        msg
    )

    print("\n========== SERIALIZED ==========")

    print(serialized)

    # Chunk chat message
    packets = chat_chunking(
        serialized
    )

    print("\n========== CHAT CHUNKS ==========")

    for packet in packets:

        print(packet)

    # ====================================
    # FILE DEMO
    # ====================================

    # User selects file path
    file_path = input(
        "\nEnter file path: "
    )

    # Check file exists
    if not os.path.exists(
        file_path
    ):

        print(
            "\n[ERROR] File not found"
        )

        return

    # Create file metadata packet
    file_packet = create_file_packet(

        file_path=file_path,
        sender="Partha"
    )

    print("\n========== FILE PACKET ==========")

    print(file_packet)

    # Read file
    file_data = read_file(
        file_path
    )

    print("\n========== FILE SIZE ==========")

    print(
        len(file_data),
        "bytes"
    )

    # Chunk file
    file_packets = file_chunking(
        file_data
    )

    print("\n========== FILE CHUNKS ==========")

    # Print first 3 chunks only
    for packet in file_packets[:3]:
        print(packet)

    print(
        f"\n[INFO] Total File Chunks: "
        f"{len(file_packets)}"
    )

# ========================================
#               ENTRY
# ========================================

if __name__ == "__main__":

    print(
        "\n[INFO] Running sender.py"
    )

    main()