"""Pydantic models, streak logic, and daily prompts."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field

# Rotating daily prompts — indexed by day-of-year for consistency.
DAILY_PROMPTS: list[str] = [
    "What's one thing you want to share today?",
    "What did you learn recently that others might find useful?",
    "What's a small win you had this week?",
    "What question are you thinking about right now?",
    "Share one tip from your area of expertise.",
    "What book, article, or podcast inspired you lately?",
    "What's a mistake you made and what did it teach you?",
    "What are you working on that excites you?",
    "Share a contrarian opinion you hold.",
    "What's one habit that's changed your life?",
    "What tool or resource do you recommend?",
    "What would you tell your past self?",
    "Share a story from your career journey.",
    "What's something underrated in your field?",
    "What are you grateful for today?",
    "Describe a problem you're trying to solve.",
    "What's a hot take you can defend?",
    "Share a framework you use regularly.",
    "What surprised you this week?",
    "What's one thing you'd do differently?",
    "Share progress on something you're building.",
    "What conversation changed your perspective?",
    "What's a myth in your industry?",
    "Share a quote that stuck with you.",
    "What skill are you currently developing?",
    "What's your take on a trending topic?",
    "Share something you wish more people knew.",
    "What does 'showing up' mean to you today?",
    "What's one actionable insight from today?",
    "Why is consistency more important than perfection?",
    "What will you share before the day ends?",
]


def get_daily_prompt(for_date: date | None = None) -> str:
    """Return the prompt for a given date (stable per calendar day)."""
    target = for_date or date.today()
    index = target.timetuple().tm_yday % len(DAILY_PROMPTS)
    return DAILY_PROMPTS[index]


def calculate_streaks(
    entry_dates: set[str],
    today: date | None = None,
) -> tuple[int, int, str, str]:
    """
    Compute current streak, longest streak, and status message.

    Streak rules:
    - Posting any time during a calendar day counts for that day.
    - If today is not posted yet, the streak still holds (grace until midnight).
    - Missing yesterday breaks the streak unless today is already posted.
    """
    today = today or date.today()
    today_str = today.isoformat()
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.isoformat()

    # Current streak: count consecutive days ending at today or yesterday.
    anchor = today if today_str in entry_dates else yesterday
    current = 0
    cursor = anchor
    while cursor.isoformat() in entry_dates:
        current += 1
        cursor -= timedelta(days=1)

    # Longest streak across all history.
    longest = 0
    if entry_dates:
        sorted_dates = sorted(date.fromisoformat(d) for d in entry_dates)
        run = 1
        longest = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
                run += 1
                longest = max(longest, run)
            else:
                run = 1

    # Gentle status messaging.
    if today_str in entry_dates:
        status = "posted_today"
        message = "You showed up today. Keep the momentum going."
    elif yesterday_str in entry_dates:
        status = "at_risk"
        message = "You haven't posted yet today — your streak is still alive. Show up before midnight."
    elif current == 0 and entry_dates:
        status = "broken"
        message = "Your streak reset, and that's okay. Today is a fresh start — just show up."
    else:
        status = "new"
        message = "Welcome! Post once today to start your streak."

    return current, longest, status, message


def build_heatmap(
    entry_dates: set[str],
    today: date | None = None,
    weeks: int = 52,
) -> list[dict]:
    """
    Build GitHub-style heatmap data for the last N weeks.

    Each cell: { date, count, level } where level is 0-4 for color intensity.
    """
    today = today or date.today()
    # Align to end of current week (Sunday).
    days_since_sunday = (today.weekday() + 1) % 7
    end = today
    start = end - timedelta(days=(weeks * 7) + days_since_sunday - 1)

    cells: list[dict] = []
    cursor = start
    while cursor <= end:
        date_str = cursor.isoformat()
        posted = date_str in entry_dates
        cells.append(
            {
                "date": date_str,
                "count": 1 if posted else 0,
                "level": 4 if posted else 0,
            }
        )
        cursor += timedelta(days=1)

    return cells


class PostRequest(BaseModel):
    """Request body for recording a daily post."""

    content: str | None = None
    post_type: Literal["single", "thread"] = "single"
    notes: str | None = None


class ThreadRequest(BaseModel):
    """Request body for formatting a numbered thread."""

    items: list[str] = Field(..., min_length=1)


class StatsResponse(BaseModel):
    """Streak and activity statistics."""

    current_streak: int
    longest_streak: int
    total_posts: int
    posted_today: bool
    status: str
    message: str
    heatmap: list[dict]
    today: str


class PromptResponse(BaseModel):
    """Daily writing prompt."""

    prompt: str
    date: str


class EntryResponse(BaseModel):
    """A single daily entry."""

    id: int
    entry_date: str
    posted_at: str
    content: str | None
    post_type: str
    notes: str | None


def format_thread(items: list[str]) -> str:
    """Format a list of points into a numbered social thread."""
    cleaned = [item.strip() for item in items if item.strip()]
    if not cleaned:
        return ""

    parts: list[str] = []
    total = len(cleaned)
    for i, item in enumerate(cleaned, start=1):
        parts.append(f"{i}/{total} {item}")
    return "\n\n".join(parts)