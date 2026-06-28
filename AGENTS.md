# AGENTS.md — Context for AI coding agents

This file helps AI agents work effectively in the Daily Forge codebase.

## What this project is

Daily Forge is a **local-first habit tracker** for daily social media posting. Philosophy: **show up first, content tools later**. No OAuth or social APIs in v1.

## Tech stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3.11+, FastAPI, uvicorn |
| Frontend | Jinja2 template + vanilla JS + custom CSS (Tailwind CDN for utilities only) |
| Database | SQLite (`daily_forge.db` at project root) |
| Validation | Pydantic v2 |

## Key files

| File | Purpose |
|------|---------|
| `daily_forge/main.py` | FastAPI routes, app startup, static mount |
| `daily_forge/database.py` | SQLite schema, CRUD for `daily_entries` |
| `daily_forge/models.py` | Streak logic, heatmap builder, prompts, Pydantic models |
| `templates/index.html` | Main UI (served at `/`) |
| `static/app.js` | Client API calls, heatmap render, copy/thread UX |
| `static/style.css` | Design system (CSS variables, dark mode) |

## Architecture decisions

1. **Single-user local app** — no auth, no multi-tenancy. One SQLite file per install.
2. **Streak = calendar day posted** — `entry_date` is `YYYY-MM-DD`. Grace period until end of day.
3. **Manual posting workflow** — user copies text, posts externally, clicks "Mark as posted".
4. **Jinja2 for HTML** — not a SPA. API is JSON for dynamic sections only.

## Common tasks

### Add a new API endpoint

1. Add Pydantic model in `models.py` if needed.
2. Add route in `main.py`.
3. Wire up in `static/app.js`.

### Change streak logic

Edit `calculate_streaks()` in `models.py`. Update tests if added later.

### Change UI

- Layout/structure: `templates/index.html`
- Behavior: `static/app.js`
- Styling: `static/style.css` (prefer CSS variables in `:root`)

## Running locally

```bash
python -m venv venv
source venv/Scripts/activate  # Windows Git Bash
pip install -r requirements.txt
uvicorn daily_forge.main:app --reload
```

Or `run.bat` on Windows.

## What NOT to do (v1 scope)

- Do not add social media API integrations without explicit request.
- Do not add user accounts / auth unless migrating to multi-user.
- Do not replace vanilla JS with React/Vue unless asked.
- Do not commit `daily_forge.db` (gitignored).

## Deployment target

Windows local dev first. Future: Raspberry Pi via systemd + Cloudflare Tunnel (see `SPEC.md`).

## Documentation map

- `SPEC.md` — technical specification
- `ROADMAP.md` — planned features by phase
- `LEARNINGS.md` — decisions made during initial build
- `CONTRIBUTING.md` — how to contribute