#!/bin/bash
# Survey API Startup Script for macOS/Linux

echo "========================================"
echo "Survey API - FastAPI Backend"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt -q

# Run seed script
echo ""
echo "Initializing database..."
python seed_db.py

# Start server
echo ""
echo "Starting FastAPI server..."
echo ""
echo "API running at: http://localhost:8000"
echo "API Docs at: http://localhost:8000/docs"
echo ""

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
