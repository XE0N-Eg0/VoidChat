# Audit Report — `receiver.py`

Your `receiver.py` is currently the most architecturally outdated part of the protocol layer.

The good news is:

* the core ideas are already correct
* chunk storage logic already exists
* reconstruction logic already exists
* cleanup architecture already exists

The problem is:

```
receiver.py still assumes the OLD text architecture
```

and:

```
file receive architecture does not exist yet
```

Right now the file behaves like:

```
OLD MESSAGE REASSEMBLER
```

But after the redesign, it must become:

```
PROTOCOL RECONSTRUCTION + TRANSFER STATE LAYER
```

This audit explains:

1. What each current function does
2. Whether it matches the NEW architecture
3. What should:

   * stay
   * change
   * be removed
   * be split
4. What NEW functions are required
5. How receiver.py should coordinate:

   * text reconstruction
   * file streaming
   * decrypt.py interaction
   * protocol state ownership

---

# Current Role of `receiver.py`

After the redesign, `receiver.py` should become:

```
PROTOCOL RECEIVE + RECONSTRUCTION LAYER
```

It should ONLY handle:

```
1. Chunk storage
2. Sequence tracking
3. Reassembly
4. Transfer state
5. Deserialization
6. Metadata parsing
7. File transfer coordination
8. Cleanup
```

It should NEVER:

❌ decrypt internally
❌ frame packets
❌ read sockets
❌ manage transport
❌ perform AES logic

That belongs to:

```
transport.py
decrypt.py
```

---

# CURRENT ARCHITECTURE PROBLEM

Current receiver.py assumes:

```
plaintext serialized chunks
```

But new architecture is:

# TEXT

```
encrypted chunks
→ reassemble encrypted blob
→ decrypt ONCE
→ deserialize
```

# FILES

```
encrypted chunk
→ decrypt chunk
→ write chunk
```

This is the MOST IMPORTANT architectural change.

---

# CURRENT FUNCTION AUDIT

---

# 1. `deserialize_message()`

```python
def deserialize_message(data: bytes) -> dict:
```

---

# CURRENT PURPOSE

Converts:

```
bytes → JSON → dict
```

---

# ARCHITECTURAL STATUS

✅ CORRECT
✅ REQUIRED
✅ GOOD RESPONSIBILITY

Deserialization belongs here.

NOT in decrypt.py.

---

# WHY THIS FUNCTION IS IMPORTANT

This becomes the canonical:

```
network payload → protocol object
```

conversion layer.

It will eventually support:

* chat messages
* system events
* file metadata
* AV negotiation packets

Good placement.

---

# WHAT SHOULD CHANGE

Current implementation:

```python
json.loads(data.decode())
```

is acceptable.

No major architectural changes needed.

---

# FUTURE RECOMMENDATION

Eventually support:

```
JSON
MessagePack
Protobuf
```

through abstraction.

But not now.

---

# FINAL VERDICT

```
KEEP
Correctly placed
Good function
```

---

# 2. `validate_packet()`

```python
def validate_packet(packet: dict) -> bool:
```

---

# CURRENT PURPOSE

Checks:

```python
required_fields = ["type"]
```

---

# ARCHITECTURAL STATUS

⚠ PARTIALLY CORRECT

Validation belongs here.

BUT:

Current validation is far too weak.

---

# CURRENT PROBLEM

Only validating:

```python
"type"
```

is not sufficient anymore.

Different packet types now require different schemas.

---

# REQUIRED REDESIGN

Validation must become:

```
packet-type aware
```

---

# RECOMMENDED STRUCTURE

Replace with:

```python
validate_chat_packet()
validate_chunk_packet()
validate_file_metadata()
```

OR:

```python
validate_packet(packet, expected_type)
```

---

# WHY THIS IS IMPORTANT

Receiver now owns:

* protocol correctness
* reconstruction safety
* metadata integrity

This validation layer becomes critical.

---

# FINAL VERDICT

```
KEEP
But heavily refactor
Needs type-aware validation
```

---

# 3. `cleanup_expired_chunks()`

```python
def cleanup_expired_chunks()
```

---

# CURRENT PURPOSE

Removes expired incomplete transfers.

---

# ARCHITECTURAL STATUS

✅ VERY IMPORTANT
✅ REQUIRED
✅ FUTURE-PROOF

This is good architecture.

---

# WHY THIS FUNCTION IS IMPORTANT

Without cleanup:

* abandoned transfers leak RAM
* dead peers accumulate state
* incomplete messages never disappear

This becomes EVEN MORE important for:

* file transfers
* resumable uploads
* AV streams

---

# CURRENT PROBLEM

Currently only cleans:

```python
chunk_storage
```

But future architecture needs:

```python
text_transfer_storage
file_transfer_storage
```

---

# REQUIRED REDESIGN

