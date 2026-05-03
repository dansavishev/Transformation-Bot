import sqlite3
from pathlib import Path
from config import DB_PATH
from db.models import ALL_TABLES


def get_connection() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    with conn:
        for ddl in ALL_TABLES:
            conn.execute(ddl)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN username TEXT")
        except Exception:
            pass
    conn.close()
