# Daily Forge

**Build the habit of showing up first.**

Daily Forge is a minimal, beautiful habit-building web app focused on building a consistent daily posting habit on social media (X, LinkedIn, etc.). No API integrations in v1 — write, copy, paste, mark done.

## Features (v0.2)

- Daily streak counter with GitHub-style activity heatmap
- **Configurable timezone** for streak day boundaries
- **Streak freezes** — 2 grace tokens per month
- **Weekly recap** with 7-day trend chart
- Rotating daily writing prompts
- Single post + thread composer with **draft autosave**
- **X URL-weighted** character count + LinkedIn guidance toggle
- **Thread split preview** — chunks under 280 chars
- **Export history** as Markdown
- Browser **reminder notifications** (optional)
- **3-step onboarding** for first-time users
- Keyboard shortcuts (`Ctrl+Enter`, `Ctrl+S`)
- Dark / light mode + **PWA offline shell**
- Fully local-first (SQLite on disk)

## Quick start (Windows)

### Option A — double-click

```
run.bat
```

Creates a venv, installs deps, and starts the server at [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Option B — Git Bash / terminal

```bash
# Clone and enter the project
git clone https://github.com/yourusername/daily-forge.git
cd daily-forge

# Create virtual environment
python -m venv venv
source venv/Scripts/activate   # Git Bash on Windows
# OR: venv\Scripts\activate    # CMD / PowerShell

# Install dependencies
pip install -r requirements.txt

# Run the app
uvicorn daily_forge.main:app --reload --host 127.0.0.1 --port 8000
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser.

## Project structure

```
daily-forge/
├── daily_forge/          # Python package
│   ├── main.py           # FastAPI app & routes
│   ├── database.py       # SQLite helpers
│   └── models.py         # Pydantic models & streak logic
├── templates/            # Jinja2 HTML templates
├── static/               # CSS & JavaScript
├── frontend/             # Static redirect (legacy path)
├── daily_forge.db        # SQLite DB (created on first run)
├── requirements.txt
├── run.bat
└── README.md
```

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Main app UI |
| GET | `/api/health` | Health check |
| GET/PUT | `/api/settings` | Timezone & reminder settings |
| GET | `/api/prompt?tz=` | Today's writing prompt |
| GET | `/api/stats?tz=` | Streaks, heatmap, freeze count |
| GET | `/api/weekly-recap?tz=` | This week's summary + trend |
| GET | `/api/today?tz=` | Today's entry (if any) |
| GET | `/api/entries` | Recent entries |
| GET | `/api/freezes?tz=` | Freezes used this month |
| POST | `/api/freeze` | Use streak freeze on missed day |
| POST | `/api/post` | Mark today as posted |
| POST | `/api/thread/format` | Format thread items |
| POST | `/api/thread/split` | Split into <280 char chunks |
| POST | `/api/char-count` | X-weighted character count |
| GET | `/api/export/markdown` | Download full history |

## Streak rules

- Posting any time during a calendar day counts for that day.
- If you haven't posted today but posted yesterday, your streak is still alive until midnight.
- Missing a full day resets the current streak (longest streak is preserved in history).

## Development

```bash
source venv/Scripts/activate
uvicorn daily_forge.main:app --reload

# Run tests
pytest tests/ -v
```

The SQLite database file `daily_forge.db` is created automatically in the project root.

### v0.2 migration notes

- Existing `daily_forge.db` files are **auto-migrated** on startup (new `app_settings` and `streak_freezes` tables).
- No manual migration needed.
- Install new deps: `pip install -r requirements.txt` (adds `tzdata`, `pytest`).
- Clear browser localStorage only if onboarding should reappear (`df-onboarding-complete`).

## License

See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).