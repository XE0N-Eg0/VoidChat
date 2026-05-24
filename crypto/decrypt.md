# decrypt.py Architecture Audit

This audit evaluates the current and future state of:

```python
crypto/decrypt.py
```

in relation to:

```python
crypto/encrypt.py
```

under the NEW VoidChat networking architecture.

The goal is to ensure:

* clean crypto separation
* proper complement symmetry
* streaming-safe file decryption
* correct text decryption model
* protocol independence
* future scalability

---

# CURRENT ARCHITECTURE SUMMARY

Your current architecture is now:

---

# TEXT MODEL

## Sender Side

```text id="2ybx4v"
metadata
→ serialize
→ encrypt WHOLE payload
→ chunk encrypted blob
→ frame
```

## Receiver Side

```text id="34x1n8"
de-frame
→ reassemble encrypted blob
→ decrypt ONCE
→ deserialize
→ parse metadata
```

Meaning:

* text is encrypted once
* chunking happens AFTER encryption
* decrypt.py must decrypt ONE FULL BLOB

---

# FILE MODEL

## Sender Side

```text id="vdjlwm"
metadata
→ serialize metadata
→ chunk raw file
→ encrypt EACH chunk
→ frame
```

## Receiver Side

```text id="8vj3zd"
de-frame
→ receiver validates chunk state
→ decrypt ONE chunk
→ receiver writes chunk
→ repeat
```

Meaning:

* each file chunk is independently encrypted
* decrypt.py must support streaming chunk decryption
* NO giant RAM reconstruction

---

# CURRENT encrypt.py AUDIT

Current encrypt.py contains:

---

# FUNCTION 1

```python id="mbz4ah"
encrypt_chunks_list()
```

Current Purpose:

* encrypt list of chunks

Current State:
❌ OUTDATED FOR TEXT

Reason:

* old architecture encrypted EACH text chunk independently
* new architecture encrypts WHOLE message before chunking

Meaning:

* this function no longer matches text pipeline
* naming is misleading
* architecture no longer uses this logic

---

# FUNCTION 2

```python id="kyr0ru"
encrypt_chunks_file()
```

Current Purpose:

* streaming file encryption generator

Current State:
✔ CORRECT

Reason:

* file architecture still encrypts chunk-by-chunk
* generator streaming is correct
* memory-safe
* scalable

This function aligns with final architecture.

---

# REQUIRED decrypt.py DESIGN

decrypt.py must become the EXACT COMPLEMENT of encrypt.py.

---

# REQUIRED FINAL FUNCTIONS

---

# 1. TEXT DECRYPTION FUNCTION

---

## REQUIRED FUNCTION

```python id="hvvqrb"
decrypt_message_blob(
    encrypted_blob: bytes,
    aes_key: bytes
) -> bytes
```

---

## PURPOSE

Decrypt ONE fully reconstructed encrypted text blob.

This is the exact opposite of:

```python id="0s4rbw"
encrypt_message_blob()
```

---

## INPUT

```python id="5e4x1y"
encrypted_blob : bytes
aes_key        : bytes
```

---

## OUTPUT

```python id="93e38n"
serialized_plaintext : bytes
```

---

## REQUIRED INTERNAL LOGIC

### Step 1 — Validate AES Key

```python id="ajcrb7"
validate_aes_key(aes_key)
```

---

### Step 2 — Extract IV

Your encryption format is:

```python id="c0x1to"
encrypted_blob = iv + ciphertext
```

So decrypt must reverse it:

```python id="uyz5l4"
iv = encrypted_blob[:12]
ciphertext = encrypted_blob[12:]
```

---

### Step 3 — AESGCM Decrypt

```python id="yhfbdq"
plaintext = aesgcm.decrypt(
    iv,
    ciphertext,
    None
)
```

---

### Step 4 — Return Plaintext

```python id="n7d5mk"
return plaintext
```

---

# IMPORTANT DESIGN NOTE

This function must ONLY:

* decrypt bytes
* return bytes

It must NEVER:

* deserialize
* parse metadata
* validate packets
* know about transport
* know about files/messages

decrypt.py must remain PURE CRYPTO.

---

# 2. FILE DECRYPTION FUNCTION

---

## REQUIRED FUNCTION

```python id="pb4e3g"
decrypt_file_chunks(
    encrypted_chunks: Iterable[bytes],
    aes_key: bytes
)
```

---

## PURPOSE

Streaming chunk-by-chunk file decryption.

Complement to:

```python id="lff2vp"
encrypt_chunks_file()
```

---

## INPUT

```python id="jgr8c5"
encrypted_chunks : Iterable[bytes]
aes_key          : bytes
```

---

## OUTPUT

```python id="vwmrba"
yield plaintext_chunk
```

Generator output.

---

