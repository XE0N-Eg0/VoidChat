# ========================================
#              receiver.py
# ========================================

# =========== SYS IMPORTS ================
import os
import json
import time
from typing import Dict, Iterable

# ========================================
#                CONFIG
# ========================================

CHUNK_TIMEOUT = 60

FLAG_FINAL_CHUNK = 0x01
FLAG_CHAT_DATA = 0x02
FLAG_FILE_METADATA = 0x04
FLAG_FILE_DATA = 0x08

# ========================================
#           GLOBAL STORAGE
# ========================================

chat_buffers = {}

"""
chat_buffers = {
    packet_id: {
        "chunks": {},
        "final_sequence": int | None,
        "received_count": int,
        "created_at": float,
    }
}
"""

file_streams = {}

"""
file_streams = {
    packet_id: {
        "expected_sequence": 0,
        "pending_chunks": {},
        "final_sequence": int | None,
        "created_at": float,
        "metadata": dict | None,
    }
}
"""

# ========================================
#              DECRYPT
# ========================================

def decrypt(data: bytes) -> bytes:
    """
    Replace with real decryption.
    """

    return data


# ========================================
#        DESERIALIZE CHAT MESSAGE
# ========================================

def deserialize_chat_message(
    serialized_message: bytes
) -> dict:

    json_data = serialized_message.decode(
        "utf-8"
    )

    message_dict = json.loads(
        json_data
    )

    return message_dict


# ========================================
#      DESERIALIZE FILE METADATA
# ========================================

def deserialize_file_metadata(
    serialized_metadata: bytes
) -> dict:

    json_data = serialized_metadata.decode(
        "utf-8"
    )

    metadata_dict = json.loads(
        json_data
    )

    return metadata_dict


# ========================================
#        EXTRACT FILE METADATA
# ========================================

def extract_file_metadata(
    metadata_packet: dict
) -> dict:

    return {
        "file_name": metadata_packet.get(
            "file_name"
        ),

        "file_size": metadata_packet.get(
            "file_size"
        ),
    }


# ========================================
#         RECEIVE CHAT FRAME
# ========================================

def receive_chat_frame(
    frame: dict
):

    """
    INPUT:
    {
        peer_ip,
        packet_id,
        sequence,
        final,
        payload
    }

    OUTPUT:
        None OR complete encrypted blob
    """

    packet_id = frame["packet_id"]
    sequence = frame["sequence"]
    final = frame["final"]
    payload = frame["payload"]

    # CREATE BUFFER
    if packet_id not in chat_buffers:

        chat_buffers[packet_id] = {
            "chunks": {},
            "final_sequence": None,
            "received_count": 0,
            "created_at": time.time(),
        }

    buffer_data = chat_buffers[
        packet_id
    ]

    # STORE CHUNK
    if sequence not in buffer_data["chunks"]:

        buffer_data["chunks"][
            sequence
        ] = payload

        buffer_data[
            "received_count"
        ] += 1

    # STORE FINAL SEQUENCE
    if final:

        buffer_data[
            "final_sequence"
        ] = sequence

    # CHECK COMPLETION
    final_sequence = buffer_data[
        "final_sequence"
    ]

    if final_sequence is None:
        return None

    expected_chunks = (
        final_sequence + 1
    )

    if (
        buffer_data["received_count"]
        == expected_chunks
    ):

        encrypted_blob = (
            reconstruct_chat_message(
                packet_id
            )
        )

        # CLEANUP
        del chat_buffers[packet_id]

        return encrypted_blob

    return None


# ========================================
#      RECONSTRUCT CHAT MESSAGE
# ========================================

def reconstruct_chat_message(
    packet_id: str
) -> bytes:

    """
    OUTPUT:
        encrypted_blob: bytes
    """

    buffer_data = chat_buffers[
        packet_id
    ]

    chunks = buffer_data["chunks"]

    ordered = []

    for seq in sorted(chunks):

        ordered.append(
            chunks[seq]
        )

    encrypted_blob = b"".join(
        ordered
    )

    return encrypted_blob


# ========================================
#        PROCESS CHAT MESSAGE
# ========================================

