transport emits raw frame
→ receiver stores encrypted chunks
→ reconstruct encrypted blob
→ decrypt blob
→ deserialize JSON
→ application message


transport emits raw frame
→ receiver orders chunks
→ decrypt chunk
→ write chunk to disk


decrypt_chat_message(encrypted_blob: bytes,aes_key: bytes) -> bytes
input: encrypted bytes & key
output : decrypted bytes 

validate key

extract iv
extract ciphertext

decrypt ciphertext

return original_serialized_message / bytes

decrypt_file_chunks(
    encrypted_chunks: Iterable[bytes],
    aes_key: bytes
)
    -> Generator[bytes, None, None]

input: envrypted chunks
ouput decrypted chunks (yeild)

validate key

for encrypted_chunk in encrypted_chunks:

    extract iv

    extract ciphertext

    decrypt chunk

    yield decrypted_chunk