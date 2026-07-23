# src/run_cli.py

import os
import sys
import time

# Ensure absolute root paths are visible across sibling imports
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from main import VoidChatOrchestrator, load_user_identity

def print_menu():
    print("\n" + "="*40)
    print("          VOIDCHAT TEST CLI")
    print("="*40)
    print("1. Discover Nearby Peers")
    print("2. List online peers")
    print("3. Send Connection Request")
    print("4. Send text message (Friends only)")
    print("5. Send file request (Friends only)")
    print("6. View chat history")
    print("7. Exit")
    print("="*40)

def select_peer(peers):
    if not peers:
        print("[CLI] No peers available.")
        return None, None, None
    print("\n--- Online Peers ---")
    peer_list = list(peers.items())
    for i, (pid, data) in enumerate(peer_list):
        status = data.get('status', 'Unknown')
        friend_tag = " (Friend)" if data.get('is_friend') else ""
        print(f"[{i}] {data.get('username', 'Unknown')} ({pid[:8]}) @ {data.get('ip')} [{status}{friend_tag}]")
    print("--------------------")
    try:
        choice = int(input("Select peer index: "))
        if 0 <= choice < len(peer_list):
            peer_id, peer_data = peer_list[choice]
            return peer_id, peer_data.get("ip"), peer_data.get("username")
    except ValueError: pass
    return None, None, None

def handle_event(event_type: str, data: dict) -> bool:
    """Callback function to handle incoming requests from main.py"""
    if event_type == "conn_req":
        print(f"\n[INBOUND REQUEST] {data['username']} wants to connect. (y/n)")
        resp = input(">> ").strip().lower()
        return resp == 'y'
    elif event_type == "file_req":
        print(f"\n[INBOUND FILE] {data['username']} wants to send '{data['filename']}' ({data['size']} bytes). (y/n)")
        resp = input(">> ").strip().lower()
        return resp == 'y'
    return False

def main():
    # 1. Bootstrapping Identity
    user_config = load_user_identity()
    print(f"\n[CLI] Welcome, {user_config['username']}!")

    # 2. Initialize Kernel
    orchestrator = VoidChatOrchestrator(
        username=user_config["username"],
        peer_id=user_config["peer_id"]
    )
    orchestrator.set_event_callback(handle_event)
    
    # 3. Start Backend
    print("[CLI] Booting backend services...")
    orchestrator.start()
    
    # Give mDNS a few seconds to find peers on the network
    print("[CLI] Waiting 3 seconds for peer discovery...")
    time.sleep(3)

    # 4. CLI Loop
    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == '1':
            orchestrator.discover_nearby()
            print("[CLI] Waiting 2 seconds for responses...")
            time.sleep(2)

        elif choice == '2':
            peers = orchestrator.get_online_peers()
            if not peers:
                print("[CLI] No peers available.")
            else:
                for pid, data in peers.items():
                    status = data.get('status', 'Unknown')
                    friend_tag = " (Friend)" if data.get('is_friend') else ""
                    print(f" - {data.get('username')} ({pid[:8]}) @ {data.get('ip')} [{status}{friend_tag}]")

        elif choice == '3':
            peers = orchestrator.get_online_peers()
            peer_id, peer_ip, _ = select_peer(peers)
            if peer_id and peer_ip:
                orchestrator.send_connection_request(peer_ip, peer_id)
                print("[CLI] Connection request sent.")

        elif choice == '4':
            peers = orchestrator.get_online_peers()
            peer_id, peer_ip, _ = select_peer(peers)
            if peer_id and peer_ip:
                text = input("Enter message: ").strip()
                if text: orchestrator.transmit_text_message(peer_ip, peer_id, text)

        elif choice == '5':
            peers = orchestrator.get_online_peers()
            peer_id, peer_ip, _ = select_peer(peers)
            if peer_id and peer_ip:
                file_path = input("Enter absolute path to file: ").strip()
                if os.path.exists(file_path):
                    print(f"[CLI] Sending file '{os.path.basename(file_path)}' to {peer_ip}...")
                    orchestrator.send_file_request(peer_ip, peer_id, file_path)
                else:
                    print("[CLI] File does not exist.")

        elif choice == '6':
            peers = orchestrator.get_online_peers()
            peer_id, _, name = select_peer(peers)
            if peer_id:
                print(f"\n--- Chat History with {name} ---")
                history = orchestrator.get_chat_history(peer_id)
                if not history:
                    print("No history found.")
                else:
                    for msg in history:
                        sender = msg.get('sender_name', 'Unknown')
                        msg_type = msg.get('message_type', 'text')
                        payload = msg.get('payload', '')
                        ts = msg.get('timestamp', '')
                        print(f"[{ts}] {sender} ({msg_type}): {payload}")
                print("--------------------------------------")

        elif choice == '7':
            print("[CLI] Shutting down VoidChat...")
            orchestrator.stop()
            print("[CLI] Goodbye!")
            break

        else:
            print("[CLI] Invalid choice. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[CLI] Interrupted by user. Exiting.")
        sys.exit(0)