# src/receiver_pipeline.py
# TODO: VISUAL SEGMENTATION OF CODE 

import os
from typing import Optional, Dict, Any
from protocol.receiver import receive_chat_frame, deserialize_chat_message, handle_file_metadata, receive_file_data_frame
from crypto.decrypt import decrypt_text, decrypt_chunks_file
from protocol.receiver import file_streams

# Global configuration pointer tracking the singular active file download task
# Because only one file is processed at a time, we don't need multi-session dictionaries.
ACTIVE_FILE_TRANSFER: Optional[Dict[str, Any]] = None 
download_File = "./downloads"  #FIXME: We need to fetch it form settings


# =========================================================================
# 1. INDEPENDENT CHAT PROCESSING PIPELINE (ALWAYS RUNNING)
# =========================================================================

def process_incoming_chat(frame: dict, aes_key: bytes) -> Optional[dict]:
    """
    Accepts a raw chat dictionary frame from transport.py.
    Returns the parsed, decrypted chat dictionary message ONLY when fully reassembled.
    Otherwise, returns None if more network frames are expected.
    """
    # 1. Submit frame chunk to the text reassembly storage buffer
    completed_encrypted_blob = receive_chat_frame(frame)
    
    # 2. Return early if the transport layer is still waiting for more fragments
    if not completed_encrypted_blob:
        return None

    # 3. Complete payload recovered Decrypt and parse JSON contents
    try:
        decrypted_bytes = decrypt_text(completed_encrypted_blob, aes_key)
        chat_message_dict = deserialize_chat_message(decrypted_bytes)
        return chat_message_dict
    except Exception as e:
        print(f"[RECEIVE ERROR] Failed cryptographically decrypting incoming chat payload: {e}")
        return None


# =========================================================================
# 2. INDEPENDENT FILE METADATA PROCESSING PIPELINE
# =========================================================================

def initialize_file_transfer(frame: dict, output_directory: str = download_File) -> dict:
    """
    Processes Chunk 0 (Plaintext File Metadata).
    Prepares the storage target path on disk and caches tracking info.
    """
    global ACTIVE_FILE_TRANSFER

    # Parse JSON properties inside the plaintext metadata block
    session_id, metadata = handle_file_metadata(frame)
    
    target_filename = metadata["file_name"]
    destination_path = os.path.join(output_directory, target_filename)

    # Ensure the target storage directory structures exist safely
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    
    # Clear out any previous file remnants at that specific path if it exists
    if os.path.exists(destination_path):
        os.remove(destination_path)

    # Track this singular file target configuration
    ACTIVE_FILE_TRANSFER = {
        "session_id": session_id, 
        "file_name": target_filename,
        "output_path": destination_path
    }

    print(f"[PIPELINE] File transfer initialized for '{target_filename}' ({metadata['file_size']} bytes)")
    return metadata


# =========================================================================
# 3. INDEPENDENT FILE DATA STREAM PROCESSING PIPELINE
# =========================================================================

def stream_incoming_file_chunk(frame: dict, aes_key: bytes) -> bool:
    """
    Processes structural data frames (Chunks 1 to N) for the singular file transfer.
    Decrypts streaming frames dynamically and flushes them directly to your drive.
    
    Returns:
        True if the file is still transferring.
        False when the absolute final packet has safely settled on disk.
    """
    global ACTIVE_FILE_TRANSFER

    if not ACTIVE_FILE_TRANSFER:
        print("[PIPELINE WARNING] Dropping file data chunk: No active file transfer initialized.")
        return False

    # 1. Pipe frame safely into the sliding window frame reassembler
    # Returns a generator yielding sequentially aligned raw chunk data bytes (sorting and returning)
    raw_chunks_generator = receive_file_data_frame(frame)

    # 2. Pass generator sequence directly through stream decryptor fx
    decrypted_chunks_generator = decrypt_chunks_file(raw_chunks_generator, aes_key)

    # 3. Flush blocks cleanly directly to the file system allocation
    target_path = ACTIVE_FILE_TRANSFER["output_path"]
    with open(target_path, "ab") as file_handle:
        for chunk in decrypted_chunks_generator:
            file_handle.write(chunk)

    # 4. Check if the session is finished
    # receiver.py automatically purges the state tracking session when next_expected_index == total_chunks
    
    if ACTIVE_FILE_TRANSFER["session_id"] not in file_streams:
        print(f"[PIPELINE COMPLETE] Singular file download completely closed: '{target_path}' saved.")
        ACTIVE_FILE_TRANSFER = None  # Reset global transfer pointer slot to allow future files
        return False  # Transmission successfully finished

    return True  # Transmission still active, more chunks expected