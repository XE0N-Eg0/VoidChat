# ==============================================================================
# IMPORTS
# ==============================================================================

import sqlite3

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


# ==============================================================================
# CONFIG
# ==============================================================================

DB_PATH = Path("data/app.db")


# ==============================================================================
# SQLITE CONNECTION
# ==============================================================================

def get_connection():

    """
    PURPOSE :
        Create SQLite connection.

    OUTPUT :
        sqlite3.Connection
    """

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


# ==============================================================================
# DATA MODELS
# ==============================================================================

@dataclass 
class User:
    user_id: str #change this to peer_id
    username: str
    public_key: Optional[str] = None #this will be uuid given by me/or other
    ip_address: Optional[str] = None
    last_seen: Optional[str] = None
    status: Optional[str] = None
    #port ?


@dataclass
class Conversation:
    conversation_id: str
    title: Optional[str] = None
    created_at: Optional[str] = None
    last_activity: Optional[str] = None


@dataclass
class ConversationParticipant:
    participant_id: str
    conversation_id: str
    user_id: str
    joined_at: Optional[str] = None
    role: Optional[str] = None
    last_seen: Optional[str] = None


@dataclass
class Message:
    message_id: str
    sender_id: str
    receiver_id: str
    conversation_id: Optional[str]
    encrypted_message: str
    timestamp: Optional[str] = None
    delivery_status: Optional[str] = None


@dataclass
class FileMetadata:
    file_id: str
    sender_id: str
    receiver_id: str
    conversation_id: Optional[str]
    filename: str
    file_size: int
    checksum: Optional[str] = None
    total_chunks: int = 0
    transfer_status: Optional[str] = None


@dataclass
class FileChunk:
    chunk_id: str
    file_id: str
    chunk_index: int
    chunk_path: str
    is_received: bool = False


# ==============================================================================
# DATABASE INITIALIZATION
# ==============================================================================

def initialize_database():

    """
    PURPOSE :
        Initialize database tables.

    OUTPUT :
        None
    """

    connection = get_connection()
    cursor = connection.cursor()

    create_users_table(cursor)
    create_conversations_table(cursor)
    create_conversation_participants_table(cursor)
    create_messages_table(cursor)
    create_files_table(cursor)
    create_file_chunks_table(cursor)

    connection.commit()
    connection.close()


def create_users_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            public_key TEXT,
            ip_address TEXT,
            last_seen TIMESTAMP,
            status TEXT
        )
        """
    )


def create_conversations_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            title TEXT,
            created_at TIMESTAMP,
            last_activity TIMESTAMP
        )
        """
    )


def create_conversation_participants_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS conversation_participants (
            participant_id TEXT PRIMARY KEY,
            conversation_id TEXT,
            user_id TEXT,
            joined_at TIMESTAMP,
            role TEXT,
            last_seen TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        """
    )


def create_messages_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            sender_id TEXT,
            receiver_id TEXT,
            conversation_id TEXT,
            encrypted_message TEXT,
            timestamp TIMESTAMP,
            delivery_status TEXT,
            FOREIGN KEY (sender_id) REFERENCES users(user_id),
            FOREIGN KEY (receiver_id) REFERENCES users(user_id),
            FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
        )
        """
    )


def create_files_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            sender_id TEXT,
            receiver_id TEXT,
            conversation_id TEXT,
            filename TEXT,
            file_size INTEGER,
            checksum TEXT,
            total_chunks INTEGER,
            transfer_status TEXT,
            FOREIGN KEY (sender_id) REFERENCES users(user_id),
            FOREIGN KEY (receiver_id) REFERENCES users(user_id),
            FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id)
        )
        """
    )


def create_file_chunks_table(cursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS file_chunks (
            chunk_id TEXT PRIMARY KEY,
            file_id TEXT,
            chunk_index INTEGER,
            chunk_path TEXT,
            is_received INTEGER,
            FOREIGN KEY (file_id) REFERENCES files(file_id)
        )
        """
    )


# ==============================================================================
# DATABASE QUERIES
# ==============================================================================

def add_user(connection: sqlite3.Connection, user: User):
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO users (
            user_id,
            username,
            public_key,
            ip_address,
            last_seen,
            status
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user.user_id,
            user.username,
            user.public_key,
            user.ip_address,
            user.last_seen,
            user.status,
        ),
    )
    connection.commit()


#create one function that fetches the user data and returns as dict

def get_user_by_id(connection: sqlite3.Connection, user_id: str):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()


def update_user_status(connection: sqlite3.Connection, user_id: str, status: str):
    cursor = connection.cursor()
    cursor.execute(
        """
        UPDATE users
        SET status = ?, last_seen = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """,
        (status, user_id),
    )
    connection.commit()

#link the table with primary / differy key to get the meessage of a particular user

