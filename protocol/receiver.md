CHAT flow

create_chat_packet()
→ serialize_message()
→ encrypt()
→ chunk_encrypted_message()
→ transport.send_chat_frame()

transport emits frame
→ receiver stores encrypted chunk
→ receiver sorts chunks
→ receiver reconstructs encrypted blob
→ receiver returns encrypted complete message
→ decrypt module decrypts
→ deserialize
→ application

file flow
create_file_packet()
→ serialize metadata
→ send metadata
→ chunk_generator()
→ encrypt_chunks_file()
→ transport.send_file_chunk_frame()


transport emits raw frame
→ receiver stores chunk temporarily
→ receiver releases next expected sequence
→ decrypt module decrypts chunk
→ disk writer writes chunk


WHAT RECEIVER SHOULD OWN FOR CHAT

chat_buffer = {
    packet_id: {
        "chunks": {},
        "final_sequence": int | None,
        "received_count": int,
        "created_at": float,
    }
}

fucntions:
receive_chat_frame(frame: dict)
INPUT:
{
    peer_ip,
    packet_id,
    sequence,
    final,
    payload
}

OUTPUT:
none / payload joined together

WHAT RECEIVER SHOULD OWN FOR FILE

file_streams = {
    packet_id: {
        "expected_sequence": 0,
        "pending_chunks": {},
        "final_sequence": None,
        "created_at": ...
    }
}


receive_file_frame(frame: dict):
INPUT:
{
    packet_id,
    sequence,
    final,
    payload
}

while expected_sequence exists:
    yield chunk
    expected_sequence += 1

OUTPUT: Iterable[bytes] / yield encrypted_chunk

---

RECONSTRUCTION:
CHAT

reconstruct_chat_message(packet_id: str) -> bytes
INPUT : packet_id

    chat_buffers[packet_id]
    ordered = []

    for seq in sorted(chunks):
        ordered.append(chunks[seq])

    encrypted_blob = b"".join(ordered)

    return encrypted_blob

OUTPUT: encrypted_blob: bytes


write_stream_to_file(decrypted_chunks,output_path)
INPUT: Decrypted CHUNKS

append to file

OUTPUT: Final PATH OF FILE

create metadata dict
→ serialize metadata
→ encrypt metadata
→ send as special FILE_METADATA frame

receive frame
→ detect FILE_METADATA flag
→ decrypt
→ deserialize
→ initialize file transfer session


FLAG_FINAL_CHUNK = 0x01
FLAG_CHAT_DATA = 0x02
FLAG_FILE_METADATA = 0x04
FLAG_FILE_DATA = 0x08


deserialize_chat_message(serialized_message: bytes) -> dict
INPUT: bytes

json_data = serialized_message.decode("utf-8")

message_dict = json.loads(json_data)

return message_dict


OUTPUT: DICT
{
    "type": "chat",
    "sender": "Alice",
    "payload": "Hello"
}

deserialize_file_metadata(serialized_metadata: bytes) -> dict
INPUT: BYTES
OUPUT: DICT

{
    "type": "file_transfer_init",
    "file_name": "abc.mp4",
    "file_size": 12345,
}

extract_file_metadata(metadata_packet: dict) -> dict
input: dict by serealise 
output: Dict 

extract_file_metadata(
    metadata_packet: dict
) -> dict


