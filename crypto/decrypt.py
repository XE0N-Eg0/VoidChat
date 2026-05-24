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
#                   TEXT DECRYPTION FUNCTION
# ==============================================================================

def decrypt_chunks_list(
    encrypted_chunks_list: list[bytes],
    aes_key: bytes
):

    """
    PURPOSE :
        Decrypt encrypted chunks list.
    INPUT :
        encrypted_chunks_list : list[bytes]
        aes_key               : bytes
    OUTPUT :
        decrypted_chunks_list : list[bytes]
    """

    validate_aes_key(aes_key)
    aesgcm = AESGCM(aes_key)
    decrypted_chunks_list = []
    for encrypted_chunk in encrypted_chunks_list:
        iv = encrypted_chunk[:IV_SIZE]
        ciphertext = encrypted_chunk[IV_SIZE:]
        original_chunk = aesgcm.decrypt(  iv,  ciphertext,  None, )
        decrypted_chunks_list.append(original_chunk)
    return decrypted_chunks_list


# ==============================================================================
#                   FILE CHUNK DECRYPTION FUNCTION
# ==============================================================================

def decrypt_chunks_file(
    encrypted_chunks: Iterable[bytes],
    aes_key: bytes
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
        original_chunk = aesgcm.decrypt(  iv,  ciphertext, None, )
        yield original_chunk