# REQUIRED INTERNAL LOGIC

---

## Step 1 — Validate AES Key

```python id="72sk5m"
validate_aes_key(aes_key)
```

---

## Step 2 — Create AESGCM Instance

```python id="ehjlwm"
aesgcm = AESGCM(aes_key)
```

---

## Step 3 — Iterate Chunks

```python id="poc1ae"
for encrypted_chunk in encrypted_chunks:
```

---

## Step 4 — Extract IV

```python id="f3ixk8"
iv = encrypted_chunk[:12]
ciphertext = encrypted_chunk[12:]
```

---

## Step 5 — Decrypt

```python id="azm4qf"
plaintext_chunk = aesgcm.decrypt(
    iv,
    ciphertext,
    None
)
```

---

## Step 6 — Yield Plaintext

```python id="rljlwm"
yield plaintext_chunk
```

---

# REQUIRED FUNCTION CHANGES

---

# REMOVE

## REMOVE THIS FUNCTION

```python id="t9yzy5"
decrypt_chunks_list()
```

---

## WHY REMOVE IT

This function belongs to OLD architecture:

```text id="jjlwm"
chunk
→ encrypt EACH chunk
```

for text messages.

But new architecture is:

```text id="9zvtjlwm"
encrypt WHOLE message
→ chunk encrypted blob
```

Meaning:

* text chunks are NOT individually encrypted anymore
* decrypting chunk-by-chunk is now incorrect for text

This function is now architecturally invalid.

---

# RENAME RECOMMENDATIONS

Current naming has ambiguity.

Recommended improvements:

---

# TEXT SIDE

---

## OLD

```python id="7jlwm"
encrypt_chunks_list()
```

---

## REPLACE WITH

```python id="jlwm8"
encrypt_message_blob()
```

Reason:

* clearer meaning
* reflects full-message encryption
* matches receiver architecture

---

## REQUIRED COMPLEMENT

```python id="jlwm9"
decrypt_message_blob()
```

---

# FILE SIDE

---

## OLD

```python id="jlwm10"
encrypt_chunks_file()
```

---

## SUGGESTED RENAME

```python id="jlwm11"
encrypt_file_chunks()
```

Reason:

* more natural naming
* clearer grammar
* symmetric with decrypt

---

## REQUIRED COMPLEMENT

```python id="jlwm12"
decrypt_file_chunks()
```

---

# FINAL RECOMMENDED decrypt.py STRUCTURE

---

# IMPORTS

```python id="jlwm13"
from collections.abc import Iterable
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
```

---

# LOCAL IMPORTS

```python id="jlwm14"
from crypto.common import validate_aes_key
```

---

# TEXT FUNCTION

```python id="jlwm15"
decrypt_message_blob()
```

Purpose:

* decrypt one full text message blob

---

# FILE FUNCTION

```python id="jlwm16"
decrypt_file_chunks()
```

Purpose:

* streaming file decryptor

---

# THINGS decrypt.py MUST NEVER DO

decrypt.py must NEVER:

❌ deserialize JSON
❌ parse metadata
❌ track packet IDs
❌ know chunk indexes
❌ manage sockets
❌ reorder sequences
❌ know transport headers
❌ write files
❌ manage state

It must remain:

```text id="jlwm17"
bytes in
→ bytes out
```

ONLY.

---

# FINAL ARCHITECTURE ALIGNMENT

After modifications:

| encrypt.py           | decrypt.py           |
| -------------------- | -------------------- |
| encrypt_message_blob | decrypt_message_blob |
| encrypt_file_chunks  | decrypt_file_chunks  |

This creates perfect symmetry.

---

# FINAL RECOMMENDED LOGIC FLOW

# TEXT

## Sender

```text id="jlwm18"
serialize
→ encrypt_message_blob
→ chunk encrypted blob
```

## Receiver

```text id="jlwm19"
reassemble encrypted blob
→ decrypt_message_blob
→ deserialize
```

---

# FILES

## Sender

```text id="jlwm20"
chunk raw file
→ encrypt_file_chunks
```

## Receiver

```text id="jlwm21"
receiver validates chunk
→ decrypt_file_chunks
→ receiver writes chunk
```

---

# FINAL VERDICT

# KEEP

✔ AESGCM usage
✔ IV-per-chunk/file design
✔ generator-based file streaming
✔ validate_aes_key() logic

---

# REMOVE

❌ decrypt_chunks_list()
❌ old text chunk decryption model

---

# ADD

✔ decrypt_message_blob()
✔ decrypt_file_chunks()
✔ proper naming symmetry

---

# MOST IMPORTANT CHANGE

Your crypto layer must now recognize:

# TEXT = BLOB ENCRYPTION

while

# FILES = STREAM ENCRYPTION

That is the foundational architectural split of the new VoidChat protocol stack.
