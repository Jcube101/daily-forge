# LEARNINGS.md

Decisions and learnings from building Daily Forge v0.1.

## Architecture

### Jinja2 + vanilla JS over a SPA

For a single-page habit tracker with a handful of API calls, a full React/Vue setup adds build complexity without benefit. Jinja2 serves the shell; JS fetches JSON for dynamic data. This keeps `run.bat` as a one-command experience.

### SQLite at project root

Placing `daily_forge.db` next to `requirements.txt` makes backup obvious (copy one file) and path resolution simple (`Path(__file__).parent.parent`). For Pi deployment, the path can move to `/var/lib/daily-forge/` via env var in a later PR.

### Streak grace period

Users expect "I haven't posted yet today" to not immediately show a broken streak. Anchoring the current streak to yesterday when today is empty matches GitHub-contribution and Duolingo-style mental models.

## UX

### Copy-first, mark-second workflow

Requiring API integration to count a post would block the core habit loop. The flow is: write → copy → paste on platform → mark posted. The mark step is one tap and can happen before or after external posting.

### Status banner over modal alerts

Gentle inline messaging ("your streak is still alive") feels calmer than popups or red error states. Four states (`new`, `at_risk`, `posted_today`, `broken`) cover all cases without nagging.

### Dark mode via CSS variables

A single `[data-theme="dark"]` block swapping variables is easier to maintain than Tailwind `dark:` classes mixed with custom design tokens. Tailwind CDN is kept for potential utility classes only.

## Technical

### Starlette `TemplateResponse` API (v0.37+)

Newer Starlette expects `TemplateResponse(request, name, context)` — not the older `(name, {"request": request, ...})` signature. Passing the dict as the first arg caused `TypeError: unhashable type: 'dict'`.

### FastAPI `on_event("startup")` for DB init

`init_db()` on startup ensures first-run works without a separate migration step. For v0.2+, consider Alembic if schema changes grow.

### Heatmap week alignment

GitHub heatmaps start weeks on Sunday with leading padding cells. Client-side JS groups API flat date array into week columns; server sends a simple `{date, count, level}` list to stay backend-agnostic.

### Thread format: `N/Total` prefix

Numbered threads like `1/5 Point one` are widely recognized on X and easy to split when copying individual tweets manually.

## What we'd do differently next time

1. Add pytest from day one for streak edge cases (timezone boundaries, DST).
2. Use `lifespan` context manager instead of deprecated `on_event` when targeting FastAPI 0.109+ exclusively.
3. Self-host fonts to avoid CDN dependency for fully offline/PWA use.

## Phase 2 learnings

### Timezone via query param + settings table

Rather than only server-local dates, v0.2 stores timezone in `app_settings` and accepts `?tz=` on all date-sensitive APIs. Client auto-detects via `Intl` and syncs on change. **Requires `tzdata` on Windows** — added to `requirements.txt`.

### Streak freezes as separate table

Freezes are not fake entries — they're a parallel `streak_freezes` table merged into `effective_dates()` for streak math. Heatmap shows freezes at level 2 (lighter accent) vs posts at level 4.

### Modular vanilla JS

`static/js/*.js` modules (settings, drafts, onboarding, etc.) loaded via script tags avoid a bundler while keeping `app.js` readable. Load order matters: settings before app.

### Service worker reminders

Browser notifications require permission; reminders check every 30s while the page is open. True background reminders when the tab is closed need Periodic Background Sync (limited support) — documented as best-effort in v0.2.

### Windows + zoneinfo

Python's `zoneinfo` does not ship IANA data on Windows. The `tzdata` package is mandatory for timezone features to work in dev and production.

## Open questions

- Should "mark posted" without content count? **Yes** — showing up is the habit; empty marks are valid.
- Background reminders when app is fully closed? Deferred to Phase 3 PWA polish.