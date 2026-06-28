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

## Phase 2 — Polish & Retention (v0.2)

### Habit mechanics

- [ ] Configurable timezone (streak day boundary)
- [ ] Optional posting reminder (browser notification / local cron)
- [ ] Weekly recap view (posts this week, streak trend)
- [ ] Streak freeze / grace tokens (1 per month?)

### Composer improvements

- [ ] Draft autosave to localStorage
- [ ] X character count with URL weighting
- [ ] LinkedIn post length guidance
- [ ] Thread split preview (per-tweet chunks under 280 chars)
- [ ] Export history as Markdown

### UX

- [ ] Onboarding flow (3-step: prompt → write → mark posted)
- [ ] Keyboard shortcuts (Ctrl+Enter to mark posted)
- [ ] Improved empty state illustrations
- [ ] Self-hosted fonts (offline-ready)

### Quality

- [ ] pytest suite for streak logic
- [ ] GitHub Actions CI (lint + test)
- [ ] Migrate FastAPI startup to `lifespan` handler

---

## Phase 3 — Pi & PWA (v0.3)

- [ ] Raspberry Pi deployment (systemd + Cloudflare Tunnel)
- [ ] PWA manifest + service worker
- [ ] Installable on mobile home screen
- [ ] Optional backup/restore (export/import DB)

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

Open an issue with the `roadmap` label. PRs welcome for Phase 2 items marked above.