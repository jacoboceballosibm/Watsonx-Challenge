#!/bin/bash
# Start the frontend with configurable port

# Default to port 3000 if not set
PORT=${FRONTEND_PORT:-3000}

cd frontend
echo "Starting ProM frontend on http://127.0.0.1:${PORT}"
echo ""
echo "To use a different backend port, add ?backend_port=8003 to the URL"
echo "Example: http://127.0.0.1:${PORT}/login.html?backend_port=8003"
echo ""
python3 -m http.server "${PORT}"
