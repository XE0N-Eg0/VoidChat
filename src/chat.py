# ========================================
#               src/chat.py
# ========================================
from protocol.sender import (
    create_chat_packet,
    serialize_message,
    chunk_encrypted_message,
)
from protocol.receiver import (
    receive_chat_frame,
)
from crypto.encrypt import encrypt_text

# ========================================
#        COMPLETE CHAT PROCESSING
# ========================================

def process_chat(text: str,sender_name: str,):

    message_packet = create_chat_packet(text=text,sender=sender_name)

    serialized_message = serialize_message(message_packet)

    encrypted_message = encrypt_text(serialized_message)

    return receive_chat_frame(encrypted_message)