# ==============================================================================
#                               IMPORTS
# ==============================================================================

from collections.abc import Iterable
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from crypto.common import (
    generate_iv,
    validate_aes_key,
    generate_aes_key,
    generate_file_hash,
    verify_file_hash,
)

from crypto.decrypt import (
    decrypt_text,
    decrypt_chunks_file,
)

# ==============================================================================
#                       TEXT ENCRYPTION FUNCTION
# ==============================================================================

def encrypt_text(
    data: bytes,
    aes_key: bytes,
):
    """
    PURPOSE :
        Encrypt a single text/data bytes object.

    INPUT :
        data    : bytes
        aes_key : bytes

    OUTPUT :
        encrypted_data : bytes
    """

    validate_aes_key(aes_key)
    aesgcm = AESGCM(aes_key)
    iv = generate_iv()
    ciphertext = aesgcm.encrypt(iv,data,None,)
    encrypted_data = iv + ciphertext
    return encrypted_data

# ==============================================================================
#                   FILE CHUNK ENCRYPTION FUNCTION
# ==============================================================================

def encrypt_chunks_file(
    raw_chunks: Iterable[bytes],
    aes_key: bytes,
):

    """
    PURPOSE :
        Encrypt file chunks using streaming.

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
        ciphertext = aesgcm.encrypt( iv,chunk,None,)
        encrypted_chunk = iv + ciphertext
        yield encrypted_chunk

# ==============================================================================
#                               SELF TEST
# ==============================================================================

if __name__ == "__main__":

    aes_key = generate_aes_key()

    # ==========================================================================
    #                           TEXT TEST
    # ==========================================================================

    print("\n")
    print("=" * 60)
    print("TEXT ENCRYPTION TEST")
    print("=" * 60)

    original_text = b"Hello VoidChat AES Encryption"

    print("\nORIGINAL TEXT :")
    print(original_text)

    encrypted_text = encrypt_text(
        original_text,
        aes_key,
    )

    print("\nENCRYPTED TEXT :")
    print(encrypted_text)

    decrypted_text = decrypt_text(
        encrypted_text,
        aes_key,
    )

    print("\nDECRYPTED TEXT :")
    print(decrypted_text)

    # ==========================================================================
    #                       FILE CHUNK TEST
    # ==========================================================================

    print("\n")
    print("=" * 60)
    print("FILE CHUNK ENCRYPTION TEST")
    print("=" * 60)

    original_file_chunks = [
        b"Chunk Number 1",
        b"Chunk Number 2",
        b"Chunk Number 3",
        b"Chunk Number 4",
    ]

    print("\nORIGINAL FILE CHUNKS :")

    for chunk in original_file_chunks:
        print(chunk)

    # --------------------------------------------------------------------------
    # FILE HASH
    # --------------------------------------------------------------------------

    original_file_hash = generate_file_hash(
        original_file_chunks,
    )

    print("\nORIGINAL FILE HASH :")
    print(original_file_hash)

    # --------------------------------------------------------------------------
    # ENCRYPT FILE
    # --------------------------------------------------------------------------

    encrypted_chunks = list(
        encrypt_chunks_file(
            original_file_chunks,
            aes_key,
        )
    )

    print("\nENCRYPTED FILE CHUNKS :")

    for chunk in encrypted_chunks:
        print(chunk)

    # --------------------------------------------------------------------------
    # DECRYPT FILE
    # --------------------------------------------------------------------------

    decrypted_chunks = list(
        decrypt_chunks_file(
            encrypted_chunks,
            aes_key,
        )
    )

    print("\nDECRYPTED FILE CHUNKS :")

    for chunk in decrypted_chunks:
        print(chunk)

    # --------------------------------------------------------------------------
    # HASH VERIFICATION
    # --------------------------------------------------------------------------

    verified = verify_file_hash(
        decrypted_chunks,
        original_file_hash,
    )

    print("\nHASH VERIFIED :")
    print(verified)