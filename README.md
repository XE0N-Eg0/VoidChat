# VoidChat

A modular peer-to-peer encrypted messaging and file transfer system built in Python.

VoidChat is designed as a beginner-friendly but professionally structured systems project focusing on:

* P2P networking
* End-to-end encrypted communication
* Custom protocol design
* Chunked file transfer
* Modular architecture
* Collaborative software development workflow

---

# Features (Planned)

* LAN peer discovery
* Secure encrypted messaging
* Chunked file transfer
* Custom packet protocol
* AES-based encryption layer
* SQLite local storage
* Modular architecture
* Team-based development workflow

---

# Project Architecture

```text
VoidChat/
│
├── networking/  # Socket communication and peer discovery   
├── protocol/    # Packet creation, parsing, framing, chunking
├── crypto/      # AES encryption and decryption
├── database/    # For Database related things
│
├── src/
│   └── main.py
│
├── .python-version
├── pyproject.toml
├── uv.lock
├── .gitignore
└── README.md
```

---

# Core Modules

## Networking Layer

Responsible for:

* Peer discovery
* TCP communication
* Connection handling
* Sending/receiving raw bytes

---

## Protocol Layer

Responsible for:

* Packet creation
* Serialization/deserialization
* Framing
* File chunking
* Message reconstruction

---

## Crypto Layer

Responsible for:

* AES encryption
* AES decryption
* Nonce handling
* Secure byte transformation

---

## Database Layer

Responsible for:

* SQLite database management
* Message persistence
* Peer metadata
* File transfer metadata

---

# Tech Stack

| Component           | Technology     |
| ------------------- | -------------- |
| Language            | Python 3.10    |
| Environment Manager | uv             |
| Encryption          | cryptography   |
| Database            | SQLite         |
| Networking          | Python sockets |
| Version Control     | Git + GitHub   |

---

# Team Workflow

This project follows a collaborative Git workflow.



# Setup Instructions

## 1. Clone Repository

```bash
git clone <repo-url>
cd VoidChat
```

---

## 2. Install uv

Official Website:

[uv Documentation](https://docs.astral.sh/uv/?utm_source=chatgpt.com)

---

## 3. Sync Environment

```bash
uv sync
```

This automatically:

* Creates virtual environment
* Installs dependencies
* Uses correct Python version

---

## 4. Activate Virtual Environment

### Windows

```bash
.venv\Scripts\activate
```

### Linux/macOS

```bash
source .venv/bin/activate
```

---

# Git Workflow

## Pull Latest Changes

```bash
git pull origin main
```

---

## Commit Changes

```bash
git add .
git commit -m "Add meaningful commit message"
```

---

## Push Changes

```bash
git push origin branch name
```

---

## Open Pull Request

After pushing:

* Open PR on GitHub
* Review changes

---

# Development Guidelines

* Keep modules independent
* Follow defined interfaces
* Write small commits
* Avoid pushing broken code
* Keep functions simple and modular
* Document important architectural decisions

---

# Current Development Stage

Initial architecture and repository setup.

Planned first milestone:

* LAN peer discovery
* TCP messaging
* Packet framing
* AES encryption
* Basic CLI communication

---

# Team Members

| Member            | Responsibility                        |
| ----------------- | ------------------------------------- |
| Raghunath Das     | System Architecture                   |
| Raghunath Das     | Networking Layer                      |
| Partha Paul       | Parsing Layer                         |
| Harshita Aggarwal | Crypto Layer                          |
| Tarunjit Biswas   | Database                              |

---

# License

MIT License

---

# Vision

VoidChat is being developed as a learning-oriented systems project focused on understanding:

* Networking fundamentals
* Protocol engineering
* Secure communication systems
* Collaborative software development
* Modular software architecture