def add_conversation(connection: sqlite3.Connection, conversation: Conversation):
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO conversations (
            conversation_id,
            title,
            created_at,
            last_activity
        ) VALUES (?, ?, ?, ?)
        """,
        (
            conversation.conversation_id,
            conversation.title,
            conversation.created_at,
            conversation.last_activity,
        ),
    )
    connection.commit()

#??

def add_conversation_participant(
    connection: sqlite3.Connection,
    participant: ConversationParticipant,
):
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO conversation_participants (
            participant_id,
            conversation_id,
            user_id,
            joined_at,
            role,
            last_seen
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            participant.participant_id,
            participant.conversation_id,
            participant.user_id,
            participant.joined_at,
            participant.role,
            participant.last_seen,
        ),
    )
    connection.commit()


def get_conversation_by_id(connection: sqlite3.Connection, conversation_id: str):
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,))
    return cursor.fetchone()


def list_conversation_participants(connection: sqlite3.Connection, conversation_id: str):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM conversation_participants WHERE conversation_id = ?",
        (conversation_id,),
    )
    return cursor.fetchall()


def add_message(connection: sqlite3.Connection, message: Message):
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO messages (
            message_id,
            sender_id,
            receiver_id,
            conversation_id,
            encrypted_message,
            timestamp,
            delivery_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            message.message_id,
            message.sender_id,
            message.receiver_id,
            message.conversation_id,
            message.encrypted_message,
            message.timestamp,
            message.delivery_status,
        ),
    )
    connection.commit()

##??

def get_messages_for_conversation(connection: sqlite3.Connection, conversation_id: str):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY timestamp ASC",
        (conversation_id,),
    )
    return cursor.fetchall()


def add_file_metadata(connection: sqlite3.Connection, file_meta: FileMetadata):
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO files (
            file_id,
            sender_id,
            receiver_id,
            conversation_id,
            filename,
            file_size,
            checksum,
            total_chunks,
            transfer_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            file_meta.file_id,
            file_meta.sender_id,
            file_meta.receiver_id,
            file_meta.conversation_id,
            file_meta.filename,
            file_meta.file_size,
            file_meta.checksum,
            file_meta.total_chunks,
            file_meta.transfer_status,
        ),
    )
    connection.commit()

## i dont need this
def add_file_chunk(connection: sqlite3.Connection, chunk: FileChunk):
    cursor = connection.cursor()
    cursor.execute(
        """
        INSERT OR REPLACE INTO file_chunks (
            chunk_id,
            file_id,
            chunk_index,
            chunk_path,
            is_received
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (
            chunk.chunk_id,
            chunk.file_id,
            chunk.chunk_index,
            chunk.chunk_path,
            int(chunk.is_received),
        ),
    )
    connection.commit()

## ?? i dont need this
def mark_file_chunk_received(connection: sqlite3.Connection, chunk_id: str):
    cursor = connection.cursor()
    cursor.execute(
        "UPDATE file_chunks SET is_received = 1 WHERE chunk_id = ?",
        (chunk_id,),
    )
    connection.commit()


def get_file_chunks(connection: sqlite3.Connection, file_id: str):
    cursor = connection.cursor()
    cursor.execute(
        "SELECT * FROM file_chunks WHERE file_id = ? ORDER BY chunk_index ASC",
        (file_id,),
    )
    return cursor.fetchall()


# ==============================================================================
# DATABASE MANAGER
# ==============================================================================

class DatabaseManager:
    def __init__(self):
        self.connection = get_connection()
        initialize_database()

    def close(self):
        self.connection.close()

    def add_user(self, user: User):
        add_user(self.connection, user)

    def get_user(self, user_id: str):
        return get_user_by_id(self.connection, user_id)

    def update_user_status(self, user_id: str, status: str):
        update_user_status(self.connection, user_id, status)

    def add_conversation(self, conversation: Conversation):
        add_conversation(self.connection, conversation)

    def add_participant(self, participant: ConversationParticipant):
        add_conversation_participant(self.connection, participant)

    def get_conversation(self, conversation_id: str):
        return get_conversation_by_id(self.connection, conversation_id)

    def list_participants(self, conversation_id: str):
        return list_conversation_participants(self.connection, conversation_id)

    def add_message(self, message: Message):
        add_message(self.connection, message)

    def get_messages(self, conversation_id: str):
        return get_messages_for_conversation(self.connection, conversation_id)

    def add_file(self, file_meta: FileMetadata):
        add_file_metadata(self.connection, file_meta)

    def add_file_chunk(self, chunk: FileChunk):
        add_file_chunk(self.connection, chunk)

    def mark_chunk_received(self, chunk_id: str):
        mark_file_chunk_received(self.connection, chunk_id)

    def get_file_chunks(self, file_id: str):
        return get_file_chunks(self.connection, file_id)


# ==============================================================================
# MAIN
# ==============================================================================

if __name__ == "__main__":
    initialize_database()
    print("DATABASE INITIALIZED")
