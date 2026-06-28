@echo off
REM Daily Forge — one-command launcher for Windows
cd /d "%~dp0"

if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo Starting Daily Forge at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.
uvicorn daily_forge.main:app --reload --host 127.0.0.1 --port 8000