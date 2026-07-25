
<div align="center">

# 🕸️ VoidChat

**A Decentralized, Serverless, Peer-to-Peer (P2P) Mesh Messenger for Local Area Networks.**

VoidChat operates without a central server, utilizing mDNS for peer discovery and raw TCP sockets for persistent, real-time encrypted communication and file sharing.

[![Status](https://img.shields.io/badge/Status-Alpha_%28Under_Passive_Development%29-orange.svg)](#-roadmap)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![UI: Flask + SSE](https://img.shields.io/badge/Frontend-Flask_%2B_SSE-green.svg)](#-engineering--architecture)

[Overview](#-overview) • [Architecture](#-engineering--architecture) • [Features](#-current-features) • [Installation](#-installation) • [Running](#-running-the-application) • [The Team](#-the-team)

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

## 🏗️ Engineering & Architecture

VoidChat is built on a strict, modular architecture. The UI acts purely as a presentation layer, while the `VoidChatOrchestrator` acts as the Application Kernel. 

```text
VoidChat/
├── networking/
│   ├── discovery.py    # mDNS/Zeroconf peer broadcast & listener
│   ├── connection.py   # Isolated TCP listeners (Control: 5001, Chat: 6000, File: 6001)
│   └── transport.py    # Binary framing (32-byte headers) & raw packet I/O
├── crypto/             # AES-GCM authenticated payload & stream encryption
├── protocol/           # Serialization, parsing, & chunk reassembly
├── database/core.py    # Thread-safe SQLite wrapper for local history & peers
└── src/
    ├── app.py          # Flask web interface with Server-Sent Events (SSE)
    └── run_cli.py      # CLI execution environment

```

* **Discovery Layer (`networking/discovery.py`)**: Uses `zeroconf` to broadcast and listen for peers on the LAN. Presence is decoupled from discovery—friend status is strictly determined by TCP connection health, preventing flaky mDNS from affecting the UX.
* **Connection Layer (`networking/connection.py`)**: Manages isolated TCP listeners for Control (`5001`), Chat (`6000`), and File (`6001`) streams.
* **Transport Layer (`networking/transport.py`)**: Handles binary framing (32-byte headers), packetization, and raw stream I/O. Differentiates between text and file metadata chunks.
* **Crypto Layer (`crypto/`)**: Implements AES-GCM authenticated encryption for both text payloads and streaming file chunks.
* **Parsing/Protocol Layer (`protocol/`)**: Manages serialization, deserialization, and chunk reassembly.
* **Persistence Layer (`database/core.py`)**: A thread-safe SQLite wrapper handling local message history and known peer metadata.
* **Presentation Layer (`src/app.py` & `ui/`)**: A Flask web frontend using Server-Sent Events (SSE) to push real-time backend events to a minimal, wireframe-inspired UI.

---

## ✨ Current Features

* 📡 **Serverless Discovery:** Automatic LAN peer discovery via mDNS.
* 🤝 **Consent-based Friendships:** Send and receive connection requests. Peers cannot message you without mutual consent.
* 🔐 **End-to-End Encryption:** All text messages and file chunks are encrypted using AES-GCM.
* 📁 **Secure File Transfers:** Stream large files over isolated TCP sockets with strict pre-approval consent workflows.
* 💾 **Local Persistence:** Chat histories and peer metadata are stored safely in a local SQLite database.
* 🌐 **Modern Web UI:** A clean, distraction-free web interface that automatically launches in your default browser.

---

## 🗺️ Roadmap

VoidChat is actively being developed. Future milestones include:

* 🌐 **Internet Routing:** Extending P2P capabilities beyond the LAN using NAT traversal (UDP hole punching) and WebRTC signaling.
* 🎙️ **Voice & Video:** Real-time audio/video streaming using P2P WebRTC.
* 🔑 **Asymmetric Key Exchange:** Implementing ECDH (Elliptic Curve Diffie-Hellman) for perfect forward secrecy during key exchange.
* 📦 **Portable Desktop App:** Packaging VoidChat as a standalone executable (`.exe` / `.AppImage`) using PyInstaller.

---

## 💾 Installation

VoidChat requires **Python 3.10+**.

### Option A: Standard Python (`pip`)

1. **Clone the repository:**
```bash
git clone [https://github.com/XE0N-Eg0/VoidChat.git](https://github.com/XE0N-Eg0/VoidChat.git)
cd VoidChat
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt

```


### Option B: Using `uv` (Recommended)

If you use [`uv`](https://github.com/astral-sh/uv) for fast Python package management:

```bash
git clone [https://github.com/XE0N-Eg0/VoidChat.git](https://github.com/XE0N-Eg0/VoidChat.git)
cd VoidChat
uv sync

```

---

## 🚀 Running the Application

### Web UI Mode (Default)

```bash
# Using standard python
python src/app.py

# Using uv
uv run src/app.py

```

### CLI Testing Mode (used for tesing purpose)

```bash
# Using standard python
python src/run_cli.py

# Using uv
uv run src/run_cli.py

```

### ⚠️ Firewall & Network Configuration

Since VoidChat operates directly over local network sockets without a central cloud server, your local operating system or network firewall may block incoming connections by default. For peer discovery and chat streams to function across your LAN, ensure that inbound and outbound traffic is permitted through your firewall for **TCP ports 5001 (Control), 6000 (Chat), and 6001 (File Transfers)**, as well as **UDP port 5353** for mDNS discovery.



## 🤝 Contributing

We welcome contributions from the community!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

> ⚠️ **Architecture Rule:** Please ensure your code adheres to existing architectural boundaries (e.g., the UI layer must never touch networking sockets directly).

---

## 👥 The Team

Meet the engineers behind VoidChat:

| Member | Responsibility |
| --- | --- |
| **Raghunath Das** | System Architecture & Networking Layer |
| **Partha Paul** | Parsing Layer |
| **Harshita Aggarwal** | Crypto Layer |
| **Tarunjit Biswas** | Database & Persistence Layer |

---

---

### What changed & improved:

1. **Added Tech & Status Badges:** Clean badges for Status, Python 3.10+, License, and Flask/SSE.
2. **Architecture Visualizer:** Added a file-tree preview directly inside the Architecture section to make it easy for developers to navigate the codebase at a glance.
3. **Structured Feature Icons & Tables:** Upgraded the feature list and team table formatting for higher visual appeal on GitHub.
4. **Maintained strict accuracy:** Preserved all of your team member credits, port definitions (`5001`, `6000`, `6001`), and exact UV / CLI execution instructions.

## 🗺️ Roadmap & Future Features

VoidChat is actively evolving to push local P2P boundaries further. Future milestones include extending communication beyond the local area network over the real internet using NAT traversal (UDP hole punching) and WebRTC signaling, introducing low-latency real-time voice and video calls, implementing ECDH asymmetric key exchange for perfect forward secrecy, and packaging the application into standalone desktop executables (`.exe` / `.AppImage`).

---