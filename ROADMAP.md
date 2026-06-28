# ROADMAP.md — Daily Forge

## Phase 1 — MVP ✅ (v0.1)

- [x] Daily streak counter
- [x] GitHub-style activity heatmap (52 weeks)
- [x] Rotating daily prompts
- [x] Single post mode with character count
- [x] Copy for X / LinkedIn buttons
- [x] Thread generation (numbered list → formatted thread)
- [x] Mark as posted / streak persistence
- [x] Gentle missed-day messaging
- [x] Dark / light mode
- [x] Windows one-command launcher (`run.bat`)
- [x] Local SQLite storage

---

## Phase 2 — Polish & Retention ✅ (v0.2)

### Habit mechanics

- [x] Configurable timezone (streak day boundary)
- [x] Optional posting reminder (browser notifications + service worker)
- [x] Weekly recap view (posts this week, streak trend, summary)
- [x] Streak freeze / grace tokens (2 per month)

### Composer improvements

- [x] Draft autosave to localStorage
- [x] X character count with URL weighting
- [x] LinkedIn post length guidance + platform toggle
- [x] Thread split preview (per-tweet chunks under 280 chars)
- [x] Export history as Markdown

### UX

- [x] Onboarding flow (3-step: welcome → timezone → first prompt)
- [x] Keyboard shortcuts (Ctrl+Enter mark posted, Ctrl+S save draft)
- [x] Improved empty states with subtle illustrations
- [x] PWA manifest + service worker (offline shell)

### Quality

- [x] pytest suite for streak logic and API
- [ ] GitHub Actions CI (lint + test)
- [x] Migrate FastAPI startup to `lifespan` handler

---

## Phase 3 — Pi & PWA (v0.3)

- [ ] Raspberry Pi deployment (systemd + Cloudflare Tunnel)
- [ ] Installable on mobile home screen (full PWA polish)
- [ ] Optional backup/restore (export/import DB)
- [ ] Self-hosted fonts (fully offline)

---

## Phase 4 — Content tools (v0.4+)

*Only after habit loop is proven solid.*

- [ ] Custom prompt library (add/edit/delete)
- [ ] Post templates / snippets
- [ ] AI-assisted draft suggestions (local or API, opt-in)
- [ ] Content calendar (plan ahead, still manual post)
- [ ] Tags / categories for posts

---

## Not planned (unless community demands)

- Direct posting to X/LinkedIn APIs (OAuth complexity, ToS)
- Multi-user / cloud accounts
- Mobile native apps
- Analytics / engagement tracking

---

## How to influence the roadmap

Open an issue with the `roadmap` label. PRs welcome for Phase 3 items.