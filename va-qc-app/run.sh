#!/bin/bash
# VA QC App - Run Script
# Usage: ./run.sh [dev|prod]

MODE=${1:-dev}
PORT=${PORT:-8000}

cd "$(dirname "$0")"

echo "Vulcan Arc QC App"
echo "================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 not found"
    exit 1
fi

# Install deps if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "Starting VA QC App..."
echo "Mode: $MODE"
echo "Port: $PORT"
echo ""

if [ "$MODE" == "dev" ]; then
    # Development - auto-reload
    uvicorn main:app --host 0.0.0.0 --port $PORT --reload
else
    # Production
    uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2
fi