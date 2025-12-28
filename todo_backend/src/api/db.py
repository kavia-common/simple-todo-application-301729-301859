import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

# Database file path is configurable via environment variable SQLITE_DB; defaults to local file.
DB_PATH = os.getenv("SQLITE_DB", os.path.join(os.path.dirname(__file__), "..", "todo.db"))

# Ensure directory exists for DB file if nested
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)


def _get_connection() -> sqlite3.Connection:
    """
    Internal: Return a new sqlite3 connection with row factory dict-like access.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db() -> Iterator[sqlite3.Connection]:
    """
    Context manager that yields a SQLite connection and ensures proper cleanup.
    """
    conn = _get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Initialize the database schema if not already present.
    Creates the 'todos' table for storing tasks.
    """
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        # Trigger-like update via on update is not available by default; use update statement to set updated_at.
        # We will set updated_at explicitly in code paths that modify rows.
