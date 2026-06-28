"""Pydantic models, streak logic, and daily prompts."""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone as std_timezone
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, Field

from daily_forge.database import FREEZES_PER_MONTH

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

# X/Twitter counts URLs as 23 characters (t.co wrapping).
X_URL_WEIGHT = 23
URL_PATTERN = re.compile(r"https?://\S+")


def resolve_timezone(tz: str | None) -> ZoneInfo:
    """Return a valid ZoneInfo, falling back to UTC."""
    candidates = [tz, "UTC"] if tz else ["UTC"]
    for name in candidates:
        if not name:
            continue
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError:
            continue
    # Last resort when tzdata is unavailable (should not happen with tzdata dep).
    return ZoneInfo("UTC")


def today_in_timezone(tz: str | None = None) -> date:
    """Return today's date in the given IANA timezone."""
    try:
        zone = resolve_timezone(tz)
        return datetime.now(zone).date()
    except ZoneInfoNotFoundError:
        return datetime.now(std_timezone.utc).date()


def month_key_for_date(d: date) -> str:
    """Return YYYY-MM for freeze monthly limits."""
    return d.strftime("%Y-%m")


def get_daily_prompt(for_date: date | None = None) -> str:
    """Return the prompt for a given date (stable per calendar day)."""
    target = for_date or date.today()
    index = target.timetuple().tm_yday % len(DAILY_PROMPTS)
    return DAILY_PROMPTS[index]


def effective_dates(
    entry_dates: set[str],
    freeze_dates: set[str],
) -> set[str]:
    """Merge posted days with streak-freeze protected days."""
    return entry_dates | freeze_dates


def calculate_streaks(
    entry_dates: set[str],
    today: date | None = None,
    freeze_dates: set[str] | None = None,
) -> tuple[int, int, str, str]:
    """
    Compute current streak, longest streak, and status message.

    Streak rules:
    - Posting any time during a calendar day counts for that day.
    - Streak freezes count as posted days for streak continuity.
    - If today is not covered yet, the streak still holds until midnight.
    """
    today = today or date.today()
    today_str = today.isoformat()
    yesterday = today - timedelta(days=1)
    yesterday_str = yesterday.isoformat()
    active = effective_dates(entry_dates, freeze_dates or set())

    anchor = today if today_str in active else yesterday
    current = 0
    cursor = anchor
    while cursor.isoformat() in active:
        current += 1
        cursor -= timedelta(days=1)

    longest = 0
    if active:
        sorted_dates = sorted(date.fromisoformat(d) for d in active)
        run = 1
        longest = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
                run += 1
                longest = max(longest, run)
            else:
                run = 1

    if today_str in active:
        status = "posted_today"
        message = "You showed up today. Keep the momentum going."
    elif yesterday_str in active:
        status = "at_risk"
        message = (
            "You haven't posted yet today — your streak is still alive. "
            "Show up before midnight."
        )
    elif current == 0 and active:
        status = "broken"
        message = (
            "Your streak reset, and that's okay. Today is a fresh start — just show up."
        )
    else:
        status = "new"
        message = "Welcome! Post once today to start your streak."

    return current, longest, status, message


def build_heatmap(
    entry_dates: set[str],
    today: date | None = None,
    weeks: int = 52,
    freeze_dates: set[str] | None = None,
) -> list[dict]:
    """Build GitHub-style heatmap: exactly N weeks ending on today."""
    today = today or date.today()
    active = effective_dates(entry_dates, freeze_dates or set())
    # Rolling window: 52*7 days inclusive, anchored on today (no future dates).
    start = today - timedelta(days=weeks * 7 - 1)

    cells: list[dict] = []
    cursor = start
    while cursor <= today:
        date_str = cursor.isoformat()
        posted = date_str in entry_dates
        frozen = date_str in (freeze_dates or set())
        covered = date_str in active
        cells.append(
            {
                "date": date_str,
                "count": 1 if covered else 0,
                "level": 4 if posted else (2 if frozen else 0),
                "frozen": frozen,
            }
        )
        cursor += timedelta(days=1)

    return cells


def count_x_characters(text: str) -> int:
    """X-style weighted count: URLs count as 23 characters each."""
    if not text:
        return 0

    urls = URL_PATTERN.findall(text)
    url_chars = sum(len(u) for u in urls)
    weighted_url_chars = len(urls) * X_URL_WEIGHT
    return len(text) - url_chars + weighted_url_chars


def split_text_to_chunks(text: str, max_len: int = 280) -> list[str]:
    """Split text into chunks under max_len, preferring word boundaries."""
    text = text.strip()
    if not text:
        return []
    if count_x_characters(text) <= max_len:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if count_x_characters(remaining) <= max_len:
            chunks.append(remaining.strip())
            break

        # Greedy split: find largest prefix that fits.
        low, high = 1, len(remaining)
        best = 1
        while low <= high:
            mid = (low + high) // 2
            candidate = remaining[:mid]
            if count_x_characters(candidate) <= max_len:
                best = mid
                low = mid + 1
            else:
                high = mid - 1

        piece = remaining[:best]
        # Prefer breaking at last space in the piece.
        if best < len(remaining):
            space_idx = piece.rfind(" ")
            if space_idx > max_len // 4:
                piece = piece[:space_idx]
                best = space_idx + 1 if space_idx >= 0 else best

        piece = piece.strip()
        if piece:
            chunks.append(piece)
        remaining = remaining[best:].strip()

    return chunks


