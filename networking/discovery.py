# networking/discovery.py

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
DISCOVERY_PORT = 5000 # This will be fetched from setting later
PEER_TIMEOUT = 120  # Kept for potential future use, but no longer used for aggressive pruning

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
        # Kept for structural compatibility, but no longer aggressively pruning
        # mDNS remove_service handles explicit disconnects.
        # TCP socket failure handles abrupt disconnects.
        pass


# =========================================================
# MDNS LISTENER
# =========================================================

class VoidChatListener(ServiceListener):
    def __init__(self, zeroconf, registry, self_peer_id, discovery_service):
        self.zeroconf = zeroconf
        self.registry = registry
        self.self_peer_id = self_peer_id
        self.discovery_service = discovery_service

    def add_service(self, zc, type_, name):
        self._handle_service(name)
        # Reactive advertisement when a new service is seen
        self.discovery_service.refresh_advertisement()

    def update_service(self, zc, type_, name):
        self._handle_service(name)

    def remove_service(self, zc, type_, name):
        # Parse peer_id from properties cache instead of fragile name splitting
        info = self.zeroconf.get_service_info(SERVICE_TYPE, name)
        if info:
            properties = {k.decode(): v.decode() for k, v in info.properties.items()}
            peer_id = properties.get("peer_id")
            if peer_id:
                self.registry.remove_peer(peer_id)

    def _handle_service(self, name):
        info = self.zeroconf.get_service_info(SERVICE_TYPE, name)

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

        # Explicitly cast to standard string to satisfy strict type checkers
        ip = str(socket.inet_ntoa(info.addresses[0]))

        peer_data = {
            "peer_id": peer_id,
            "username": properties.get("username"),
            "ip": ip,
            "port": info.port,
        }

        self.registry.update_peer(peer_id, peer_data)


# =========================================================
# DISCOVERY SERVICE
# =========================================================

class DiscoveryService:
    # CHANGES: Accept peer_id from orchestrator instead of generating ephemeral
    def __init__(self, username: str, peer_id: str):
        self.username = username
        self.peer_id = peer_id
        
        self.local_ip = self.get_local_ip()

        self.registry = PeerRegistry()

        # CHANGES: Explicitly bind Zeroconf to the local interface IP.
        # This fixes Windows dropping mDNS packets on 0.0.0.0
        self.zeroconf = Zeroconf(interfaces=[self.local_ip])
        
        # CHANGES: Cooldown state for reactive advertisement
        self.last_advertisement = 0
        self.advertisement_cooldown = 5  # 5 seconds to prevent storms

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
            self.peer_id,
            self # CHANGES: Pass self for reactive ad callback
        )

        self.browser = None
        self.running = False

    # =====================================================
    # NETWORK
    # =====================================================

    def get_local_ip(self) -> str:
        """
        CHANGES: Pure standard library implementation to find the active LAN IP.
        Ignores loopback, link-local, and common virtual machine adapters.
        """
        valid_ips = []
        
        try:
            hostname = socket.gethostname()
            # getaddrinfo returns tuples: (family, type, proto, canonname, sockaddr)
            results = socket.getaddrinfo(hostname, None, socket.AF_INET)
            
            for result in results:
                sock_addr = result[4]
                ip = sock_addr[0]
                
                # Ensure it's a string and skip loopback/link-local
                if not isinstance(ip, str):
                    continue
                if ip.startswith("127.") or ip.startswith("169.254"):
                    continue
                    
                valid_ips.append(ip)
        except Exception:
            pass
            
        # Filter out common virtual adapter IPs to find the real LAN IP
        for ip in valid_ips:
            # Heuristic: Virtual adapters often use specific subnets
            if not (ip.startswith("192.168.56.") or   # VirtualBox
                    ip.startswith("172.16.") or       # Docker/VMware
                    ip.startswith("10.0.0.")):        # Sometimes VMs
                return ip
                
        # Fallback to first valid IP found, or the UDP probe method
        if valid_ips:
            return valid_ips[0]
            
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # =====================================================
    # SERVICE CONTROL
    # =====================================================

    def start(self):
        if self.running:
            return
        
        self.zeroconf.register_service(self.service_info)

        self.browser = ServiceBrowser(
            self.zeroconf,
            SERVICE_TYPE,
            self.listener
        )

        # CHANGES: Removed the cleanup_stale_peers thread. 
        # mDNS remove_service handles explicit disconnects. 
        # For abrupt disconnects, the TCP socket failure will handle it.

        self.running = True
        print(f"[DISCOVERY] Broadcasting as {self.username} ({self.peer_id[:8]}) on {self.local_ip}")

    def stop(self):
        if not self.running:
            return
        
        try:
            self.zeroconf.unregister_service(self.service_info)
            self.zeroconf.close()
        except Exception as e:
            print(f"[DISCOVERY] Error during shutdown: {e}")

        self.running = False

    # =====================================================
    # PUBLIC API
    # =====================================================

    def get_peers(self):
        return self.registry.get_peers()

    # CHANGES: Added on-demand discovery
    def discover_now(self):
        """Triggers a fresh discovery cycle by restarting the browser."""
        if not self.running: return
        if self.browser:
            try:
                self.browser.cancel()
            except Exception:
                pass
        time.sleep(0.1)
        self.browser = ServiceBrowser(self.zeroconf, SERVICE_TYPE, self.listener)
        self.refresh_advertisement()
        print("[DISCOVERY] On-demand discovery triggered.")

    # CHANGES: Added reactive advertisement with cooldown
    def refresh_advertisement(self):
        """Re-broadcasts presence if cooldown has passed."""
        current_time = time.time()
        if current_time - self.last_advertisement > self.advertisement_cooldown:
            self.last_advertisement = current_time
            try:
                # Re-registering forces a multicast announcement
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.register_service(self.service_info)
            except Exception:
                pass