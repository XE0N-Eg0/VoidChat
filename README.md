
<div align="center">

#  VoidChat

**A Decentralized, Serverless, Peer-to-Peer (P2P) Mesh Messenger for Local Area Networks.**

VoidChat operates without a central server, utilizing mDNS for peer discovery and raw TCP sockets for persistent, real-time encrypted communication and file sharing.

*Status: 🚧 Under Passive Development (Alpha)*

</div>

---

## 📖 Table of Contents
- [Overview](#-overview)
- [Engineering & Architecture](#-engineering--architecture)
- [Current Features](#-current-features)
- [Roadmap](#-roadmap)
- [Installation](#-installation)
- [Running the Application](#-running-the-application)
- [Contributing](#-contributing)
- [The Team](#-the-team)

---

## 📖 Overview

VoidChat is designed to be a lightweight, secure, and serverless communication tool. Whether you are on a corporate LAN, a home network, or an offline ad-hoc network, VoidChat allows you to discover peers, establish friendships via consent workflows, and chat or share files directly. 

By leveraging mDNS (Zeroconf) for discovery and a custom binary TCP framing protocol for transport, VoidChat bypasses the need for any intermediate servers, ensuring minimal latency and maximum privacy.

---

## 🏗 Engineering & Architecture

VoidChat is built on a strict, modular architecture. The UI acts purely as a presentation layer, while the `VoidChatOrchestrator` acts as the Application Kernel. 

- **Discovery Layer (`networking/discovery.py`)**: Uses `zeroconf` to broadcast and listen for peers on the LAN. Presence is decoupled from discovery—friend status is strictly determined by TCP connection health, preventing flaky mDNS from affecting the UX.
- **Connection Layer (`networking/connection.py`)**: Manages isolated TCP listeners for Control (5001), Chat (6000), and File (6001) streams.
- **Transport Layer (`networking/transport.py`)**: Handles binary framing (32-byte headers), packetization, and raw stream I/O. Differentiates between text and file metadata chunks.
- **Crypto Layer (`crypto/`)**: Implements AES-GCM authenticated encryption for both text payloads and streaming file chunks.
- **Parsing/Protocol Layer (`protocol/`)**: Manages serialization, deserialization, and chunk reassembly.
- **Persistence Layer (`database/core.py`)**: A thread-safe SQLite wrapper handling local message history and known peer metadata.
- **Presentation Layer (`src/app.py` & `ui/`)**: A Flask web frontend using Server-Sent Events (SSE) to push real-time backend events to a minimal, wireframe-inspired UI.

---

##  Current Features

-  **Serverless Discovery:** Automatic LAN peer discovery via mDNS.
-  **Consent-based Friendships:** Send and receive connection requests. Peers cannot message you without mutual consent.
-  **End-to-End Encryption:** All text messages and file chunks are encrypted using AES-GCM.
-  **Secure File Transfers:** Stream large files over isolated TCP sockets with strict pre-approval consent workflows.
-  **Local Persistence:** Chat histories and peer metadata are stored safely in a local SQLite database.
-  **Modern Web UI:** A clean, distraction-free web interface that automatically launches in your default browser.

---

## 🗺 Roadmap

VoidChat is actively being developed. Future milestones include:

-  **Internet Routing:** Extending P2P capabilities beyond the LAN using NAT traversal (UDP hole punching) and WebRTC signaling.
-  **Voice & Video:** Real-time audio/video streaming using P2P WebRTC.
-  **Asymmetric Key Exchange:** Implementing ECDH (Elliptic Curve Diffie-Hellman) for perfect forward secrecy during key exchange.
-  **Portable Desktop App:** Packaging VoidChat as a standalone executable (`.exe` / `.AppImage`) using PyInstaller.

*Want to suggest a feature? Open an [Issue](https://github.com/XE0N-Eg0/VoidChat/issues) or start a Discussion!*

---

## 💾 Installation

VoidChat requires **Python 3.10+**. 

### Option A: Standard Python (`pip`)
1. Clone the repository:
   ```bash
   git clone https://github.com/XE0N-Eg0/VoidChat.git
   cd VoidChat
   ```
2. Create and activate a virtual environment:
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Option B: Using `uv` (Recommended for speed)
If you use [`uv`](https://github.com/astral-sh/uv) for Python package management:
1. Clone the repository:
   ```bash
   git clone https://github.com/XE0N-Eg0/VoidChat.git
   cd VoidChat
   ```
2. Synchronize the environment:
   ```bash
   uv sync
   ```

---

##  Running the Application

### Manual Launch (Command Line)

**To run the Web UI:**
```bash
# Using standard python
python src/app.py

# Using uv
uv run src/app.py
```

**To run the CLI testing environment:**
```bash
# Using standard python
python src/run_cli.py

# Using uv
uv run src/run_cli.py
```

---

##  Contributing

We welcome contributions from the community! Whether it's a bug fix, a new feature, or improvements to the documentation, your help is appreciated.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure your code adheres to the existing architectural boundaries (e.g., the UI should never touch networking sockets directly).

---

##  The Team

Meet the engineers behind VoidChat:

| Member            | Responsibility                        |
| ----------------- | ------------------------------------- |
| **Raghunath Das** | System Architecture & Networking Layer|
| **Partha Paul**   | Parsing Layer                         |
| **Harshita Aggarwal** | Crypto Layer                      |
| **Tarunjit Biswas**| Database                             |

---

<div align="center">
  <sub>Built with ❤️ by the VoidChat Team. </sub>
</div>