Cleanup must support BOTH:

# TEXT STORAGE

```python
text_transfer_storage
```

# FILE STORAGE

```python
file_transfer_storage
```

---

# REQUIRED ADDITIONS

For file cleanup:

* close dangling file handles
* delete incomplete temp files
* cleanup transfer metadata

---

# FINAL VERDICT

```
KEEP
Expand for file transfer lifecycle
```

---

# 4. `process_packet()`

```python
def process_packet(packet: dict)
```

---

# CURRENT PURPOSE

Routes packet types.

---

# ARCHITECTURAL STATUS

⚠ OUTDATED

Current logic assumes:

```
plaintext packet arrives directly
```

But transport now emits:

```
encrypted framed payloads
```

Receiver must now operate BEFORE plaintext exists.

---

# CURRENT PROBLEM

Current flow:

```
process_packet()
→ process_chunk()
→ reconstruct_message()
→ deserialize
```

assumes chunks already contain plaintext.

That is now wrong.

---

# REQUIRED REDESIGN

This function must become:

```
HIGH-LEVEL PROTOCOL ROUTER
```

---

# RECOMMENDED STRUCTURE

```python
process_frame(frame)
```

instead of:

```python
process_packet(packet)
```

because transport now emits:

```python
{
    "packet_id": "...",
    "sequence": 0,
    "final": False,
    "payload": encrypted_bytes
}
```

NOT plaintext packets.

---

# REQUIRED ROUTING

Receiver should now route by:

```python
frame["channel"]
```

Example:

```python
if frame["channel"] == "txt":
    handle_text_frame(frame)

elif frame["channel"] == "file":
    handle_file_frame(frame)
```

---

# WHY THIS IS IMPORTANT

Receiver is now:

```
transport-aware
```

NOT:

```
plaintext-packet-aware
```

Huge architectural shift.

---

# FINAL VERDICT

```
REMOVE CURRENT LOGIC
Replace with frame-based routing
```

---

# 5. `process_chunk()`

```python
def process_chunk(packet: dict)
```

---

# CURRENT PURPOSE

Stores message chunks.

---

# CURRENT ARCHITECTURE ASSUMPTION

Assumes:

```python
payload == plaintext serialized bytes
```

This is no longer true.

---

# CURRENT PROBLEM

Text chunks are now:

```
pieces of encrypted blob
```

NOT plaintext chunks.

---

# REQUIRED REDESIGN

This function must become:

```python
store_text_chunk()
```

---

# REQUIRED PURPOSE

ONLY:

* store encrypted chunks
* track sequences
* detect completion

NOT deserialize.

---

# REQUIRED NEW FUNCTION

```python
def store_text_chunk(
    packet_id: str,
    sequence: int,
    payload: bytes,
    final: bool
)
```

---

# REQUIRED STORAGE STRUCTURE

```python
text_transfer_storage = {
    packet_id: {
        "chunks": {},
        "received_sequences": set(),
        "final_sequence": int | None,
        "created_at": float,
    }
}
```

---

# WHY THIS STRUCTURE IS IMPORTANT

Supports future:

* retransmission
* duplicate detection
* resumability
* integrity validation

---

# FINAL VERDICT

```
REMOVE CURRENT FUNCTION
Replace with encrypted chunk storage logic
```

---

# 6. `reconstruct_message()`

```python
def reconstruct_message(message_id: str)
```

---

# CURRENT PURPOSE

Joins chunks into one payload.

---

# ARCHITECTURAL STATUS

⚠ PARTIALLY CORRECT

The REASSEMBLY idea is correct.

BUT:

Current reconstruction assumes:

```
joined bytes == plaintext serialized message
```

That is no longer true.

---

# REQUIRED NEW FLOW

New text flow:

```
join encrypted chunks
→ decrypt blob
→ deserialize plaintext
```

NOT:

```
join plaintext chunks
→ deserialize directly
```

---

# REQUIRED REDESIGN

Function should become:

```python
reassemble_text_payload()
```

---

# REQUIRED PURPOSE

ONLY:

```
encrypted chunks
→ encrypted blob
```

NOT deserialization.

---

# REQUIRED FUNCTION

```python
def reassemble_text_payload(
    packet_id: str
) -> bytes:
```

---

# REQUIRED INTERNAL LOGIC

## Step 1 — Retrieve Stored Chunks

```python
storage = text_transfer_storage[packet_id]
```

---

## Step 2 — Order By Sequence

```python
sorted(chunks.keys())
```

---

## Step 3 — Join

```python
encrypted_blob = b"".join(...)
```

---

## Step 4 — Return Blob

```python
return encrypted_blob
```

---

# VERY IMPORTANT

This function must NOT:

❌ decrypt
❌ deserialize
❌ parse metadata

