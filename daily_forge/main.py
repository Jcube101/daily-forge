"""FastAPI application entry point for Daily Forge."""

from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from daily_forge import __version__
from daily_forge.database import (
    FREEZES_PER_MONTH,
    add_streak_freeze,
    count_freezes_in_month,
    get_all_entries,
    get_all_entry_dates,
    get_all_settings,
    get_entry,
    get_freeze_dates,
    get_freezes_for_month,
    get_recent_entries,
    init_db,
    record_entry,
    set_setting,
)
from daily_forge.models import (
    EntryResponse,
    FreezeRequest,
    FreezeResponse,
    PostRequest,
    PromptResponse,
    SettingsResponse,
    SettingsUpdate,
    StatsResponse,
    ThreadRequest,
    ThreadSplitRequest,
    build_heatmap,
    build_weekly_recap,
    calculate_streaks,
    count_x_characters,
    entries_to_markdown,
    format_thread,
    get_daily_prompt,
    month_key_for_date,
    split_text_to_chunks,
    split_thread_items,
    today_in_timezone,
)

# Project paths.
ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"

DEFAULT_TIMEZONE = "UTC"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Daily Forge",
    description="Build the habit of showing up first.",
    version=__version__,
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


def _resolve_tz(tz: str | None) -> str:
    """Pick timezone from query/body or persisted settings."""
    if tz:
        return tz
    stored = get_all_settings().get("timezone")
    return stored or DEFAULT_TIMEZONE


def _freeze_stats(tz: str) -> tuple[int, int]:
    """Return (used_this_month, remaining) for streak freezes."""
    today = today_in_timezone(tz)
    month_key = month_key_for_date(today)
    used = count_freezes_in_month(month_key)
    return used, max(0, FREEZES_PER_MONTH - used)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """Serve the main application page."""
    return templates.TemplateResponse(
        request,
        "index.html",
        {"version": __version__},
    )


@app.get("/api/health")
async def health() -> dict:
    """Simple health check for monitoring."""
    return {"status": "ok", "version": __version__}


@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings(tz: str | None = Query(None)) -> SettingsResponse:
    """Return user settings (timezone, reminders)."""
    settings = get_all_settings()
    timezone = _resolve_tz(tz)
    used, remaining = _freeze_stats(timezone)
    return SettingsResponse(
        timezone=timezone,
        reminder_enabled=settings.get("reminder_enabled", "false") == "true",
        reminder_time=settings.get("reminder_time", "18:00"),
        freezes_per_month=FREEZES_PER_MONTH,
    )


@app.put("/api/settings", response_model=SettingsResponse)
async def update_settings(body: SettingsUpdate) -> SettingsResponse:
    """Update user settings."""
    if body.timezone is not None:
        set_setting("timezone", body.timezone)
    if body.reminder_enabled is not None:
        set_setting("reminder_enabled", str(body.reminder_enabled).lower())
    if body.reminder_time is not None:
        set_setting("reminder_time", body.reminder_time)

    settings = get_all_settings()
    timezone = settings.get("timezone", DEFAULT_TIMEZONE)
    return SettingsResponse(
        timezone=timezone,
        reminder_enabled=settings.get("reminder_enabled", "false") == "true",
        reminder_time=settings.get("reminder_time", "18:00"),
        freezes_per_month=FREEZES_PER_MONTH,
    )


@app.get("/api/prompt", response_model=PromptResponse)
async def daily_prompt(tz: str | None = Query(None)) -> PromptResponse:
    """Return today's writing prompt."""
    timezone = _resolve_tz(tz)
    today = today_in_timezone(timezone)
    return PromptResponse(prompt=get_daily_prompt(today), date=today.isoformat())


@app.get("/api/stats", response_model=StatsResponse)
async def stats(
    tz: str | None = Query(None),
    weeks: int = Query(52, ge=4, le=52),
) -> StatsResponse:
    """Return streak statistics and heatmap data."""
    timezone = _resolve_tz(tz)
    today = today_in_timezone(timezone)
    entry_dates = get_all_entry_dates()
    freeze_dates = get_freeze_dates()
    entries_by_date = {e["entry_date"]: e for e in get_recent_entries(limit=400)}
    current, longest, status, message = calculate_streaks(
        entry_dates, today, freeze_dates
    )
    used, remaining = _freeze_stats(timezone)

    return StatsResponse(
        current_streak=current,
        longest_streak=longest,
        total_posts=len(entry_dates),
        posted_today=today.isoformat() in entry_dates,
        status=status,
        message=message,
        heatmap=build_heatmap(
            entry_dates,
            today,
            weeks=weeks,
            freeze_dates=freeze_dates,
            entries_by_date=entries_by_date,
        ),
        today=today.isoformat(),
        timezone=timezone,
        freezes_remaining=remaining,
        freezes_used_this_month=used,
    )


