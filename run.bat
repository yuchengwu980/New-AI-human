@echo off
setlocal

cd /d %~dp0

echo [1/4] Checking virtual environment...
if not exist .venv (
  echo .venv not found, creating...
  python -m venv .venv
)

echo [2/4] Installing dependencies...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt

if not exist .env (
  echo [3/4] .env not found, creating from .env.example...
  copy /Y .env.example .env >nul
) else (
  echo [3/4] .env already exists, skip copy.
)

echo [4/4] Starting service at http://127.0.0.1:8000

echo Health: http://127.0.0.1:8000/health
echo UI    : http://127.0.0.1:8000/ui

.venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

endlocal