Only reconstruct encrypted bytes.

---

# FINAL VERDICT

```
KEEP IDEA
Completely redesign logic
```

---

# REQUIRED NEW FUNCTIONS

---

# TEXT RECEIVE FUNCTIONS

---

# 1. `process_frame()`

```python
def process_frame(frame: dict)
```

---

# PURPOSE

Main protocol entrypoint from transport.py.

Routes frames by:

```python
frame["channel"]
```

---

# INPUT

Raw transport frame:

```python
{
    "channel": "txt",
    "packet_id": "...",
    "sequence": 0,
    "final": False,
    "payload": b"..."
}
```

---

# OUTPUT

Dispatches internally.

---

# 2. `handle_text_frame()`

```python
def handle_text_frame(frame: dict)
```

---

# PURPOSE

Coordinates text receive lifecycle.

---

# REQUIRED FLOW

```
store encrypted chunk
→ detect completion
→ reconstruct encrypted blob
→ send blob to decrypt.py
→ deserialize plaintext
→ parse metadata
```

---

# OUTPUT

Final message dict.

---

# 3. `is_text_transfer_complete()`

```python
def is_text_transfer_complete(
    packet_id: str
) -> bool
```

---

# PURPOSE

Checks:

* all sequences received
* final chunk known

---

# REQUIRED LOGIC

```python
len(received_sequences)
==
final_sequence + 1
```

---

# 4. `parse_chat_message()`

```python
def parse_chat_message(
    message: dict
)
```

---

# PURPOSE

Extract:

* sender
* payload
* timestamp
* message_id

This separates protocol parsing from deserialization.

---

# FILE RECEIVE FUNCTIONS

---

# 5. `handle_file_frame()`

```python
def handle_file_frame(frame: dict)
```

---

# PURPOSE

Coordinates file receive lifecycle.

---

# REQUIRED FLOW

```
validate sequence
→ pass encrypted chunk to decrypt.py
→ receive plaintext chunk
→ write chunk
→ update transfer state
```

---

# IMPORTANT

Receiver owns:

* transfer state
* ordering
* lifecycle

decrypt.py owns ONLY:

* bytes → bytes

---

# 6. `initialize_file_transfer()`

```python
def initialize_file_transfer(
    metadata: dict
)
```

---

# PURPOSE

Prepare:

* file handle
* transfer storage
* temp file
* metadata tracking

---

# REQUIRED STORAGE STRUCTURE

```python
file_transfer_storage = {
    packet_id: {
        "file_handle": file,
        "received_sequences": set(),
        "metadata": {},
        "created_at": time.time(),
    }
}
```

---

# 7. `write_file_chunk()`

```python
def write_file_chunk(
    packet_id: str,
    plaintext_chunk: bytes
)
```

---

# PURPOSE

Append directly to disk.

---

# VERY IMPORTANT

This replaces:

```
RAM reconstruction
```

with:

```
filesystem streaming reconstruction
```

Huge architectural improvement.

---

# 8. `finalize_file_transfer()`

```python
def finalize_file_transfer(
    packet_id: str
)
```

---

# PURPOSE

Finalize transfer:

* close file
* verify size
* cleanup state
* rename temp file

---

# THINGS receiver.py SHOULD NEVER DO

receiver.py must NEVER:

❌ perform AES logic
❌ manage sockets
❌ frame packets
❌ parse TCP streams
❌ generate IVs
❌ know crypto internals

That belongs to:

```
transport.py
decrypt.py
```

---

# FINAL RECEIVE ARCHITECTURE

# TEXT

```
transport.py
→ de-frame

receiver.py
→ store encrypted chunks
→ reconstruct encrypted blob

decrypt.py
→ decrypt_message_blob()

receiver.py
→ deserialize
→ parse metadata
→ emit message
```

---

# FILES

```
transport.py
→ de-frame

receiver.py
→ validate transfer state

decrypt.py
→ decrypt_file_chunks()

receiver.py
→ write plaintext chunk
→ finalize transfer
```

---

# OVERALL AUDIT RESULT

| Component                  | Verdict          |
| -------------------------- | ---------------- |
| `deserialize_message()`    | KEEP             |
| `validate_packet()`        | REFACTOR         |
| `cleanup_expired_chunks()` | KEEP + EXPAND    |
| `process_packet()`         | REMOVE           |
| `process_chunk()`          | REMOVE           |
| `reconstruct_message()`    | REFACTOR HEAVILY |

---

# FINAL ARCHITECTURAL SCORE

Your protocol architecture is now evolving correctly toward:

```
transport layer
↓
protocol reconstruction layer
↓
crypto layer
↓
application layer
```

The biggest improvement was realizing:

```
receiver.py owns protocol state
```

while:

```
decrypt.py owns only byte transformation
```

That is the correct layered networking architecture.
