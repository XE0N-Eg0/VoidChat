


# ==============================================================================
#                               IMPORTS
# ==============================================================================

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from crypto.common import (
    generate_iv,
    validate_aes_key,
    generate_aes_key,
)


# ==============================================================================
#                   FILE CHUNK ENCRYPTION FUNCTION
# ==============================================================================

def encrypt_file_chunks(
    file_chunks,
    aes_key
):

    """
    PURPOSE :
        Encrypt all chunks of a file.

    INPUT :
        file_chunks : list[bytes]
        aes_key     : bytes

    OUTPUT :
        encrypted_file_chunks : list[bytes]
    """


    validate_aes_key(aes_key)

    aesgcm = AESGCM(aes_key)

    encrypted_file_chunks = []



    for chunk in file_chunks:
        iv = generate_iv()    #this generates iv for each chunk 

        ciphertext = aesgcm.encrypt(iv,chunk,None,)

        encrypted_chunk = (iv + ciphertext )

        encrypted_file_chunks.append(encrypted_chunk)

    return encrypted_file_chunks


# ==============================================================================
#                               SELF TEST
# ==============================================================================

if __name__ == "__main__":


    from crypto.decrypt import decrypt_file_chunks


    file_chunks = [    # this list contains chunk for encryption
        b"Hello",
        b"VoidChat",
        b"AES Encryption",
        b"Chunk Number 4",
    ]
    aes_key = generate_aes_key()  # this is the key

    print("\n")
    print("=" * 60)
    print("ORIGINAL FILE CHUNKS")
    print("=" * 60)

    for chunk in file_chunks:
        print(chunk)

    encrypted_chunks = encrypt_file_chunks(file_chunks,aes_key )


    print("\n")
    print("=" * 60)
    print("ENCRYPTED FILE CHUNKS")
    print("=" * 60)

    for chunk in encrypted_chunks:

        print(chunk)


    decrypted_chunks = decrypt_file_chunks(encrypted_chunks,aes_key)

    print("\n")
    print("=" * 60)
    print("DECRYPTED FILE CHUNKS")
    print("=" * 60)

    for chunk in decrypted_chunks:

        print(chunk)


    print("\n")
    print("=" * 60)

    print("VALIDATION")

    print("=" * 60)

    if file_chunks == decrypted_chunks:

        print("SUCCESS")

        print("Encryption & Decryption Working Properly")

    else:

        print("FAILED")