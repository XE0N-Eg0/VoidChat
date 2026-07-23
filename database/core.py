# database/core.py

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any

# ==============================================================================
# CONFIG
# ==============================================================================

DB_PATH = Path("data/app.db")

# ==============================================================================
# SQLITE CONNECTION
# ==============================================================================

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """
    PURPOSE :
        Create a secure thread-safe SQLite connection configuration.
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # timeout=10 helps manage busy states if multiple threads attempt to write
    connection = sqlite3.connect(db_path, timeout=10.0)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection

# ==============================================================================
# DATA MODELS
# ==============================================================================

@dataclass 
class Peer:
    peer_id: str
    username: str
    ip_address: str
    shared_key: Optional[bytes] = None
    last_seen: Optional[str] = None

@dataclass
class Message:
    id: Optional[int]
    peer_id: str
    sender_name: str
    message_type: str
    payload: Optional[str] = None
    file_path: Optional[str] = None
    timestamp: Optional[str] = None

# ==============================================================================
# DATABASE INITIALIZATION
# ==============================================================================

def initialize_database(db_path: Path = DB_PATH):
    """
    PURPOSE :
        Initialize database schema structurally if missing.
    """
    with get_connection(db_path) as connection:
        cursor = connection.cursor()

        # Create peers table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS peers (
                peer_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                shared_key BLOB,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # Create messages table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                peer_id TEXT NOT NULL,
                sender_name TEXT NOT NULL,
                message_type TEXT NOT NULL,
                payload TEXT,
                file_path TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (peer_id) REFERENCES peers(peer_id) ON DELETE CASCADE
            )
            """
        )
        connection.commit()

# ==============================================================================
# DATABASE QUERIES (THREAD-SAFE & UNIFIED)
# ==============================================================================

def save_or_update_peer(
    connection: sqlite3.Connection,
    peer_id: str,
    username: str,
    ip_address: str,
    shared_key: bytes = None
) -> bool:
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO peers (peer_id, username, ip_address, shared_key, last_seen)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(peer_id) DO UPDATE SET
                username = excluded.username,
                ip_address = excluded.ip_address,
                shared_key = COALESCE(excluded.shared_key, peers.shared_key),
                last_seen = CURRENT_TIMESTAMP
            """,
            (peer_id, username, ip_address, shared_key),
        )
        connection.commit()
        return True  # If execution reaches here without error, write was successful
    except sqlite3.Error as e:
        print(f"[DB ERROR] save_or_update_peer failed: {e}")
        return False

def get_peer_ip_by_username(connection: sqlite3.Connection, username: str) -> Optional[str]:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT ip_address FROM peers WHERE username = ? ORDER BY last_seen DESC LIMIT 1",
        (username,)
    )
    row = cursor.fetchone()
    return row["ip_address"] if row else None

def get_peer_id_by_username(connection: sqlite3.Connection, username: str) -> Optional[str]:
    cursor = connection.cursor()
    cursor.execute(
        "SELECT peer_id FROM peers WHERE username = ? LIMIT 1",
        (username,)
    )
    row = cursor.fetchone()
    return row["peer_id"] if row else None

def get_all_active_chats(connection: sqlite3.Connection) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT p.peer_id, p.username, p.ip_address, m.payload AS last_message, m.timestamp
        FROM peers p
        JOIN messages m ON p.peer_id = m.peer_id
        WHERE m.id = (
            SELECT MAX(m2.id)
            FROM messages m2
            WHERE m2.peer_id = p.peer_id
        )
        ORDER BY m.id DESC
        """
    )
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def log_message(
    connection: sqlite3.Connection,
    peer_id: str,
    sender_name: str,
    message_type: str,
    payload: str = None,
    file_path: str = None
) -> int:
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT INTO messages (peer_id, sender_name, message_type, payload, file_path, timestamp)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (peer_id, sender_name, message_type, payload, file_path),
    )
    connection.commit()
    return cursor.lastrowid

def fetch_conversation_history(
    connection: sqlite3.Connection,
    peer_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT sender_name, message_type, payload, file_path, timestamp 
        FROM messages 
        WHERE peer_id = ? 
        ORDER BY id DESC 
        LIMIT ? OFFSET ?
        """,
        (peer_id, limit, offset),
    )
    rows = cursor.fetchall()
    return list(reversed([dict(row) for row in rows]))

# ==============================================================================
# DATABASE MANAGER (CLEAN AUTOMATED LAYER FOR MULTI-THREADING)
# ==============================================================================

class DatabaseManager:
    """
    Manages operational task workflows thread-safely by spawning context connections 
    per runtime request dynamically.
    """
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        # Setup structural layout safety bounds upon invocation
        initialize_database(self.db_path)

    def save_or_update_peer(self, peer_id: str, username: str, ip_address: str, shared_key: bytes = None) -> bool:
        with get_connection(self.db_path) as conn:
            return save_or_update_peer(conn, peer_id, username, ip_address, shared_key)

    def get_peer_ip_by_username(self, username: str) -> Optional[str]:
        with get_connection(self.db_path) as conn:
            return get_peer_ip_by_username(conn, username)

    def get_peer_id_by_username(self, username: str) -> Optional[str]:
        with get_connection(self.db_path) as conn:
            return get_peer_id_by_username(conn, username)

    def get_all_active_chats(self) -> List[Dict[str, Any]]:
        with get_connection(self.db_path) as conn:
            return get_all_active_chats(conn)

    def log_message(self, peer_id: str, sender_name: str, message_type: str, payload: str = None, file_path: str = None) -> int:
        with get_connection(self.db_path) as conn:
            return log_message(conn, peer_id, sender_name, message_type, payload, file_path)

    def fetch_conversation_history(self, peer_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        with get_connection(self.db_path) as conn:
            return fetch_conversation_history(conn, peer_id, limit, offset)
        
    def get_all_known_peers(self) -> List[Dict[str,Any]]:
        """Fetch all the know peers"""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT peer_id, username, ip_address FROM peers")
            return [dict(row) for row in cursor.fetchall()]


# ==============================================================================
# MAIN PROTOTYPE TESTING RULE
# ==============================================================================

if __name__ == "__main__":
    initialize_database()
    print("DATABASE INITIALIZED SUCCESSFULLY")
    
    # Simple validation test pass
    mgr = DatabaseManager()
    mgr.save_or_update_peer("test-uuid-1234", "Alice", "192.168.1.15")
    mgr.log_message("test-uuid-1234", "Alice", "text", "Hello World Script Test!")
    
    print("Active Chats View Output:")
    print(mgr.get_all_active_chats())