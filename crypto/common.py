
# ==============================================================================
#                               IMPORTS
# ==============================================================================
import os
# ==============================================================================
#                               CONFIG
# ==============================================================================

KEY_SIZE = 32
IV_SIZE = 12


def generate_aes_key():

    """
    PURPOSE :
        Generate random AES-256 key.

    OUTPUT :
        bytes
    """

    return os.urandom(KEY_SIZE)

def generate_iv():
    """
    PURPOSE :
        Generate random IV.
    OUTPUT :
        bytes
    """
    return os.urandom(IV_SIZE)

def validate_aes_key(aes_key):
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