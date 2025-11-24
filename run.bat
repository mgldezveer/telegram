@echo off
REM Quick start script for Windows

echo ========================================
echo AI Content Bot - Quick Start
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies if needed
echo Checking dependencies...
pip install -q -r requirements.txt
echo.

REM Check setup
echo Checking configuration...
python check_setup.py
if errorlevel 1 (
    echo.
    echo Please fix the issues above before running the bot.
    pause
    exit /b 1
)
echo.

REM Initialize database if needed
if not exist "bot.db" (
    echo Initializing database...
    python init_db.py
    echo.
)

REM Run the bot
echo Starting bot...
echo Press Ctrl+C to stop
echo ========================================
echo.
python run.py

pause
