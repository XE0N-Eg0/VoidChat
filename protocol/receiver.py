# ========================================
#              receiver.py
# ========================================
# =========== SYS IMPORTS ================
import json
# =========== CONFIG ================
PACKET_TYPE_CHAT = "chat"
PACKET_TYPE_CHAT_CHUNK = "chat_chunk"
# ========================================
#           GLOBAL STORAGE
# ========================================
chunk_storage = {}

# ========================================
#           CORE FUNCTIONS
# ========================================
def deserialize_message(data: bytes) -> dict:
    """
    Converts bytes back to dictionary
    """

    json_data = data.decode()

    return json.loads(json_data)

def process_packet(packet: dict):
    """
    Processes incoming packet
    """

    packet_type = packet["type"]

    # ==============================
    # CHAT MESSAGE
    # ==============================

    if packet_type == PACKET_TYPE_CHAT:

        sender = packet["sender"]
        payload = packet["payload"]
        timestamp = packet["timestamp"]

        print("\n[CHAT MESSAGE]")
        print(f"Sender    : {sender}")
        print(f"Message   : {payload}")
        print(f"Timestamp : {timestamp}")

    # ==============================
    # CHUNK PACKET
    # ==============================

    elif packet_type == PACKET_TYPE_CHAT_CHUNK:

        process_chunk(packet)

    else:

        print("[WARNING] Unknown Packet")


def process_chunk(packet: dict):
    """
    Stores chunk packet and reconstructs
    full message when complete
    """

    total_chunks = packet["total_chunks"]
    chunk_index = packet["chunk_index"]
    payload = packet["payload"]

    # Convert string representation back to bytes
    if isinstance(payload, str):

        payload = payload.encode(
            errors="ignore"
        )

    # Initialize storage
    if "chunks" not in chunk_storage:

        chunk_storage["chunks"] = {}

        chunk_storage["total_chunks"] = (
            total_chunks
        )

    # Store chunk
    chunk_storage["chunks"][
        chunk_index
    ] = payload

    print(
        f"[INFO] Received Chunk "
        f"{chunk_index + 1}/{total_chunks}"
    )

    # Check completion
    if len(
        chunk_storage["chunks"]
    ) == total_chunks:

        reconstruct_message()


def reconstruct_message():
    """
    Rebuilds original serialized message
    """

    chunks = chunk_storage["chunks"]

    ordered_chunks = []

    for index in sorted(chunks.keys()):

        ordered_chunks.append(
            chunks[index]
        )

    merged_data = b"".join(
        ordered_chunks
    )

    try:

        message = deserialize_message(
            merged_data
        )

        print("\n[INFO] Message Reconstructed")

        process_packet(message)

    except Exception as error:

        print(
            f"[ERROR] Reconstruction Failed: "
            f"{error}"
        )
# ========================================
#              DEMO TEST
# ========================================

def main():
    """
    Demo receiver test
    """

    print("[INFO] Receiver Ready")


if __name__ == "__main__":

    print("[INFO] Running receiver.py")

    main()