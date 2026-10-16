
import sqlite3
from datetime import datetime, timezone
from uuid import uuid4

from app.core.config import DB_PATH


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat(timespec="seconds")


def get_connection():
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=10
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


def init_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL
                    CHECK(role IN ('user', 'assistant')),
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id)
                    REFERENCES conversations(id)
                    ON DELETE CASCADE
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_messages_conversation
            ON messages(conversation_id, id)
        """)


def create_conversation(title="New Conversation"):
    conversation_id = str(uuid4())

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO conversations
            (id, title, created_at)
            VALUES (?, ?, ?)
            """,
            (
                conversation_id,
                title,
                utc_now()
            )
        )

    return conversation_id


def get_conversations():
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, title, created_at
            FROM conversations
            ORDER BY created_at DESC, rowid DESC
        """).fetchall()

    return [dict(row) for row in rows]


def get_messages(conversation_id):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = ?
            ORDER BY id ASC
            """,
            (conversation_id,)
        ).fetchall()

    return [dict(row) for row in rows]


def save_message(conversation_id, role, content):
    if role not in ("user", "assistant"):
        raise ValueError("Invalid message role.")

    if not content.strip():
        raise ValueError("Message cannot be empty.")

    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO messages
            (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                conversation_id,
                role,
                content,
                utc_now()
            )
        )


def update_conversation_title(
    conversation_id,
    title
):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE conversations
            SET title = ?
            WHERE id = ?
            """,
            (title, conversation_id)
        )


def delete_conversation(conversation_id):
    with get_connection() as conn:
        conn.execute(
            """
            DELETE FROM conversations
            WHERE id = ?
            """,
            (conversation_id,)
        )
