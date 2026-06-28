"""SQLite database setup and helpers for Daily Forge."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Generator

# Database file lives at project root (next to requirements.txt).
DB_PATH = Path(__file__).resolve().parent.parent / "daily_forge.db"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_connection() -> sqlite3.Connection:
    """Return a connection with row factory enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session() -> Generator[sqlite3.Connection, None, None]:
    """Context manager that commits on success and rolls back on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables if they do not exist."""
    with db_session() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS daily_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL UNIQUE,
                posted_at TEXT NOT NULL,
                content TEXT,
                post_type TEXT NOT NULL DEFAULT 'single',
                notes TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_daily_entries_date
                ON daily_entries (entry_date DESC);
            """
        )


def record_entry(
    entry_date: date,
    content: str | None = None,
    post_type: str = "single",
    notes: str | None = None,
) -> dict:
    """Insert or update a daily entry for the given date."""
    date_str = entry_date.isoformat()
    posted_at = _utc_now_iso()

    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO daily_entries (entry_date, posted_at, content, post_type, notes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(entry_date) DO UPDATE SET
                posted_at = excluded.posted_at,
                content = excluded.content,
                post_type = excluded.post_type,
                notes = excluded.notes
            """,
            (date_str, posted_at, content, post_type, notes),
        )
        row = conn.execute(
            "SELECT * FROM daily_entries WHERE entry_date = ?",
            (date_str,),
        ).fetchone()

    return dict(row)


def get_entry(entry_date: date) -> dict | None:
    """Return a single entry by date, or None."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT * FROM daily_entries WHERE entry_date = ?",
            (entry_date.isoformat(),),
        ).fetchone()
    return dict(row) if row else None


def get_all_entry_dates() -> set[str]:
    """Return all dates (YYYY-MM-DD) that have entries."""
    with db_session() as conn:
        rows = conn.execute(
            "SELECT entry_date FROM daily_entries ORDER BY entry_date"
        ).fetchall()
    return {row["entry_date"] for row in rows}


def get_entries_since(since: date) -> list[dict]:
    """Return entries on or after `since`, newest first."""
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT * FROM daily_entries
            WHERE entry_date >= ?
            ORDER BY entry_date DESC
            """,
            (since.isoformat(),),
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent_entries(limit: int = 30) -> list[dict]:
    """Return the most recent entries."""
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT * FROM daily_entries
            ORDER BY entry_date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]