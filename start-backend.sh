#!/bin/bash
# Start the FastAPI backend with configurable port

# Load .env if it exists
if [ -f backend/.env ]; then
  export $(cat backend/.env | grep -v '^#' | xargs)
fi

# Default to port 8000 if not set
PORT=${PORT:-8000}
HOST=${HOST:-127.0.0.1}

cd backend
echo "Starting ProM backend on http://${HOST}:${PORT}"
uvicorn app.main:app --host "${HOST}" --port "${PORT}" --reload