@app.get("/api/weekly-recap")
async def weekly_recap(tz: str | None = Query(None)) -> dict:
    """Return this week's posts, streak trend, and summary."""
    timezone = _resolve_tz(tz)
    today = today_in_timezone(timezone)
    since = today - timedelta(days=14)
    entries = [
        e
        for e in get_recent_entries(limit=365)
        if date.fromisoformat(e["entry_date"]) >= since
    ]
    return build_weekly_recap(
        get_all_entry_dates(),
        entries,
        today,
        get_freeze_dates(),
    )


@app.get("/api/today", response_model=EntryResponse | None)
async def today_entry(tz: str | None = Query(None)) -> EntryResponse | None:
    """Return today's entry if it exists."""
    timezone = _resolve_tz(tz)
    today = today_in_timezone(timezone)
    entry = get_entry(today)
    return EntryResponse(**entry) if entry else None


@app.get("/api/entries", response_model=list[EntryResponse])
async def list_entries(days: int = 90) -> list[EntryResponse]:
    """Return recent entries within the last N days."""
    since = date.today() - timedelta(days=days)
    entries = [
        e
        for e in get_recent_entries(limit=days)
        if date.fromisoformat(e["entry_date"]) >= since
    ]
    return [EntryResponse(**e) for e in entries]


@app.get("/api/freezes", response_model=list[FreezeResponse])
async def list_freezes(tz: str | None = Query(None)) -> list[FreezeResponse]:
    """Return streak freezes used in the current month."""
    timezone = _resolve_tz(tz)
    today = today_in_timezone(timezone)
    month_key = month_key_for_date(today)
    return [FreezeResponse(**f) for f in get_freezes_for_month(month_key)]


@app.post("/api/freeze", response_model=FreezeResponse)
async def use_freeze(body: FreezeRequest) -> FreezeResponse:
    """Use a streak freeze on a missed day."""
    timezone = _resolve_tz(body.timezone)
    today = today_in_timezone(timezone)

    try:
        freeze_day = date.fromisoformat(body.freeze_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid date format") from exc

    if freeze_day >= today:
        raise HTTPException(status_code=400, detail="Can only freeze past days")

    entry_dates = get_all_entry_dates()
    freeze_dates = get_freeze_dates()
    date_str = freeze_day.isoformat()

    if date_str in entry_dates:
        raise HTTPException(status_code=400, detail="Already posted that day")
    if date_str in freeze_dates:
        raise HTTPException(status_code=400, detail="Already frozen that day")

    month_key = month_key_for_date(today)
    if count_freezes_in_month(month_key) >= FREEZES_PER_MONTH:
        raise HTTPException(status_code=400, detail="No streak freezes left this month")

    record = add_streak_freeze(freeze_day, month_key)
    return FreezeResponse(**record)


@app.post("/api/post", response_model=EntryResponse)
async def mark_posted(body: PostRequest) -> EntryResponse:
    """Record or update today's post — maintains the streak."""
    timezone = _resolve_tz(body.timezone)
    today = today_in_timezone(timezone)
    entry = record_entry(
        entry_date=today,
        content=body.content,
        post_type=body.post_type,
        notes=body.notes,
    )
    return EntryResponse(**entry)


@app.post("/api/thread/format")
async def format_thread_endpoint(body: ThreadRequest) -> dict:
    """Convert numbered list items into a formatted thread."""
    formatted = format_thread(body.items)
    return {
        "formatted": formatted,
        "tweet_count": len([i for i in body.items if i.strip()]),
    }


@app.post("/api/thread/split")
async def split_thread_endpoint(body: ThreadSplitRequest) -> dict:
    """Split thread items or raw text into <280 char numbered chunks."""
    if body.items:
        chunks = split_thread_items(body.items, body.max_len)
    elif body.text:
        raw = split_text_to_chunks(body.text.strip(), body.max_len)
        total = len(raw)
        chunks = [
            {
                "index": i,
                "total": total,
                "text": part,
                "chars": len(part),
                "weighted_chars": count_x_characters(part),
            }
            for i, part in enumerate(raw, start=1)
        ]
    else:
        raise HTTPException(status_code=400, detail="Provide items or text")

    return {"chunks": chunks, "chunk_count": len(chunks)}


@app.post("/api/char-count")
async def char_count_endpoint(body: dict) -> dict:
    """Return X-weighted and raw character counts."""
    text = body.get("text", "")
    return {
        "raw": len(text),
        "weighted": count_x_characters(text),
        "limit": 280,
        "over_limit": count_x_characters(text) > 280,
    }


@app.get("/api/export/markdown", response_class=PlainTextResponse)
async def export_markdown() -> PlainTextResponse:
    """Export full post history as Markdown."""
    entries = get_all_entries()
    freeze_dates = get_freeze_dates()
    content = entries_to_markdown(entries, freeze_dates)
    return PlainTextResponse(
        content,
        media_type="text/markdown",
        headers={
            "Content-Disposition": 'attachment; filename="daily-forge-history.md"'
        },
    )