def split_thread_items(items: list[str], max_len: int = 280) -> list[dict]:
    """
    Split thread items into numbered tweet chunks under max_len.

    Returns list of { index, total, text, chars, weighted_chars }.
    """
    cleaned = [item.strip() for item in items if item.strip()]
    if not cleaned:
        return []

    # Reserve space for numbering prefix like "12/12 ".
    body_max = max(max_len - 8, 50)
    raw_chunks: list[str] = []
    for item in cleaned:
        raw_chunks.extend(split_text_to_chunks(item, body_max))

    total = len(raw_chunks)
    result: list[dict] = []
    for i, chunk in enumerate(raw_chunks, start=1):
        prefix = f"{i}/{total} "
        available = max_len - count_x_characters(prefix)
        if count_x_characters(chunk) > available:
            chunk = split_text_to_chunks(chunk, available)[0] if available > 0 else chunk[:50]
        text = prefix + chunk
        result.append(
            {
                "index": i,
                "total": total,
                "text": text,
                "chars": len(text),
                "weighted_chars": count_x_characters(text),
            }
        )

    return result


def build_weekly_recap(
    entry_dates: set[str],
    entries: list[dict],
    today: date,
    freeze_dates: set[str] | None = None,
) -> dict:
    """Build weekly recap: posts this week, daily trend, summary."""
    freeze_dates = freeze_dates or set()
    active = effective_dates(entry_dates, freeze_dates)

    # Week starts Monday (ISO).
    week_start = today - timedelta(days=today.weekday())
    week_days: list[dict] = []

    for i in range(7):
        d = week_start + timedelta(days=i)
        d_str = d.isoformat()
        posted = d_str in entry_dates
        frozen = d_str in freeze_dates
        entry = next((e for e in entries if e["entry_date"] == d_str), None)
        week_days.append(
            {
                "date": d_str,
                "day_label": d.strftime("%a"),
                "posted": posted,
                "frozen": frozen,
                "covered": d_str in active,
                "content_preview": (entry["content"] or "")[:80] if entry else None,
            }
        )

    posts_this_week = sum(1 for d in week_days if d["posted"])
    days_covered = sum(1 for d in week_days if d["covered"])

    # Streak trend: last 7 days ending today.
    trend: list[dict] = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        d_str = d.isoformat()
        trend.append(
            {
                "date": d_str,
                "day_label": d.strftime("%a"),
                "covered": d_str in active,
            }
        )

    current, longest, _, _ = calculate_streaks(entry_dates, today, freeze_dates)

    return {
        "week_start": week_start.isoformat(),
        "week_end": (week_start + timedelta(days=6)).isoformat(),
        "posts_this_week": posts_this_week,
        "days_covered": days_covered,
        "current_streak": current,
        "longest_streak": longest,
        "week_days": week_days,
        "streak_trend": trend,
    }


def entries_to_markdown(entries: list[dict], freeze_dates: set[str]) -> str:
    """Export full history as clean Markdown."""
    lines = [
        "# Daily Forge — Post History",
        "",
        f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
    ]

    if not entries and not freeze_dates:
        lines.append("*No posts yet. Your story starts with day one.*")
        return "\n".join(lines)

    for entry in entries:
        d = entry["entry_date"]
        frozen = d in freeze_dates
        badge = " 🧊" if frozen and entry.get("content") is None else ""
        lines.append(f"## {d}{badge}")
        lines.append("")
        if entry.get("content"):
            lines.append(entry["content"])
            lines.append("")
        lines.append(f"- **Type:** {entry.get('post_type', 'single')}")
        lines.append(f"- **Posted at:** {entry.get('posted_at', '—')}")
        if frozen:
            lines.append("- **Streak freeze:** used on this day")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Freezes without entries.
    orphan_freezes = freeze_dates - {e["entry_date"] for e in entries}
    for d in sorted(orphan_freezes):
        lines.append(f"## {d} 🧊")
        lines.append("")
        lines.append("*Streak freeze — no post content recorded.*")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


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


# --- Pydantic models ---


class PostRequest(BaseModel):
    """Request body for recording a daily post."""

    content: str | None = None
    post_type: Literal["single", "thread"] = "single"
    notes: str | None = None
    timezone: str | None = None


class ThreadRequest(BaseModel):
    """Request body for formatting a numbered thread."""

    items: list[str] = Field(..., min_length=1)


class ThreadSplitRequest(BaseModel):
    """Request body for splitting thread items into tweet chunks."""

    items: list[str] = Field(default_factory=list)
    text: str | None = None
    max_len: int = Field(default=280, ge=50, le=3000)


class FreezeRequest(BaseModel):
    """Request body for using a streak freeze on a missed day."""

    freeze_date: str  # YYYY-MM-DD
    timezone: str | None = None


class SettingsUpdate(BaseModel):
    """Partial settings update."""

    timezone: str | None = None
    reminder_enabled: bool | None = None
    reminder_time: str | None = None  # HH:MM (24h, user local)


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
    timezone: str
    freezes_remaining: int
    freezes_used_this_month: int


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


class FreezeResponse(BaseModel):
    """A streak freeze record."""

    id: int
    freeze_date: str
    month_key: str
    used_at: str


class SettingsResponse(BaseModel):
    """User settings."""

    timezone: str
    reminder_enabled: bool
    reminder_time: str
    freezes_per_month: int = FREEZES_PER_MONTH