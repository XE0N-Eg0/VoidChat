# ========================================
#               sender.py
# ========================================

# =========== SYS IMPORTS ================

import json
import time
import uuid


# =========== LOCAL IMPORTS ================
"""
Local project imports will go here

Example:
from protocol.common import serialize_packet
"""
# =========== CONFIG ================

CHUNK_SIZE = 1024

# ========================================
#           CORE FUNCTIONS
# ========================================

def create_message(
    text: str,
    sender: str
) -> dict:
    """
    Purpose:
        Creates a chat message packet

    Input:
        text   -> Chat message
        sender -> Sender name

    Output:
        Returns packet dictionary
    """

    return {
        "type": "chat",
        "message_id": str(uuid.uuid4()),
        "sender": sender,
        "timestamp": time.time(),
        "payload": text
    }



def serialize_message(
    msg: dict
) -> bytes:
    """
    Purpose:
        Converts message dictionary into bytes

    Input:
        msg -> Message packet

    Output:
        Returns encoded bytes
    """

    json_data = json.dumps(msg)

    byte_data = json_data.encode(
            )

    return byte_data
def chunking(
    data: bytes,
    chunk_size: int = CHUNK_SIZE
) -> list:
    """
    Purpose:
        Splits serialized message into
        smaller network chunks

    Input:
        data       -> Serialized bytes
        chunk_size -> Size of each chunk

    Output:
        Returns list of chunk packets
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
#              DEMO TEST
# ========================================

def main():
    """
    Purpose:
        Demonstrates sender workflow
    """

    # Create chat packet
    msg = create_message(
        text="hi, i am sender",
        sender="Partha"
    )

    print("\n[MESSAGE]")
    print(msg)

    # Serialize message
    serialized = serialize_message(
        msg
    )

    print("\n[SERIALIZED]")
    print(serialized)

    # Split into chunks
    packets = chunking(
        serialized,
        20
    )

    print("\n[CHUNKS]")

    for packet in packets:
        print(packet)


if __name__ == "__main__":

    print("[INFO] Running sender.py")

    main()