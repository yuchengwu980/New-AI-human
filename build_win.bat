@echo off
setlocal

cd /d %~dp0
set APP_NAME=NewAIHuman
set DIST_DIR=dist\%APP_NAME%
set ZIP_NAME=%APP_NAME%_Win64.zip

echo [1/7] Checking virtual environment...
if not exist .venv (
  python -m venv .venv
)

echo [2/7] Installing dependencies...
.venv\Scripts\python -m pip install --upgrade pip
.venv\Scripts\python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Install requirements failed.
  echo Try: .venv\Scripts\python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
  exit /b 1
)

echo [3/7] Installing PyInstaller...
.venv\Scripts\python -m pip install pyinstaller
if errorlevel 1 (
  echo Install pyinstaller failed.
  exit /b 1
)

echo [4/7] Building executable...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist %APP_NAME%.spec del /q %APP_NAME%.spec

.venv\Scripts\pyinstaller --noconfirm --clean --windowed --name %APP_NAME% --paths . --hidden-import app --hidden-import pydantic --hidden-import pydantic_core --collect-submodules app --add-data "scripts;scripts" app\desktop\main_desktop.py
if errorlevel 1 (
  echo PyInstaller build failed.
  exit /b 1
)

echo [5/7] Smoke test executable...
%DIST_DIR%\%APP_NAME%.exe --selfcheck
if errorlevel 1 (
  echo Smoke test failed: %DIST_DIR%\%APP_NAME%.exe --selfcheck
  exit /b 1
)

echo [6/7] Staging runtime files...
if not exist %DIST_DIR%\output\audio mkdir %DIST_DIR%\output\audio
if not exist %DIST_DIR%\output\events mkdir %DIST_DIR%\output\events
copy /Y docs\README_使用说明.txt %DIST_DIR%\README_使用说明.txt >nul

echo [7/7] Creating zip package...
if exist %ZIP_NAME% del /q %ZIP_NAME%
powershell -NoProfile -Command "Compress-Archive -Path '%DIST_DIR%\*' -DestinationPath '%ZIP_NAME%' -Force"
if errorlevel 1 (
  echo Zip creation failed.
  exit /b 1
)

echo Done: %ZIP_NAME%
endlocal