def process_chat_message(
    encrypted_blob: bytes
) -> dict:

    # DECRYPT
    serialized_message = decrypt(
        encrypted_blob
    )

    # DESERIALIZE
    message_dict = (
        deserialize_chat_message(
            serialized_message
        )
    )

    return message_dict


# ========================================
#      RECEIVE FILE METADATA FRAME
# ========================================

def receive_file_metadata_frame(
    frame: dict
) -> dict:

    """
    FLOW

    receive frame
    → detect FILE_METADATA flag
    → decrypt
    → deserialize
    → initialize session
    """

    packet_id = frame["packet_id"]

    encrypted_metadata = frame[
        "payload"
    ]

    # DECRYPT
    serialized_metadata = decrypt(
        encrypted_metadata
    )

    # DESERIALIZE
    metadata_packet = (
        deserialize_file_metadata(
            serialized_metadata
        )
    )

    # EXTRACT
    metadata = extract_file_metadata(
        metadata_packet
    )

    # INITIALIZE STREAM
    file_streams[packet_id] = {
        "expected_sequence": 0,
        "pending_chunks": {},
        "final_sequence": None,
        "created_at": time.time(),
        "metadata": metadata,
    }

    return metadata


# ========================================
#         RECEIVE FILE FRAME
# ========================================

def receive_file_frame(
    frame: dict
) -> Iterable[bytes]:

    """
    INPUT:
    {
        packet_id,
        sequence,
        final,
        payload
    }

    OUTPUT:
        yields encrypted chunk
    """

    packet_id = frame["packet_id"]
    sequence = frame["sequence"]
    final = frame["final"]
    payload = frame["payload"]

    if packet_id not in file_streams:
        return

    stream = file_streams[
        packet_id
    ]

    # STORE PENDING CHUNK
    stream["pending_chunks"][
        sequence
    ] = payload

    # STORE FINAL SEQUENCE
    if final:

        stream[
            "final_sequence"
        ] = sequence

    # RELEASE IN ORDER
    while (
        stream["expected_sequence"]
        in stream["pending_chunks"]
    ):

        expected_sequence = stream[
            "expected_sequence"
        ]

        encrypted_chunk = (
            stream["pending_chunks"].pop(
                expected_sequence
            )
        )

        stream[
            "expected_sequence"
        ] += 1

        yield encrypted_chunk

    # CLEANUP
    final_sequence = stream[
        "final_sequence"
    ]

    if (
        final_sequence is not None
        and
        stream["expected_sequence"]
        > final_sequence
    ):

        del file_streams[packet_id]


# ========================================
#      PROCESS FILE CHUNK STREAM
# ========================================

def process_file_chunk_stream(
    encrypted_chunks: Iterable[bytes]
) -> Iterable[bytes]:

    for encrypted_chunk in encrypted_chunks:

        decrypted_chunk = decrypt(
            encrypted_chunk
        )

        yield decrypted_chunk


# ========================================
#        WRITE STREAM TO FILE
# ========================================

def write_stream_to_file(
    decrypted_chunks: Iterable[bytes],
    output_path: str,
) -> str:

    """
    INPUT:
        decrypted chunks

    OUTPUT:
        final file path
    """

    with open(
        output_path,
        "ab"
    ) as file_handle:

        for chunk in decrypted_chunks:

            file_handle.write(
                chunk
            )

    return output_path


# ========================================
#         CLEANUP OLD BUFFERS
# ========================================

def cleanup_expired_buffers():

    current_time = time.time()

    # CHAT CLEANUP
    expired_chat_packets = []

    for (
        packet_id,
        buffer_data
    ) in chat_buffers.items():

        age = (
            current_time
            - buffer_data["created_at"]
        )

        if age > CHUNK_TIMEOUT:

            expired_chat_packets.append(
                packet_id
            )

    for packet_id in expired_chat_packets:

        del chat_buffers[packet_id]

    # FILE CLEANUP
    expired_file_packets = []

    for (
        packet_id,
        stream
    ) in file_streams.items():

        age = (
            current_time
            - stream["created_at"]
        )

        if age > CHUNK_TIMEOUT:

            expired_file_packets.append(
                packet_id
            )

    for packet_id in expired_file_packets:

        del file_streams[packet_id]