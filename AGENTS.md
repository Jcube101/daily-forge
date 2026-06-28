# AGENTS.md — Context for AI coding agents

This file helps AI agents work effectively in the Daily Forge codebase.

## What this project is

Daily Forge is a **local-first habit tracker** for daily social media posting. Philosophy: **show up first, content tools later**. No OAuth or social APIs in v1.

**Current version:** 0.2.0 (Phase 2 — polish & retention)

## Tech stack

| Layer | Choice |
|-------|--------|
| Backend | Python 3.11+, FastAPI, uvicorn, lifespan handler |
| Frontend | Jinja2 template + modular vanilla JS + custom CSS |
| Database | SQLite (`daily_forge.db` at project root) |
| Validation | Pydantic v2 |
| Tests | pytest + httpx TestClient |
| PWA | manifest.json + service worker (`static/sw.js`) |

## Key files

| File | Purpose |
|------|---------|
| `daily_forge/main.py` | FastAPI routes, lifespan, static mount |
| `daily_forge/database.py` | SQLite schema: entries, settings, freezes |
| `daily_forge/models.py` | Streak logic, timezone, heatmap, thread split, recap |
| `templates/index.html` | Main UI (served at `/`) |
| `static/app.js` | Main client orchestration |
| `static/js/*.js` | Modular features (settings, drafts, onboarding, etc.) |
| `static/sw.js` | Service worker — offline cache + notifications |
| `tests/test_models.py` | Streak/timezone/char-count unit tests |
| `tests/test_api.py` | API integration tests |

## Architecture decisions

1. **Single-user local app** — no auth, no multi-tenancy.
2. **Streak = calendar day in user timezone** — client sends `tz` query param or stores in settings.
3. **Streak freezes** — 2 per month; stored in `streak_freezes` table; count as posted for streak math.
4. **Manual posting workflow** — copy → paste externally → mark posted.
5. **Drafts in localStorage** — server stores only completed posts; drafts are client-side.
6. **Jinja2 + vanilla JS** — not a SPA.

## Timezone flow

- Browser detects IANA timezone via `Intl.DateTimeFormat`.
- Stored in `localStorage` (`df-timezone`) and synced to `app_settings` table.
- All streak/date APIs accept `?tz=America/New_York`.
- `POST /api/post` accepts `timezone` in body.

## Common tasks

### Add a new API endpoint

1. Add Pydantic model in `models.py` if needed.
2. Add route in `main.py`.
3. Wire up in `static/app.js` or a `static/js/*.js` module.

### Change streak logic

Edit `calculate_streaks()` in `models.py`. Add/update tests in `tests/test_models.py`.

### Run tests

```bash
pytest tests/ -v
```

## What NOT to do

- Do not add social media API integrations without explicit request.
- Do not replace vanilla JS with React/Vue unless asked.
- Do not commit `daily_forge.db` (gitignored).

## Documentation map

- `SPEC.md` — technical specification
- `ROADMAP.md` — planned features by phase
- `LEARNINGS.md` — decisions made during builds
- `CONTRIBUTING.md` — how to contribute