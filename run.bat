@echo off
REM Survey API Startup Script for Windows

echo ========================================
echo Survey API - FastAPI Backend
echo ========================================
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt -q

REM Run seed script
echo.
echo Initializing database...
python seed_db.py

REM Start server
echo.
echo Starting FastAPI server...
echo.
echo API running at: http://localhost:8000
echo API Docs at: http://localhost:8000/docs
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
