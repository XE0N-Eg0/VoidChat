# ==============================================================================
#                               IMPORTS
# ==============================================================================

import os
import hashlib
from collections.abc import Iterable

# ==============================================================================
#                               CONFIG
# ==============================================================================

KEY_SIZE = 32
IV_SIZE = 12

# ==============================================================================
#                           AES KEY GENERATION
# ==============================================================================

def generate_aes_key():

    """
    PURPOSE :
        Generate random AES-256 key.

    OUTPUT :
        bytes
    """

    return os.urandom(KEY_SIZE)

# ==============================================================================
#                               IV GENERATION
# ==============================================================================

def generate_iv():

    """
    PURPOSE :
        Generate random IV.

    OUTPUT :
        bytes
    """

    return os.urandom(IV_SIZE)

# ==============================================================================
#                           AES KEY VALIDATION
# ==============================================================================

def validate_aes_key(
    aes_key: bytes
):

    """
    PURPOSE :
        Validate AES key length.

    INPUT :
        aes_key : bytes
    """

    if len(aes_key) != KEY_SIZE:

        raise ValueError(
            f"""
            Invalid AES Key Length
            Expected : {KEY_SIZE} bytes
            Received : {len(aes_key)} bytes
            """
        )

# ==============================================================================
#                       FILE HASH GENERATION FUNCTION
# ==============================================================================

def generate_file_hash(
    file_chunks: Iterable[bytes]
):

    """
    PURPOSE :
        Generate SHA-256 hash for file chunks.

    INPUT :
        file_chunks : Iterable[bytes]

    OUTPUT :
        file_hash : bytes
    """

    sha256 = hashlib.sha256()

    for chunk in file_chunks:

        sha256.update(chunk)

    file_hash = sha256.digest()

    return file_hash

# ==============================================================================
#                       FILE HASH VERIFICATION FUNCTION
# ==============================================================================

def verify_file_hash(
    file_chunks: Iterable[bytes],
    original_hash: bytes,
):

    """
    PURPOSE :
        Verify SHA-256 file hash.

    INPUT :
        file_chunks  : Iterable[bytes]
        original_hash : bytes

    OUTPUT :
        bool
    """

    new_hash = generate_file_hash(
        file_chunks,
    )

    return new_hash == original_hash