


# ==============================================================================
#                               IMPORTS
# ==============================================================================
from collections.abc import Iterable
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from crypto.common import (
    generate_iv,
    validate_aes_key,
    generate_aes_key,
)


# ==============================================================================
#                   TEXT   ENCRYPTION FUNCTION
# ==============================================================================

def encrypt_chunks_list(
    file_chunks:list[bytes],
    aes_key:bytes
):

    """
    PURPOSE :
        Encrypt all chunks of a file.

    INPUT :
        file_chunks : list[bytes]
        aes_key     : bytes

    OUTPUT :
        encrypted_chunks_list : list[bytes]
    """


    validate_aes_key(aes_key)

    aesgcm = AESGCM(aes_key)

    encrypted_chunks_list = []



    for chunk in file_chunks:
        iv = generate_iv()    #this generates iv for each chunk 

        ciphertext = aesgcm.encrypt(iv,chunk,None,)

        encrypted_chunk = (iv + ciphertext )

        encrypted_chunks_list.append(encrypted_chunk)

    return encrypted_chunks_list


# ==============================================================================
#                   FILE CHUNK  ENCRYPTION FUNCTION
# ==============================================================================
def encrypt_chunks_file(
    raw_chunks: Iterable[bytes],
    aes_key: bytes
):
    """
    PURPOSE :
        Encrypt file chunks using generator streaming.
    INPUT :
        raw_chunks : Iterable[bytes]
        aes_key    : bytes
    OUTPUT :
        yield encrypted_chunk
    """
    validate_aes_key(aes_key)
    aesgcm = AESGCM(aes_key)
    for chunk in raw_chunks:
        iv = generate_iv()
        ciphertext = aesgcm.encrypt( iv, chunk, None, )
        encrypted_chunk = ( iv +  ciphertext )
        yield encrypted_chunk

# ==============================================================================
#                               SELF TEST
# ==============================================================================

if __name__ == "__main__":

    from crypto.decrypt import decrypt_chunks_list


    file_chunks = [

        b"Hello",

        b"VoidChat",

        b"AES Encryption",

        b"Chunk Number 4",
    ]


    aes_key = generate_aes_key()


    print("\n")
    print("=" * 60)
    print("ORIGINAL FILE CHUNKS")
    print("=" * 60)

    for chunk in file_chunks:

        print(chunk)


    encrypted_chunks = encrypt_chunks_list(

        file_chunks,

        aes_key
    )


    print("\n")
    print("=" * 60)
    print("ENCRYPTED FILE CHUNKS")
    print("=" * 60)

    for chunk in encrypted_chunks:

        print(chunk)


    decrypted_chunks = decrypt_chunks_list(

        encrypted_chunks,

        aes_key
    )


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