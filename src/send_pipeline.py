# src/chat.py

# TODO:  THE WHOLE VISUAL SEGEMENTATION OF THE SCRIPT 
import uuid
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

#FIXME: we need to gen the key 
AES_KEY = b"7Yv9Wp2Rk5Nx4Qt8Fm3Gj6Hk1Dx7Mp9B"  # Harshita we need to somehow gen and transfer this to peer
destination_ip = "0.1.1.1"  # just for demo purposes will be removed later wards


# =========================================================================
# CHAT PIPELINE ORCHESTRATION
# =========================================================================

def process_chat(text: str, sender: str) -> list:
    """
    Serializes, encrypts, and slices a text message into protocol-safe chunk dictionaries.
    """
    transfer_ready_payload = create_chat_packet(text, sender)

    # TODO: Database persistence logic can hooks into here cleanly
    # db.save_chat_message(transfer_ready_payload)

    transfer_ready_payload = serialize_message(transfer_ready_payload)
    transfer_ready_payload = encrypt_text(transfer_ready_payload, AES_KEY)
    
    # Returns a pre-allocated list of packet dictionaries containing 'total_chunks'
    packets = chunk_encrypted_message(transfer_ready_payload)
    return packets


def send_chat_to_peer(peer_ip: str, text: str, sender_name: str, transport_mgr: TransportManager):
    """
    Processes a raw text message string and transmits it over the network to a specific peer.
    """
    # NOTE: Re-mapped variables correctly so text and identity parameters route without inversion
    packets = process_chat(text, sender_name)
    
    for data_frame in packets:
        transport_mgr.send_packetized_frame(peer_ip, data_frame)
    print(f"[PIPELINE] Chat message successfully packetized and sent to {peer_ip}")


# =========================================================================
# FILE STREAMING PIPELINE ORCHESTRATION
# =========================================================================

def process_and_send_file(peer_ip: str, file_path: str, sender_name: str, transport_mgr: TransportManager, aes_key: bytes):
    """
    Executes the streaming file pipeline end-to-end.
    Processes metadata, encrypts the binary sequence, and handles network I/O.
    """
    
    # NOTE: Generate ONE master session ID here so that Chunk 0 (Metadata)
    # and Chunks 1..N (Data) share the exact same tracking identifier across the wire.
    session_id = str(uuid.uuid4())  # technically this will be our msg id in future 
    

    # PART 1: GENERATE & SEND METADATA (CHUNK 0)

    # 1. Gather raw metadata dict info
    file_metadata = FileStreamer.create_file_packet(file_path, sender_name)
    
    # 2. Convert to raw unencrypted JSON transmission bytes
    serialized_metadata = FileStreamer.serialize_metadata(file_metadata)
    
    # 3. Get the generator containing chunk_index 0
    # NOTE: Passed down the required master session_id parameter
    metadata_generator = FileStreamer.file_packet_generator(
        file_path=file_path,
        payload_source=serialized_metadata,
        message_id=session_id,
        chunk_index=0
    )
    
    # 4. Extract and send the metadata packet immediately
    metadata_packet = next(metadata_generator)
    transport_mgr.send_packetized_frame(peer_ip, metadata_packet)
    print(f"[PIPELINE] Plaintext metadata configuration (Chunk 0) sent to {peer_ip} [Session: {session_id}]")


    # PART 2: STREAM, ENCRYPT, AND SEND FILES (CHUNKS 1 TO N)

    # 1. Create raw disk reader stream
    raw_disk_chunks = FileStreamer.chunk_generator(file_path)
    
    # 2. Wrap it inside  stream encryptor filter
    # NOTE: Standardized to use the passed key securely instead of local constant variables
    encrypted_chunks = encrypt_chunks_file(raw_disk_chunks, aes_key)
    
    # 3. Feed the encrypted stream into the packet generator
    # NOTE: Passed down the matching master session_id parameter
    data_packet_stream = FileStreamer.file_packet_generator(
        file_path=file_path,
        payload_source=encrypted_chunks,
        message_id=session_id #as said the session id will be the message id that will make sure its the same file/session transfer
    )

    # 4. This clean loop automatically pulls, encrypts, and transmits one chunk at a time
    for data_packet in data_packet_stream:
        transport_mgr.send_packetized_frame(peer_ip, data_packet)
        print(f"[PIPELINE] Transmitted sequential data block: Chunk #{data_packet['chunk_index']} / {data_packet['total_chunks'] - 1}")

    print(f"[PIPELINE] File transfer sequence for '{file_path}' completed successfully under ID: {session_id}")