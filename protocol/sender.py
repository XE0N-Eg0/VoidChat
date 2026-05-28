# protocol/sender.py

# =========== SYS IMPORTS ================
import json
import time
import uuid
import os
from typing import Generator, Optional
import math
from collections.abc import Iterable


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
        chunk_size: int = MSG_CHUNK_SIZE,) -> list:
    """
    Purpose:
        Splits encrypted message into protocol-safe chunks.

    Architecture:
        serialize → encrypt → chunk (THIS LAYER ONLY HANDLES ENCRYPTED DATA)
    """
    message_id = str(uuid.uuid4()) #NOTE: we generated the UUID before also which may not be necessary unless db needs that
    chunks = []
    total_chunks = (len(encrypted_blob) + chunk_size - 1) // chunk_size

    for index in range(total_chunks):
        start = index * chunk_size
        end = start + chunk_size

        chunk = encrypted_blob[start:end]

        packet = {
            "channel": "text",
            "message_id": message_id, #NOTE: this will be later session id
            "chunk_index": index,
            "total_chunks": total_chunks,
            "payload": chunk #the actual chunks
        }
        chunks.append(packet)

    return chunks  #list of chucnks FIXME: the nameing shall be changed we should append chunk and return packets 

# ========================================
#         FILE STREAMING CLASS
# ========================================

class FileStreamer():

    @staticmethod
    def create_file_packet(file_path: str, sender: str) -> dict:
        """
        Purpose:
            Creates file metadata packet for network transfer.
        """
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)

        metadata = {
            "sender": sender,
            "file_name": file_name,
            "file_size": file_size,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        return metadata

    @staticmethod
    def serialize_metadata(metadata: dict) -> bytes:
        """
        Serializes metadata packet into bytes.
        """
        return json.dumps(metadata, separators=(",", ":")).encode("utf-8")

    @staticmethod
    def chunk_generator(file_path: str, chunk_size: int = FILE_CHUNK_SIZE) -> Generator[bytes, None, None]:
        """
        Lazily reads a file from disk and yields raw binary chunks.
        """
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk

    @staticmethod
    def file_packet_generator( 
        file_path: str,  
        payload_source,  # Serialized metadata bytes OR an iterable/generator of encrypted chunks
        message_id: str, # NOTE: Passed from above to keep message_id identical between metadata and data
        chunk_size: int = FILE_CHUNK_SIZE,
        chunk_index: Optional[int] = None
    ) -> Generator[dict, None, None]:
        """
        Wraps payloads into standard dictionary packets matching TransportManager expectations.
        """
        file_size = os.path.getsize(file_path)
        data_chunks_count = math.ceil(file_size / chunk_size)
        total_chunks = 1 + data_chunks_count  # Metadata chunk (Index 0) + Data Chunks

        # Case A: Create and yield ONLY the metadata chunk
        if chunk_index == 0:
            metadata_chunk = {
                "channel": "file",
                "message_id": message_id,
                "chunk_index": 0,
                "total_chunks": total_chunks,
                "payload": payload_source  # Serialized metadata bytes
            }
            yield metadata_chunk
            return  # Terminate generator cleanly

        # Case B: Process and yield the streaming data frames sequentially
        current_idx = 1
        for single_encrypted_chunk in payload_source:
            data_packet = {
                "channel": "file",
                "message_id": message_id,
                "chunk_index": current_idx,
                "total_chunks": total_chunks,
                "payload": single_encrypted_chunk
            }
            yield data_packet
            current_idx += 1

# ========================================
#               DEMO TEST                       # NOTE: we dont really need this now but its fine we can remove later
# ========================================

def main():
    # ====================================
    # CHAT MESSAGE DEMO
    # ====================================
    msg = create_chat_packet(text="hi, i am sender", sender="Partha")

    print("\n========== MESSAGE ==========")
    print(msg)

    serialized = serialize_message(msg)

    print("\n========== SERIALIZED ==========")
    print(serialized)

    packets = chunk_encrypted_message(serialized)

    print("\n========== CHAT CHUNKS ==========")
    for packet in packets:
        print(f"Index {packet['chunk_index']}/{packet['total_chunks']} -> Message ID: {packet['message_id']}")

    # ====================================
    # FILE DEMO
    # ====================================
    file_path = input("\nEnter file path: ")

    if not os.path.exists(file_path):
        print("\n[ERROR] File not found")
        return

    file_packet = FileStreamer.create_file_packet(file_path=file_path, sender="Partha")

    print("\n========== FILE PACKET ==========")
    print(file_packet)

    print("\n========== FILE SIZE ==========")
    print(os.path.getsize(file_path), "bytes")

    print("\n========== STREAMING DEMO ==========")
    metadata = FileStreamer.serialize_metadata(file_packet)

    print("\nMetadata Bytes Payload Size:", len(metadata))
    
    # Showcase how application level orchestration handles generators seamlessly:
    session_id = str(uuid.uuid4())
    
    # 1. Produce Metadata Envelope
    meta_gen = FileStreamer.file_packet_generator(file_path, metadata, message_id=session_id, chunk_index=0)
    meta_packet = next(meta_gen)
    print(f"Generated Metadata Packet: Channel={meta_packet['channel']}, ID={meta_packet['message_id']}, Index={meta_packet['chunk_index']}, Total={meta_packet['total_chunks']}")

    # 2. Produce Sample Data Pipeline Envelopes
    raw_chunks = FileStreamer.chunk_generator(file_path)
    data_packet_generator = FileStreamer.file_packet_generator(file_path, raw_chunks, message_id=session_id)
    
    print("\nStreaming first 2 data packet dictionary outlines:")
    for idx, data_packet in enumerate(data_packet_generator):
        print(f"Data Packet {idx+1}: Channel={data_packet['channel']}, ID={data_packet['message_id']}, Index={data_packet['chunk_index']}/{data_packet['total_chunks']}, Payload Size={len(data_packet['payload'])} bytes")
        if idx >= 1:
            break

if __name__ == "__main__":
    main()