# protocol/receiver.py
#TODO: VISUAL CLEANING OF CODE
# ================= RESPONSIBILITIES ======================
# 1. Maintain memory reassembly buffers for incomplete text chats
# 2. Maintain sequential window streaming pipelines for files
# 3. Handle chunk_index 0 vs raw data transitions cleanly
# 4. Remain completely stateless regarding I/O and Cryptography
# =========================================================

import os
import json
import time
from typing import Dict, Optional, Tuple, Generator

# =========================================================
# CONFIGURATION BOUNDS
# =========================================================
CHUNK_TIMEOUT = 60.0  # Seconds before incomplete transfers are abandoned

# In-memory allocation map for text chat frame gathering
# Format: message_id -> {"chunks": {chunk_index: bytes}, "total_chunks": int, "created_at": float}
chat_buffers: Dict[str, dict] = {}

# In-memory state tracking window for sequential file blocks
# Format: message_id -> {"next_expected_index": int, "total_chunks": int, "window_buffer": {chunk_index: bytes}, "created_at": float}
file_streams: Dict[str, dict] = {}


# =========================================================
# 1. TEXT CHAT REASSEMBLY PIPELINE
# =========================================================

def receive_chat_frame(frame: dict) -> Optional[bytes]:
    """
    Assembles scattered incoming text frames.
    Returns a unified bytes block ONLY when all fragments have been received.
    """
    msg_id = frame["message_id"] #also the session id in uppder layers 
    chunk_idx = frame["chunk_index"]
    total_chunks = frame["total_chunks"]  
    payload = frame["payload"] # the main chunk 

    # Initialize tracking allocation if this is the first slice seen
    if msg_id not in chat_buffers:
        chat_buffers[msg_id] = {
            "chunks": {},
            "total_chunks": total_chunks,
            "created_at": time.time()
        }

    buffer = chat_buffers[msg_id]
    buffer["chunks"][chunk_idx] = payload

    
    if len(buffer["chunks"]) == buffer["total_chunks"]:
        # Piece the block together in strict mathematical index order
        ordered_parts = [buffer["chunks"][i] for i in range(buffer["total_chunks"])] #the worst pythonic way to say pick the correct block form buffer though indexing
        complete_encrypted_block = b"".join(ordered_parts)
        
        # Purge resource allocation instantly
        del chat_buffers[msg_id] # prevents the overflow or OOM errors (if any would like to occur)
        return complete_encrypted_block

    return None


def deserialize_chat_message(decrypted_bytes: bytes) -> dict:
    """Helper utility to unpack JSON chat dict strings after decryption."""
    return json.loads(decrypted_bytes.decode("utf-8")) #just encoded message


# =========================================================
# 2. FILE TRANSFERS & STREAMING LOGIC
# =========================================================

def handle_file_metadata(frame: dict) -> Tuple[str, dict]:
    """
    Processes file chunk_index 0.
    Unpacks file configuration metadata and initializes a sequential stream.
    
    OUTPUT:
        Tuple[message_id, metadata_dict]
    """
    message_id = frame["message_id"]
    total_chunks = frame["total_chunks"]
    payload = frame["payload"]  # Metadata payload is handled at upper pipeline layers 

    # Chunk 0 payload is always a serialized JSON string containing file specs
    metadata = json.loads(payload.decode("utf-8")) 

    #NOTE: For now we dont encrypting the metadata that means anyone can sniff and see the file metadata

    # Initialize sliding tracking window state
    # NOTE: 'next_expected_index' is set to 1, because chunk 0 was metadata (so we techinally start form 1->END OF FILE)
    file_streams[message_id] = {
        "next_expected_index": 1,
        "total_chunks": total_chunks,  # NOTE: Cached to manage clean pipeline teardown bounds
        "window_buffer": {},
        "created_at": time.time()
    }

    return message_id, metadata #this returns both 


def receive_file_data_frame(frame: dict) -> Generator[bytes, None, None]:
    """
    A lazy sliding-window chunk collector. 
    Accepts file data frames (indexes 1 to N), caches out-of-order chunks, 
    and yields them in absolute sequential order as soon as gaps close.
    """
    message_id = frame["message_id"]
    chunk_idx = frame["chunk_index"]
    payload = frame["payload"]

    #NOTE: If chunk 0 never initialized this stream layout, drop it
    if message_id not in file_streams:
        print(f"[RECEIVER WARNING] Dropping orphaned file frame for session {message_id}")
        return

    stream = file_streams[message_id]
    
    # Store chunk inside out-of-order map cache
    stream["window_buffer"][chunk_idx] = payload

    # Yield all consecutive matching chunks ready in the queue line
    while stream["next_expected_index"] in stream["window_buffer"]:
        current_idx = stream["next_expected_index"]
        chunk_data = stream["window_buffer"].pop(current_idx)
        
        yield chunk_data
        
        stream["next_expected_index"] += 1
        
        # NOTE: Teardown logic relies purely on checking if the counter has hit the calculated total size.
        # This prevents dropped packet frames or out-of-order arrivals from prematurely breaking the socket handler.
        if stream["next_expected_index"] == stream["total_chunks"]:
            del file_streams[message_id]
            return


# =========================================================
# 3. HOUSEKEEPING & MEMORY MANAGEMENT
# =========================================================

def cleanup_expired_buffers(): #NOTE: THIS FUCNTION WAS GENERATED THROUGH AI SO I DONT GET THE BLAME FOR IT
    now = time.time()

    dead_chats = [k for k, v in chat_buffers.items() if now - v["created_at"] > CHUNK_TIMEOUT]
    for k in dead_chats:
        del chat_buffers[k]

    dead_files = [k for k, v in file_streams.items() if now - v["created_at"] > CHUNK_TIMEOUT]
    for k in dead_files:
        del file_streams[k]