"""SQLite database setup and helpers for Daily Forge."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Generator

# Database file lives at project root (next to requirements.txt).
DB_PATH = Path(__file__).resolve().parent.parent / "daily_forge.db"

# Grace tokens allowed per calendar month (user timezone).
FREEZES_PER_MONTH = 2


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

            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS streak_freezes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                freeze_date TEXT NOT NULL UNIQUE,
                month_key TEXT NOT NULL,
                used_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_streak_freezes_month
                ON streak_freezes (month_key);
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


def get_all_entries() -> list[dict]:
    """Return all entries, oldest first."""
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM daily_entries ORDER BY entry_date ASC"
        ).fetchall()
    return [dict(row) for row in rows]


# --- Settings ---


def get_setting(key: str, default: str | None = None) -> str | None:
    """Return a single app setting value."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT value FROM app_settings WHERE key = ?",
            (key,),
        ).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    """Upsert an app setting."""
    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO app_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )


def get_all_settings() -> dict[str, str]:
    """Return all settings as a dict."""
    with db_session() as conn:
        rows = conn.execute("SELECT key, value FROM app_settings").fetchall()
    return {row["key"]: row["value"] for row in rows}


# --- Streak freezes ---


def get_freeze_dates() -> set[str]:
    """Return all dates protected by a streak freeze."""
    with db_session() as conn:
        rows = conn.execute("SELECT freeze_date FROM streak_freezes").fetchall()
    return {row["freeze_date"] for row in rows}


def get_freezes_for_month(month_key: str) -> list[dict]:
    """Return freezes used in a given YYYY-MM month."""
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT * FROM streak_freezes
            WHERE month_key = ?
            ORDER BY freeze_date DESC
            """,
            (month_key,),
        ).fetchall()
    return [dict(row) for row in rows]


def count_freezes_in_month(month_key: str) -> int:
    """Count how many freezes were used in a month."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM streak_freezes WHERE month_key = ?",
            (month_key,),
        ).fetchone()
    return int(row["cnt"])


def add_streak_freeze(freeze_date: date, month_key: str) -> dict:
    """Record a streak freeze for a missed day."""
    used_at = _utc_now_iso()
    date_str = freeze_date.isoformat()

    with db_session() as conn:
        conn.execute(
            """
            INSERT INTO streak_freezes (freeze_date, month_key, used_at)
            VALUES (?, ?, ?)
            """,
            (date_str, month_key, used_at),
        )
        row = conn.execute(
            "SELECT * FROM streak_freezes WHERE freeze_date = ?",
            (date_str,),
        ).fetchone()

    return dict(row)