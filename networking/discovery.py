#protocol/discovery.py

# ================ SYS IMPORTS ===========================
import socket
import threading
import time
import uuid

# ================ LIB IMPORTS ===========================
from zeroconf import (
    Zeroconf,
    ServiceInfo,
    ServiceBrowser,
    ServiceListener,
)

# =========================================================
# CONFIG
# =========================================================

SERVICE_TYPE = "_voidchat._tcp.local."

DISCOVERY_PORT = 5000 #This will be fetched from setting later

PEER_TIMEOUT = 15


# =========================================================
# PEER REGISTRY
# =========================================================

class PeerRegistry:
    def __init__(self):
        self.peers = {}
        self.lock = threading.Lock()

    def update_peer(self, peer_id, data):
        with self.lock:
            self.peers[peer_id] = {
                **data,
                "last_seen": time.time()
            }

    def remove_peer(self, peer_id):
        with self.lock:
            if peer_id in self.peers:
                del self.peers[peer_id]

    def get_peers(self):
        with self.lock:
            return {
                peer_id: data.copy()
                for peer_id, data in self.peers.items()
            }

    def cleanup_stale_peers(self):
        while True:
            time.sleep(5)

            current_time = time.time()

            with self.lock:
                stale_peers = []

                for peer_id, data in self.peers.items():
                    elapsed = current_time - data["last_seen"]

                    if elapsed > PEER_TIMEOUT:
                        stale_peers.append(peer_id)

                for peer_id in stale_peers:
                    del self.peers[peer_id]


# =========================================================
# MDNS LISTENER
# =========================================================

class VoidChatListener(ServiceListener):
    def __init__(self, zeroconf, registry, self_peer_id):
        self.zeroconf = zeroconf
        self.registry = registry
        self.self_peer_id = self_peer_id

    def add_service(self, zc, type_, name):
        self._handle_service(name)

    def update_service(self, zc, type_, name):
        self._handle_service(name)

    def remove_service(self, zc, type_, name):
        peer_id = self._extract_peer_id(name)

        if peer_id:
            self.registry.remove_peer(peer_id)

    def _handle_service(self, name):
        info = self.zeroconf.get_service_info(
            SERVICE_TYPE,
            name
        )

        if not info:
            return

        if not info.addresses:
            return

        properties = {
            k.decode(): v.decode()
            for k, v in info.properties.items()
        }

        peer_id = properties.get("peer_id")

        if not peer_id:
            return

        if peer_id == self.self_peer_id:
            return

        ip = socket.inet_ntoa(info.addresses[0])

        peer_data = {
            "peer_id": peer_id,
            "username": properties.get("username"),
            "ip": ip,
            "port": info.port,
        }

        self.registry.update_peer(
            peer_id,
            peer_data
        )

    def _extract_peer_id(self, service_name):
        try:
            name_part = service_name.split(".")[0]

            return name_part.split("-")[-1]

        except Exception:
            return None


# =========================================================
# DISCOVERY SERVICE
# =========================================================

class DiscoveryService:
    def __init__(self, username): #(this will eventually take UUID, USERNAME)
        self.username = username

        self.peer_id = str(uuid.uuid4())[:8] # from settings

        self.local_ip = self.get_local_ip()

        self.registry = PeerRegistry()

        self.zeroconf = Zeroconf()

        self.service_name = (
            f"{self.username}-"
            f"{self.peer_id}."
            f"{SERVICE_TYPE}"
        )

        self.service_info = ServiceInfo(
            type_=SERVICE_TYPE,
            name=self.service_name,
            addresses=[socket.inet_aton(self.local_ip)],
            port=DISCOVERY_PORT,
            properties={
                "peer_id": self.peer_id,
                "username": self.username,
            },
            server=f"{socket.gethostname()}.local.",
        )

        self.listener = VoidChatListener(
            self.zeroconf,
            self.registry,
            self.peer_id
        )

        self.browser = None

        self.running = False

    # =====================================================
    # NETWORK
    # =====================================================

    def get_local_ip(self):
        
        s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]

        except Exception:
            ip = "127.0.0.1"

        finally:
            s.close()

        return ip

    # =====================================================
    # SERVICE CONTROL
    # =====================================================

    def start(self):
        if self.running:
            return
        
        #debug 
        # print(f"\n[INFO] Starting discovery...")
        # print(f"[INFO] Username : {self.username}")
        # print(f"[INFO] Peer ID  : {self.peer_id}")
        # print(f"[INFO] Local IP : {self.local_ip}")

        self.zeroconf.register_service(
            self.service_info
        )

        self.browser = ServiceBrowser(
            self.zeroconf,
            SERVICE_TYPE,
            self.listener
        )

        threading.Thread(
            target=self.registry.cleanup_stale_peers,
            daemon=True
        ).start()

        self.running = True

    def stop(self):
        if not self.running:
            return
        
        #debug
        # print("\n[INFO] Stopping discovery...")

        self.zeroconf.unregister_service(
            self.service_info
        )

        self.zeroconf.close()

        self.running = False

    # =====================================================
    # PUBLIC API
    # =====================================================

    def get_peers(self):
        return self.registry.get_peers()


# =========================================================
# TESTING / DEBUG
# =========================================================

if __name__ == "__main__":

    username = input("Username: ")

    discovery = DiscoveryService(username)

    discovery.start()

    print("\n[INFO] Discovery running.")
    print("[INFO] Press CTRL+C to exit.")

    try:
        while True:
            time.sleep(5)

            peers = discovery.get_peers()

            print("\n========== DISCOVERED PEERS ==========")

            if not peers:
                print("No peers discovered.")

            for peer_id, data in peers.items():

                elapsed = round(
                    time.time() - data["last_seen"],
                    1
                )

                print(f"""
Peer ID : {peer_id}
Username: {data['username']}
IP      : {data['ip']}
Port    : {data['port']}
LastSeen: {elapsed}s ago
                """)

    except KeyboardInterrupt:
        pass

    finally:
        discovery.stop()