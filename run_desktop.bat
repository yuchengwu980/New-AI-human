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
if errorlevel 1 (
  echo.
  echo Install failed. Try mirror command:
  echo .venv\Scripts\python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  pause
  exit /b 1
)

if not exist .env (
  echo [3/4] .env not found, creating from .env.example...
  copy /Y .env.example .env >nul
) else (
  echo [3/4] .env already exists, skip copy.
)

echo [4/4] Launching desktop app...
.venv\Scripts\python -m app.desktop.main_desktop

endlocal
