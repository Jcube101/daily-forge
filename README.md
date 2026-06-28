# Daily Forge

**Build the habit of showing up first.**

Daily Forge is a minimal, beautiful habit-building web app focused on building a consistent daily posting habit on social media (X, LinkedIn, etc.). No API integrations in v1 — write, copy, paste, mark done.

## Features (v0.1)

- Daily streak counter with GitHub-style activity heatmap
- Rotating daily writing prompts
- Single post mode with character count and copy buttons
- Thread mode — numbered list to formatted thread
- Gentle streak reminders (at-risk, broken, posted states)
- Dark / light mode
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
| GET | `/api/prompt` | Today's writing prompt |
| GET | `/api/stats` | Streaks, heatmap, status |
| GET | `/api/today` | Today's entry (if any) |
| GET | `/api/entries` | Recent entries |
| POST | `/api/post` | Mark today as posted |
| POST | `/api/thread/format` | Format thread items |

## Streak rules

- Posting any time during a calendar day counts for that day.
- If you haven't posted today but posted yesterday, your streak is still alive until midnight.
- Missing a full day resets the current streak (longest streak is preserved in history).

## Development

```bash
source venv/Scripts/activate
uvicorn daily_forge.main:app --reload
```

The SQLite database file `daily_forge.db` is created automatically in the project root.

## License

See [LICENSE](LICENSE).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).