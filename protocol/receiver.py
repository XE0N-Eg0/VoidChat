#protocol/reciver.py


# =========== SYS IMPORTS ================
import json
import time
# =========== CONFIG =====================

PACKET_TYPE_CHAT = "chat"
PACKET_TYPE_CHAT_CHUNK = "chat_chunk"

CHUNK_TIMEOUT = 60

# ========================================
#           GLOBAL STORAGE
# ========================================
"""
Structure:
chunk_storage = {
    message_id: {
        "total_chunks": int,
        "received_at": float,
        "chunks": {
            chunk_index: bytes
        }
    }
}
"""
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


def validate_packet(packet: dict) -> bool:
    """
    Validates incoming packet
    """
    required_fields = ["type"]

    for field in required_fields:
        if field not in packet:
            print(f"[ERROR] Missing Field: {field}")
            return False
    return True

def cleanup_expired_chunks():
    """
    Removes expired incomplete messages
    """

    current_time = time.time()
    expired_messages = []
    for message_id, storage in (
        chunk_storage.items()
    ):
        received_at = storage["received_at"]
        if (current_time - received_at > CHUNK_TIMEOUT):
            expired_messages.append(message_id)

    for message_id in expired_messages:
        del chunk_storage[message_id]

        print(
            f"[INFO] Removed Expired "
            f"Message: {message_id}"
        )

def process_packet(packet: dict):
    """
    Processes incoming packet
    """

    if not validate_packet(packet):
        return

    packet_type = packet["type"]
    # ==============================
    # CHAT MESSAGE
    # ==============================
    if packet_type == PACKET_TYPE_CHAT:

        sender = packet.get("sender","Unknown")
        payload = packet.get("payload","")
        timestamp = packet.get("timestamp","Unknown")
        print("\n[CHAT MESSAGE]")
        print(f"Sender    : {sender}")
        print(f"Message   : {payload}")
        print(f"Timestamp : {timestamp}")
    # ==============================
    # CHUNK PACKET
    # ==============================

    elif packet_type == (PACKET_TYPE_CHAT_CHUNK):
        process_chunk(packet)
    else:
        print("[WARNING] Unknown Packet")


def process_chunk(packet: dict):
    """
    Stores chunk packet and reconstructs
    full message when complete
    """
    required_fields = ["message_id","total_chunks","chunk_index","payload"]

    for field in required_fields:
        if field not in packet:
            print(f"[ERROR] Missing "
                f"Chunk Field: {field}")
            return

    message_id = packet["message_id"]
    total_chunks = packet["total_chunks"]
    chunk_index = packet["chunk_index"]
    payload = packet["payload"]

    # ==============================
    # VALIDATION
    # ==============================

    if chunk_index >= total_chunks:

        print("[ERROR] Invalid ""Chunk Index")

        return

    # ==============================
    # STRING → BYTES
    # ==============================

    if isinstance(payload, str):

        payload = payload.encode()

    # ==============================
    # INITIALIZE STORAGE
    # ==============================

    if message_id not in (
        chunk_storage
    ):

        chunk_storage[message_id] = {
            "total_chunks":
                total_chunks,
            "received_at":
                time.time(),
            "chunks": {}
        }

    # ==============================
    # STORE CHUNK
    # ==============================

    chunk_storage[
        message_id
    ]["chunks"][
        chunk_index
    ] = payload

    print(

        f"[INFO] Received Chunk "
        f"{chunk_index + 1}"
        f"/{total_chunks}"
    )
    # ==============================
    # CHECK COMPLETION
    # ==============================
    received_chunks = len(

        chunk_storage[
            message_id
        ]["chunks"]
    )
    if received_chunks == total_chunks:

        reconstruct_message(
            message_id
        )
def reconstruct_message(message_id: str):
    """
    Rebuilds original serialized message
    """

    storage = chunk_storage[message_id]

    chunks = storage["chunks"]
    ordered_chunks = []

    for index in sorted(chunks.keys()):
        ordered_chunks.append(chunks[index])

    merged_data = b"".join(ordered_chunks)

    try:

        message = (
            deserialize_message(
                merged_data
            )
        )

        print(
            "\n[INFO] Message "
            "Reconstructed"
        )

        process_packet(message)

    except Exception as error:

        print(

            f"[ERROR] "
            f"Reconstruction Failed: "
            f"{error}"

        )
    finally:

        # Cleanup storage
        del chunk_storage[
            message_id
        ]
# ========================================
#              DEMO TEST
# ========================================

def main():
    """
    Demo receiver test
    """
    print(
        "[INFO] Receiver Ready"
    )

    while True:
        cleanup_expired_chunks()
        time.sleep(5)


if __name__ == "__main__":

    print("[INFO] Running receiver.py")
    main()