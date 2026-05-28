# main.py
import os
import sys
import time
import threading

# Import your network and routing managers
from networking.connection import ConnectionManager, ConnectionType
from networking.transport import TransportManager

# Import your upper application pipeline functions
from src.receive_pipeline import process_incoming_chat, initialize_file_transfer, stream_incoming_file_chunk
from src.send_pipeline import send_chat_to_peer, process_and_send_file

# Shared cryptographic key (Must be identical on both machines) #NOTE: HARSHITA YOU NEED TO FIGURE OUT HOW CAN WE SHARE THE KEY INDEPENDENTLY
# Ensure it matches the expected key length for your AES layer (16, 24, or 32 bytes)
SHARED_AES_KEY = b"7Yv9Wp2Rk5Nx4Qt8Fm3Gj6Hk1Dx7Mp9B"   # SOME BS KEY


def setup_application_router(transport_mgr: TransportManager):
    """
    Hooks into TransportManager to receive parsed raw network frames
    and direct them to the appropriate processing pipeline.
    """
    def application_frame_router(frame_data: dict):
        channel = frame_data["channel"]
        chunk_index = frame_data["chunk_index"]

        if channel == "text":
            # Pass to Chat Pipeline
            completed_chat = process_incoming_chat(frame_data, SHARED_AES_KEY)
            if completed_chat:
                print(f"\n[RECEIVED CHAT] From {completed_chat['sender']}: {completed_chat['payload']}")
                print("Enter option (1/2): ", end="", flush=True)

        elif channel == "file":
            # Pass to File Pipeline
            if chunk_index == 0:
                # Chunk 0 is the unencrypted metadata block
                initialize_file_transfer(frame_data, output_directory="./downloads")
            else:
                # Chunks 1 to N are sequential encrypted data payloads
                still_transferring = stream_incoming_file_chunk(frame_data, SHARED_AES_KEY)
                if not still_transferring:
                    print("\n[DOWNLOAD COMPLETE] File saved successfully in './downloads/' directory.")
                    print("Enter option (1/2): ", end="", flush=True)

    # Bind the routing handler to the transport engine
    transport_mgr.register_handler(application_frame_router)


def setup_network_links(connection_mgr: ConnectionManager, transport_mgr: TransportManager):
    """
    Binds the low-level connection manager events to the transport manager.
    When a remote peer opens a socket connection to us, this ensures the transport manager
    immediately spawns a tracking thread to listen and unpack incoming frames.
    """
    def on_incoming_socket_established(peer_ip: str, conn_type: ConnectionType, sock):
        # Map ConnectionType Enums directly back to Transport string channels
        channel_map = {
            ConnectionType.CHAT: "text",
            ConnectionType.FILE: "file",
            ConnectionType.CONTROL: "control"
        }
        channel_str = channel_map[conn_type]
        
        # Dynamically link the socket to the Transport layer receive system
        transport_mgr.bind_socket(peer_ip, channel_str, sock)

    connection_mgr.register_connection_handler(on_incoming_socket_established)


def main():
    # 1. Initialize Network Core
    connection_mgr = ConnectionManager()
    transport_mgr = TransportManager(connection_manager=connection_mgr)

    # 2. Wire the Layers Together (Connection -> Transport -> Pipelines)
    setup_network_links(connection_mgr, transport_mgr)
    setup_application_router(transport_mgr)

    # 3. Fire up Background Servers (Listens on ports defined in connection.py)
    connection_mgr.start() #NOTE: Starts background activity
    transport_mgr.start() #NOTE: Starts background activity
    
    print("[SYSTEM] Network nodes and servers are active.")
    print("[SYSTEM] Listening for incoming messages or files in the background...")

    
    my_name = input("Enter your username for this session: ").strip()

    
    try:
        while True:
            print("\n--- VOIDCHAT P2P TRANSFER INTERFACE ---")
            print("1. Send a Chat Message")
            print("2. Send a File")
            print("Type 'exit' to quit.")
            choice = input("Enter option (1/2): ").strip()

            if choice.lower() == 'exit':
                break

            if choice not in ["1", "2"]:
                print("[ERROR] Invalid selection.")
                continue

            target_ip = input("Enter the target computer's IP address: ").strip()
            if not target_ip:
                print("[ERROR] IP address cannot be empty.")
                continue

            if choice == "1":
                text_message = input("Enter text message to send: ")
                # Run network sending loop inside a temporary background thread 
                # so the CLI doesn't lock up during network I/O blockings
                threading.Thread(
                    target=send_chat_to_peer,
                    args=(target_ip, text_message, my_name, transport_mgr),
                    daemon=True
                ).start()

            elif choice == "2":
                file_path = input("Enter the path of the file to transfer: ").strip()
                if not os.path.exists(file_path):
                    print(f"[ERROR] File '{file_path}' does not exist.")
                    continue

                print(f"[PIPELINE] Initializing file streaming pipeline for {os.path.basename(file_path)}...")
                threading.Thread(
                    target=process_and_send_file,
                    args=(target_ip, file_path, my_name, transport_mgr, SHARED_AES_KEY),
                    daemon=True
                ).start()

            # Brief pause to let thread log prints settle beautifully before showing menu again
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Execution interrupted by user.")
    finally:
        print("[SYSTEM] Cleaning up runtime resources and halting background daemons...")
        # Gracefully shut down socket structures inside your engine threads
        transport_mgr.stop()


if __name__ == "__main__":
    main()