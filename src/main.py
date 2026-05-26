# main_orchestrator.py
from networking.connection import ConnectionManager, ConnectionType
from networking.transport import TransportManager

connection_manager = ConnectionManager()
transport_manager = TransportManager(connection_manager)

def on_new_socket_established(peer_ip, conn_type, sock):
    """
    Acts as the system router. Automatically catches sockets created on-demand
    and binds them to the correct transport wire protocols.
    """
    channel_name = None
    if conn_type == ConnectionType.CHAT:
        channel_name = "txt"
    elif conn_type == ConnectionType.FILE:
        channel_name = "file"
    elif conn_type == ConnectionType.CONTROL:
        channel_name = "control" # If you want transport headers on control frames

    if channel_name:
        # Dynamically attach a background receiver thread to the newly born socket
        transport_manager.bind_socket(peer_ip, channel_name, sock)

# Register the dynamic binding bridge
connection_manager.register_connection_handler(on_new_socket_established)

connection_manager.start()
transport_manager.start()

# =========================================================
# SAMPLE DISPATCH WORKFLOW: SENDING A FILE ON DEMAND
# =========================================================
def share_file_flow(peer_ip, file_path):
    # 1. (Higher Layer Logic) Sends text/control JSON frame: {"type": "file_req", "name": "photo.png"}
    # 2. Wait for incoming txt frame response validating consent.
    consent_received = True # Mocking the async response intercept
    
    if consent_received:
        print("[PROCESS] Consent granted! Opening transient file pipe...")
        # Open the TCP socket strictly on demand
        file_socket = connection_manager.open_data_channel(peer_ip, ConnectionType.FILE)
        
        if file_socket:
            # 3. Stream chunks over the transport frame helper
            # for chunk_idx, chunk in enumerate(encrypted_file_chunks):
            #     transport_manager.send_file_chunk_frame(peer_ip, ..., chunk_idx, chunk, ...)
            
            # 4. Tear it completely down when finished to free system memory and thread space!
            connection_manager.close_data_channel(peer_ip, ConnectionType.FILE)