# src/receiver_pipeline.py

# =========================================================================
# RESPONSIBILITIES:
# 1. Reassemble, Decrypt, and De-serialize Inbound Text Conversations
# 2. Extract Plaintext File Metadata (Chunk 0) & Set Up Destination Bounds
# 3. Stream-Decrypt Binary Data Chunks (1 to N) and Flush Directly to Drive
# 4. Save Verified Logs to DB Immediately Upon Complete Reassembly
# =========================================================================

import os
import threading
from typing import Optional, Dict, Any
from protocol.receiver import (
    receive_chat_frame,
    deserialize_chat_message,
    handle_file_metadata,
    receive_file_data_frame,
    file_streams
)
from crypto.decrypt import (
    decrypt_text,
    decrypt_chunks_file
)

# FIXME: This must be fetched from configuration settings later
DEFAULT_DOWNLOAD_DIR = "./downloads"

# =========================================================================
# CHANGES: Replaced global singleton with a thread-safe session dictionary
# This prevents concurrent file transfers from clobbering each other's state.
# =========================================================================
ACTIVE_FILE_TRANSFERS: Dict[str, Dict[str, Any]] = {}
TRANSFERS_LOCK = threading.Lock()


# =========================================================================
# 1. INDEPENDENT CHAT PROCESSING PIPELINE (ALWAYS RUNNING)
# =========================================================================

def process_incoming_chat(frame: dict, aes_key: bytes, peer_id: str, db_mgr) -> Optional[dict]:
    """
    Accepts a raw chat fragment frame, passes it through reassembly, decrypts it,
    and logs the complete conversation message directly to the local database.

    Returns:
        Optional[dict]: The unencrypted metadata packet if fully reassembled, otherwise None.
    """
    # 1. Submit frame chunk to the memory reassembly storage buffers
    completed_encrypted_blob = receive_chat_frame(frame)

    # 2. Return early if the network layer is still waiting for missing chunks
    if not completed_encrypted_blob:
        return None

    # 3. Complete chunk set recovered! Decrypt and parse JSON envelope structures
    try:
        decrypted_bytes = decrypt_text(completed_encrypted_blob, aes_key)
        chat_message_dict = deserialize_chat_message(decrypted_bytes)

        # -----------------------------------------------------------------
        # PERSISTENCE HOOK: Log the incoming conversation safely to disk
        # -----------------------------------------------------------------
        # chat_message_dict contains: {"sender": "Alice", "payload": "Hello!", "timestamp": ...}
        db_mgr.log_message(
            peer_id=peer_id,
            sender_name=chat_message_dict["sender"],
            message_type="text",
            payload=chat_message_dict["payload"]
        )

        return chat_message_dict

    except Exception as e:
        print(f"[RECEIVE ERROR] Failed decrypting incoming chat payload: {e}")
        return None


# =========================================================================
# 2. INDEPENDENT FILE METADATA PROCESSING PIPELINE
# =========================================================================

def initialize_file_transfer(frame: dict, output_directory: str = DEFAULT_DOWNLOAD_DIR) -> dict:
    """
    Processes Chunk 0 (Plaintext File Metadata Envelope).
    Prepares target path alignments on your filesystem and registers active tracking state pointers.
    """
    # Parse standard structural properties from the raw unencrypted metadata packet block
    session_id, metadata = handle_file_metadata(frame)

    target_filename = metadata["file_name"]

    # CHANGES: Security hardening against path traversal attacks
    # Strip any directory traversal sequences and force a safe basename
    safe_filename = os.path.basename(target_filename).replace("..", "_")
    if not safe_filename:
        safe_filename = f"voidchat_download_{session_id[:8]}"

    destination_path = os.path.join(output_directory, safe_filename)

    # Ensure targeted folders exist safely on disk before parsing data stream bytes
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)

    # Sweep away dirty lingering blocks if a file with the exact same name already exists
    if os.path.exists(destination_path):
        try:
            os.remove(destination_path)
        except Exception as e:
            print(f"[PIPELINE WARNING] Could not remove existing file {destination_path}: {e}")

    # CHANGES: Cache this data structure inside the thread-safe session dictionary
    with TRANSFERS_LOCK:
        ACTIVE_FILE_TRANSFERS[session_id] = {
            "session_id": session_id,
            "file_name": safe_filename,
            "output_path": destination_path,
            "sender_name": metadata["sender"]
        }

    print(
        f"[PIPELINE] File transfer initialized for '{safe_filename}' "
        f"({metadata['file_size']} bytes) [Session: {session_id[:8]}]"
    )
    return metadata


# =========================================================================
# 3. INDEPENDENT FILE DATA STREAM PROCESSING PIPELINE
# =========================================================================

def stream_incoming_file_chunk(frame: dict, aes_key: bytes, peer_id: str, db_mgr):
    """
    Processes sequential encrypted blocks (Chunks 1 to N). Decrypts slices on the fly,
    flushes the binary array data to your storage media, and signs a database record
    the exact moment the full download finishes.
    """
    # CHANGES: Identify the active transfer using the message_id from the frame
    session_id = frame.get("message_id")
    if not session_id:
        return False

    # Safely fetch the active transfer context for this specific session
    with TRANSFERS_LOCK:
        active_transfer = ACTIVE_FILE_TRANSFERS.get(session_id)

    if not active_transfer:
        return False

    # 1. Pipe frame directly into sliding network protocol memory windows
    raw_chunks_generator = receive_file_data_frame(frame)

    # 2. Route generator streams directly through structural decryptor filters
    decrypted_chunks_generator = decrypt_chunks_file(raw_chunks_generator, aes_key)

    # 3. Flush chunk pieces directly to storage without inflating RAM profile
    target_path = active_transfer["output_path"]
    try:
        with open(target_path, "ab") as file_handle:
            for chunk in decrypted_chunks_generator:
                file_handle.write(chunk)
    except Exception as e:
        print(f"[PIPELINE ERROR] Failed writing file chunk to disk: {e}")

        # Clean up the broken transfer state
        with TRANSFERS_LOCK:
            ACTIVE_FILE_TRANSFERS.pop(session_id, None)

        return False

    # 4. Verify whether the internal tracking engine has wrapped up the session
    if active_transfer["session_id"] not in file_streams:
        file_name = active_transfer["file_name"]
        sender_name = active_transfer["sender_name"]

        print(f"[PIPELINE COMPLETE] Singular file download completely closed: '{target_path}' saved.")

        # -----------------------------------------------------------------
        # PERSISTENCE HOOK: Commit download details once fully written
        # -----------------------------------------------------------------
        try:
            db_mgr.log_message(
                peer_id=peer_id,
                sender_name=sender_name,
                message_type="file",
                payload=file_name,
                file_path=target_path
            )
        except Exception as e:
            print(f"[PIPELINE DB ERROR] Failed logging completed file transfer: {e}")

        # CHANGES: Reset tracking pointers safely for this specific session
        with TRANSFERS_LOCK:
            ACTIVE_FILE_TRANSFERS.pop(session_id, None)

        return {
            "status": "complete",
            "file_path": target_path,
            "file_name": file_name,
            "sender_name": sender_name
        }

    # Transfer still actively processing remaining slices...
    return True 