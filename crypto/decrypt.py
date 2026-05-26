# ==============================================================================
#                               IMPORTS
# ==============================================================================

from collections.abc import Iterable
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from crypto.common import (
    validate_aes_key,
    IV_SIZE,
)

# ==============================================================================
#                       TEXT DECRYPTION FUNCTION
# ==============================================================================

def decrypt_text(
    encrypted_data: bytes,
    aes_key: bytes,
):

    """
    PURPOSE :
        Decrypt encrypted text/data.

    INPUT :
        encrypted_data : bytes
        aes_key        : bytes

    OUTPUT :
        original_data : bytes
    """

    validate_aes_key(aes_key)
    aesgcm = AESGCM(aes_key)
    iv = encrypted_data[:IV_SIZE]
    ciphertext = encrypted_data[IV_SIZE:]
    original_data = aesgcm.decrypt(iv, ciphertext,None,)
    return original_data

# ==============================================================================
#                   FILE CHUNK DECRYPTION FUNCTION
# ==============================================================================

def decrypt_chunks_file(
    encrypted_chunks: Iterable[bytes],
    aes_key: bytes,
):

    """
    PURPOSE :
        Decrypt encrypted file chunks using streaming.

    INPUT :
        encrypted_chunks : Iterable[bytes]
        aes_key          : bytes

    OUTPUT :
        yield original_chunk
    """

    validate_aes_key(aes_key)
    aesgcm = AESGCM(aes_key)

    for encrypted_chunk in encrypted_chunks:
        iv = encrypted_chunk[:IV_SIZE]
        ciphertext = encrypted_chunk[IV_SIZE:]
        original_chunk = aesgcm.decrypt( iv,ciphertext,None,)
        yield original_chunk