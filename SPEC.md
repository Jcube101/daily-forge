# SPEC.md — Daily Forge Technical Specification

## 1. Overview

**Product:** Daily Forge  
**Version:** 0.1.0 (MVP / Phase 1)  
**Goal:** Help users build a daily social media posting habit through streak tracking, prompts, and lightweight composition tools.

## 2. Philosophy

1. **Habit before tooling** — streak and show-up mechanics are primary.
2. **Local-first** — data stays on the user's machine.
3. **Manual posting** — copy-paste to X/LinkedIn; no API coupling in v1.
4. **Calm UX** — motivational, not gamified to exhaustion.

## 3. Tech stack

### Backend

- **Runtime:** Python 3.11+
- **Framework:** FastAPI
- **Server:** uvicorn (with `--reload` in dev)
- **Templates:** Jinja2
- **Database:** SQLite 3 (file: `daily_forge.db`)

### Frontend

- **Markup:** HTML5 (Jinja2 template)
- **Styling:** Custom CSS with CSS variables + Tailwind CDN (utility only)
- **Script:** Vanilla ES6+ JavaScript (no bundler)
- **Fonts:** DM Sans (UI), Fraunces (display) via Google Fonts

### Platform targets

| Phase | Platform |
|-------|----------|
| v0.1 | Windows (local dev) |
| v0.2+ | Raspberry Pi (systemd service) |

## 4. Data model

### Table: `daily_entries`

| Column | Type | Notes |
|--------|------|-------|
| `id` | INTEGER PK | Auto-increment |
| `entry_date` | TEXT UNIQUE | ISO date `YYYY-MM-DD` |
| `posted_at` | TEXT | UTC ISO timestamp |
| `content` | TEXT NULL | Draft or formatted post |
| `post_type` | TEXT | `single` or `thread` |
| `notes` | TEXT NULL | Reserved for future use |

## 5. Streak algorithm

```
current_streak:
  anchor = today if posted today else yesterday
  count consecutive days backward from anchor where entry exists

longest_streak:
  max run of consecutive dates in all entry_dates

status:
  posted_today  → user posted today
  at_risk       → posted yesterday, not yet today
  broken        → missed at least one day (with prior history)
  new           → no entries yet
```

## 6. API contract

### `GET /api/stats`

```json
{
  "current_streak": 5,
  "longest_streak": 12,
  "total_posts": 20,
  "posted_today": true,
  "status": "posted_today",
  "message": "You showed up today...",
  "heatmap": [{ "date": "2026-06-28", "count": 1, "level": 4 }],
  "today": "2026-06-28"
}
```

### `POST /api/post`

```json
{ "content": "optional text", "post_type": "single", "notes": null }
```

### `POST /api/thread/format`

```json
{ "items": ["First point", "Second point"] }
```

Response:

```json
{ "formatted": "1/2 First point\n\n2/2 Second point", "tweet_count": 2 }
```

## 7. UI sections

1. Header with theme toggle
2. Status banner (contextual message)
3. Stats: current streak, longest streak, total days
4. 52-week activity heatmap
5. Daily prompt card
6. Composer tabs: Single post | Thread
7. Mark as posted CTA

## 8. Non-functional requirements

- **Performance:** < 100ms API responses on local SQLite
- **Mobile:** Responsive layout, touch-friendly buttons
- **Accessibility:** ARIA labels on tabs, live region for toasts
- **Privacy:** No network calls except Google Fonts / Tailwind CDN

## 9. Out of scope (v1)

- Social media API posting
- User accounts / cloud sync
- PWA / service worker
- Email/push notifications
- AI content generation

## 10. Future considerations

See [ROADMAP.md](ROADMAP.md).