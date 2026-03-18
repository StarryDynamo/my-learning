@echo off
cd /d "%~dp0"
REM Activate venv if present
if exist .venv\Scripts\activate.bat (
  call .venv\Scripts\activate.bat
) else if exist venv\Scripts\activate.bat (
  call venv\Scripts\activate.bat
)
python run_daily_digest.py
pause
