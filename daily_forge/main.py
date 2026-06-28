"""FastAPI application entry point for Daily Forge."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from daily_forge import __version__
from daily_forge.database import (
    get_all_entry_dates,
    get_entry,
    get_recent_entries,
    init_db,
    record_entry,
)
from daily_forge.models import (
    EntryResponse,
    PostRequest,
    PromptResponse,
    StatsResponse,
    ThreadRequest,
    build_heatmap,
    calculate_streaks,
    format_thread,
    get_daily_prompt,
)

# Project paths.
ROOT_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"

app = FastAPI(
    title="Daily Forge",
    description="Build the habit of showing up first.",
    version=__version__,
)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.on_event("startup")
def on_startup() -> None:
    """Initialize database on first run."""
    init_db()


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


@app.get("/api/prompt", response_model=PromptResponse)
async def daily_prompt() -> PromptResponse:
    """Return today's writing prompt."""
    today = date.today()
    return PromptResponse(prompt=get_daily_prompt(today), date=today.isoformat())


@app.get("/api/stats", response_model=StatsResponse)
async def stats() -> StatsResponse:
    """Return streak statistics and heatmap data."""
    today = date.today()
    entry_dates = get_all_entry_dates()
    current, longest, status, message = calculate_streaks(entry_dates, today)

    return StatsResponse(
        current_streak=current,
        longest_streak=longest,
        total_posts=len(entry_dates),
        posted_today=today.isoformat() in entry_dates,
        status=status,
        message=message,
        heatmap=build_heatmap(entry_dates, today),
        today=today.isoformat(),
    )


@app.get("/api/today", response_model=EntryResponse | None)
async def today_entry() -> EntryResponse | None:
    """Return today's entry if it exists."""
    entry = get_entry(date.today())
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


@app.post("/api/post", response_model=EntryResponse)
async def mark_posted(body: PostRequest) -> EntryResponse:
    """Record or update today's post — maintains the streak."""
    entry = record_entry(
        entry_date=date.today(),
        content=body.content,
        post_type=body.post_type,
        notes=body.notes,
    )
    return EntryResponse(**entry)


@app.post("/api/thread/format")
async def format_thread_endpoint(body: ThreadRequest) -> dict:
    """Convert numbered list items into a formatted thread."""
    formatted = format_thread(body.items)
    return {"formatted": formatted, "tweet_count": len([i for i in body.items if i.strip()])}