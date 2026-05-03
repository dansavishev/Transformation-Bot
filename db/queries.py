import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from db.database import get_connection


def _conn() -> sqlite3.Connection:
    return get_connection()


# ── Users ──────────────────────────────────────────────────────────────────

def get_or_create_user(telegram_id: int, name: Optional[str] = None, username: Optional[str] = None) -> int:
    conn = _conn()
    with conn:
        row = conn.execute(
            "SELECT user_id FROM users WHERE telegram_id = ?", (telegram_id,)
        ).fetchone()
        if row:
            if username:
                conn.execute(
                    "UPDATE users SET username = ? WHERE telegram_id = ?",
                    (username, telegram_id),
                )
            return row["user_id"]
        cur = conn.execute(
            "INSERT INTO users (telegram_id, name, username) VALUES (?, ?, ?)",
            (telegram_id, name, username),
        )
        user_id = cur.lastrowid
        conn.execute(
            "INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?)", (user_id,)
        )
        return user_id


def get_all_users() -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT u.user_id, u.telegram_id, u.name, u.username, u.created_at,
               MAX(m.created_at) AS last_message_at
        FROM users u
        INNER JOIN messages m ON u.user_id = m.user_id
        GROUP BY u.user_id
        ORDER BY last_message_at DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_user_by_id(user_id: int) -> Optional[dict]:
    conn = _conn()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_telegram_id(telegram_id: int) -> Optional[dict]:
    conn = _conn()
    row = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    return dict(row) if row else None


# ── Messages ───────────────────────────────────────────────────────────────

def save_message(user_id: int, role: str, content: str) -> None:
    conn = _conn()
    with conn:
        conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content),
        )


def get_history(user_id: int, limit: int = 15) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT role, content, created_at FROM messages
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def get_messages_since(user_id: int, hours: Optional[int] = 24) -> list[dict]:
    conn = _conn()
    if hours is None:
        rows = conn.execute(
            "SELECT role, content, created_at FROM messages WHERE user_id = ? ORDER BY created_at ASC",
            (user_id,),
        ).fetchall()
    else:
        since = datetime.utcnow() - timedelta(hours=hours)
        rows = conn.execute(
            """
            SELECT role, content, created_at FROM messages
            WHERE user_id = ? AND created_at >= ?
            ORDER BY created_at ASC
            """,
            (user_id, since.isoformat()),
        ).fetchall()
    return [dict(r) for r in rows]


def get_user_messages_paginated(user_id: int, offset: int = 0, limit: int = 20) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT role, content, created_at FROM messages
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset),
    ).fetchall()
    return [dict(r) for r in reversed(rows)]


def count_user_messages(user_id: int) -> int:
    conn = _conn()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row["cnt"] if row else 0


def get_users_active_since(hours: int = 24) -> list[int]:
    since = datetime.utcnow() - timedelta(hours=hours)
    conn = _conn()
    rows = conn.execute(
        """
        SELECT DISTINCT user_id FROM messages
        WHERE created_at >= ?
        """,
        (since.isoformat(),),
    ).fetchall()
    return [r["user_id"] for r in rows]


# ── Summaries ──────────────────────────────────────────────────────────────

def get_summary(user_id: int) -> Optional[str]:
    conn = _conn()
    row = conn.execute(
        "SELECT summary FROM user_profiles WHERE user_id = ?", (user_id,)
    ).fetchone()
    return row["summary"] if row else None


def update_summary(user_id: int, summary: str) -> None:
    conn = _conn()
    with conn:
        conn.execute(
            """
            INSERT INTO user_profiles (user_id, summary, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                summary = excluded.summary,
                updated_at = excluded.updated_at
            """,
            (user_id, summary),
        )
        conn.execute(
            "INSERT INTO summaries_history (user_id, summary) VALUES (?, ?)",
            (user_id, summary),
        )


def get_users_with_summaries() -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT u.user_id, u.name, u.username, u.telegram_id, p.summary, p.updated_at
        FROM users u
        JOIN user_profiles p ON u.user_id = p.user_id
        WHERE p.summary IS NOT NULL AND p.summary != ''
        ORDER BY p.updated_at DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


def get_user_summaries_history(user_id: int) -> list[dict]:
    conn = _conn()
    rows = conn.execute(
        """
        SELECT summary, created_at FROM summaries_history
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT 10
        """,
        (user_id,),
    ).fetchall()
    return [dict(r) for r in rows]
