# src/send_pipeline.py

# =========================================================================
# RESPONSIBILITIES:
# 1. Orchestrate Outgoing Chat: Packetize, Encrypt, Log to DB, and Transmit
# 2. Orchestrate Outgoing Files: Extract Metadata, Stream-Encrypt, Log, and Transmit
# 3. Maintain Complete Separation of Network, Cryptography, and Persistence
# =========================================================================

import os
import uuid
from typing import Tuple

from protocol.sender import (
    create_chat_packet,
    serialize_message,
    chunk_encrypted_message,
    FileStreamer  
)
from crypto.encrypt import (
    encrypt_text,
    encrypt_chunks_file
)
from networking.transport import (
    TransportManager
)
from networking.connection import (
    ConnectionType
)


# =========================================================================
# CHAT PIPELINE ORCHESTRATION
# =========================================================================

def process_chat(text: str, sender: str, aes_key: bytes) -> Tuple[dict, list]:
    """
    Serializes, encrypts, and slices a text message into protocol-safe chunk dictionaries.
    
    Returns:
        Tuple[dict, list]: The raw metadata packet (for DB logs) and the encrypted network packets.
    """
    # 1. Capture the unencrypted raw metadata envelope mapping the permanent message_id
    raw_metadata_packet = create_chat_packet(text, sender)

    # 2. Serialize and encrypt the payload data block for transmission wires
    serialized_payload = serialize_message(raw_metadata_packet)
    encrypted_payload = encrypt_text(serialized_payload, aes_key)
    
    # 3. Chop the encrypted sequence into network-optimized transmission chunks
    network_packets = chunk_encrypted_message(encrypted_payload)
    
    return raw_metadata_packet, network_packets


def send_chat_to_peer(peer_id: str, peer_ip: str, text: str, sender_name: str, 
                      transport_mgr: TransportManager, db_mgr, aes_key: bytes) -> bool:
    """
    Processes a raw text message string, transmits it over network sockets, 
    and logs the history to disk storage immediately upon successful verification.
    """
    try:
        # 1. Generate transmission structures and retain the clean log envelope
        metadata_packet, network_packets = process_chat(text, sender_name, aes_key)
        
        # 2. Fire every packet frame sequentially across active network sockets
        for data_frame in network_packets:
            transport_mgr.send_packetized_frame(peer_ip, data_frame)
            
        print(f"[PIPELINE] Chat message safely packetized and sent to {peer_ip}")

        # 3. NETWORK SUCCESSFUL: Commit directly to local SQLite archive
        db_mgr.log_message(
            peer_id=peer_id,
            sender_name=sender_name,      # "Partha" -> Placed on the right-side layout bubble
            message_type="text",
            payload=metadata_packet["payload"] # Raw message text stored securely on disk
        )
        return True

    except Exception as e:
        print(f"[PIPELINE ERROR] Transmission crash over chat pipeline channel: {e}")
        return False


# =========================================================================
# FILE STREAMING PIPELINE ORCHESTRATION
# =========================================================================

def process_and_send_file(peer_id: str, peer_ip: str, file_path: str, sender_name: str, 
                          transport_mgr: TransportManager, db_mgr, aes_key: bytes) -> bool:
    """
    Executes the streaming file pipeline end-to-end.
    Processes metadata, encrypts the binary sequence, handles network I/O,
    and saves file pointer logs locally on successful completion.
    """
    if not os.path.exists(file_path):
        print(f"[PIPELINE ERROR] Aborting execution. Target file not found: {file_path}")
        return False

    session_id = str(uuid.uuid4())  

    try:
        # PART 1: GENERATE & SEND METADATA (CHUNK 0)
        file_metadata = FileStreamer.create_file_packet(file_path, sender_name)
        serialized_metadata = FileStreamer.serialize_metadata(file_metadata)
        metadata_generator = FileStreamer.file_packet_generator(
            file_path=file_path,
            payload_source=serialized_metadata,
            message_id=session_id,
            chunk_index=0
        )
        metadata_packet = next(metadata_generator)
        transport_mgr.send_packetized_frame(peer_ip, metadata_packet)
        print(f"[PIPELINE] Plaintext metadata configuration (Chunk 0) sent to {peer_ip} [Session: {session_id[:8]}]")

        # PART 2: STREAM, ENCRYPT, AND SEND FILES (CHUNKS 1 TO N)
        raw_disk_chunks = FileStreamer.chunk_generator(file_path)
        encrypted_chunks = encrypt_chunks_file(raw_disk_chunks, aes_key)
        data_packet_stream = FileStreamer.file_packet_generator(
            file_path=file_path,
            payload_source=encrypted_chunks,
            message_id=session_id 
        )

        for data_packet in data_packet_stream:
            transport_mgr.send_packetized_frame(peer_ip, data_packet)
            print(f"[PIPELINE] Transmitted sequential data block: Chunk #{data_packet['chunk_index']} / {data_packet['total_chunks'] - 1}")

        print(f"[PIPELINE] File transfer sequence for '{file_path}' completed successfully under ID: {session_id[:8]}")

        # PART 3: SUCCESSFUL LOG ENTRY PERSISTENCE
        filename = os.path.basename(file_path)
        db_mgr.log_message(
            peer_id=peer_id,
            sender_name=sender_name,
            message_type="file",
            payload=filename,
            file_path=file_path
        )
        
        # CHANGES: Explicitly close the FILE channel socket after transfer completes
        # This prevents idle sockets from clogging the network interface/firewall
        try:
            transport_mgr.connection_manager.close_data_channel(peer_ip, ConnectionType.FILE)
            print(f"[PIPELINE] Closed file transfer socket to {peer_ip}")
        except Exception as cleanup_err:
            print(f"[PIPELINE WARNING] Failed to close FILE socket: {cleanup_err}")
            
        return True

    except Exception as e:
        print(f"[PIPELINE ERROR] Critical crash during binary file transfer execution: {e}")
        return False