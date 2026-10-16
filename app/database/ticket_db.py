
import hashlib
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


DB_PATH = Path(
    os.getenv("TICKET_DB_PATH", "data/support_tickets.db")
)

VALID_STATUSES = {
    "open",
    "in_progress",
    "resolved",
    "closed",
}

VALID_PRIORITIES = {"low", "medium", "high"}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        DB_PATH,
        timeout=15,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA busy_timeout = 15000")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_ticket_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_id TEXT UNIQUE,
                customer_id TEXT NOT NULL,
                customer_message TEXT NOT NULL,
                intent TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                urgency TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                summary TEXT NOT NULL,
                message_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(customer_id, message_hash)
            )
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickets_status
            ON tickets(status)
        """)

        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tickets_priority
            ON tickets(priority)
        """)


def message_fingerprint(message):
    normalized = " ".join(message.casefold().split())
    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def create_ticket(
    customer_id,
    customer_message,
    classification,
):
    customer_id = customer_id.strip()
    customer_message = customer_message.strip()

    if not customer_id or not customer_message:
        raise ValueError(
            "Customer ID and message are required."
        )

    init_ticket_db()

    fingerprint = message_fingerprint(customer_message)
    now = utc_now()

    with get_connection() as conn:
        existing = conn.execute(
            """
            SELECT ticket_id
            FROM tickets
            WHERE customer_id = ?
              AND message_hash = ?
            """,
            (customer_id, fingerprint),
        ).fetchone()

        if existing:
            return {
                "ticket_id": existing["ticket_id"],
                "created": False,
                "reason": "duplicate",
            }

        try:
            cursor = conn.execute(
                """
                INSERT INTO tickets (
                    customer_id,
                    customer_message,
                    intent,
                    sentiment,
                    urgency,
                    priority,
                    status,
                    summary,
                    message_hash,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    customer_id,
                    customer_message,
                    classification["intent"],
                    classification["sentiment"],
                    classification["urgency"],
                    classification["urgency"],
                    "open",
                    classification["summary"],
                    fingerprint,
                    now,
                    now,
                ),
            )
        except sqlite3.IntegrityError:
            existing = conn.execute(
                """
                SELECT ticket_id
                FROM tickets
                WHERE customer_id = ?
                  AND message_hash = ?
                """,
                (customer_id, fingerprint),
            ).fetchone()

            if existing:
                return {
                    "ticket_id": existing["ticket_id"],
                    "created": False,
                    "reason": "duplicate",
                }
            raise

        ticket_id = f"TKT-{cursor.lastrowid:06d}"

        conn.execute(
            """
            UPDATE tickets
            SET ticket_id = ?
            WHERE id = ?
            """,
            (ticket_id, cursor.lastrowid),
        )

        return {
            "ticket_id": ticket_id,
            "created": True,
            "reason": "created",
        }


def get_ticket(ticket_id):
    init_ticket_db()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM tickets
            WHERE ticket_id = ?
            """,
            (ticket_id,),
        ).fetchone()

        return dict(row) if row else None


def list_tickets(status=None, priority=None, limit=100):
    init_ticket_db()

    if status is not None and status not in VALID_STATUSES:
        raise ValueError("Invalid ticket status.")

    if priority is not None and priority not in VALID_PRIORITIES:
        raise ValueError("Invalid ticket priority.")

    limit = max(1, min(int(limit), 500))

    query = "SELECT * FROM tickets WHERE 1=1"
    params = []

    if status:
        query += " AND status = ?"
        params.append(status)

    if priority:
        query += " AND priority = ?"
        params.append(priority)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    with get_connection() as conn:
        rows = conn.execute(
            query,
            params,
        ).fetchall()

        return [dict(row) for row in rows]


def update_ticket_status(ticket_id, new_status):
    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid status: {new_status}"
        )

    init_ticket_db()

    with get_connection() as conn:
        cursor = conn.execute(
            """
            UPDATE tickets
            SET status = ?,
                updated_at = ?
            WHERE ticket_id = ?
            """,
            (
                new_status,
                utc_now(),
                ticket_id,
            ),
        )

        return cursor.rowcount > 0


def get_ticket_stats():
    init_ticket_db()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT status, COUNT(*) AS total
            FROM tickets
            GROUP BY status
        """).fetchall()

        stats = {
            "open": 0,
            "in_progress": 0,
            "resolved": 0,
            "closed": 0,
        }

        for row in rows:
            stats[row["status"]] = row["total"]

        stats["total"] = sum(stats.values())
        return stats
