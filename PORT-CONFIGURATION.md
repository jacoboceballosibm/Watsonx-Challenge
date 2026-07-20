# Port Configuration Guide

This project supports flexible port configuration for both backend and frontend.

## Quick Setup for Different Ports

### Using ports 8003 (backend) and 3003 (frontend)

1. **Backend:**
   ```bash
   cd backend
   # Edit .env and set: PORT=8003
   uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload
   ```

2. **Frontend:**
   ```bash
   cd frontend
   python3 -m http.server 3003
   ```

3. **Configure frontend to talk to backend:**
   Open `http://127.0.0.1:3003/login.html?backend_port=8003`
   
   The `?backend_port=8003` parameter tells the frontend to use port 8003 for API calls.
   This setting is saved in localStorage, so you only need to set it once.

## Alternative: Using Startup Scripts

```bash
# Backend (edit backend/.env first to set PORT=8003)
./start-backend.sh

# Frontend (in another terminal)
FRONTEND_PORT=3003 ./start-frontend.sh
```

Then visit: `http://127.0.0.1:3003/login.html?backend_port=8003`

## How It Works

### Backend
- Reads `PORT` from `backend/.env` (defaults to 8000)
- Can be overridden via command line: `--port 8003`

### Frontend
- Can be served on any port via `python3 -m http.server <PORT>`
- Automatically detects backend port from:
  1. Query parameter: `?backend_port=8003`
  2. localStorage: `BACKEND_PORT` key
  3. Default: 8000

### Frontend Configuration Priority
1. **Query parameter** (highest): `?backend_port=8003` - sets and persists to localStorage
2. **localStorage**: Previously saved `BACKEND_PORT` value
3. **Default** (lowest): Port 8000

## Checking Current Configuration

Open browser console on any page and run:
```javascript
console.log('Backend API URL:', API);
```

## Changing Backend Port After Setup

**Option 1: Query parameter** (recommended)
```
http://127.0.0.1:3003/login.html?backend_port=8003
```

**Option 2: Browser console**
```javascript
localStorage.setItem('BACKEND_PORT', '8003');
location.reload();
```

**Option 3: Clear and reset**
```javascript
localStorage.removeItem('BACKEND_PORT');
location.reload();
// Then use ?backend_port=XXX to set new port
```

## Troubleshooting

**Frontend can't reach backend:**
1. Check backend is running: `curl http://127.0.0.1:8003/api/health`
2. Check frontend config: Open browser console and type `API` - should show the correct URL
3. If wrong port, add `?backend_port=XXXX` to URL

**Port already in use:**
- Backend: Change `PORT` in `backend/.env` to a different number (e.g., 8004)
- Frontend: Use different port: `python3 -m http.server 3004`

## MCP Server Configuration

Don't forget to update your MCP server config to match your backend port:

In your MCP `mcp.json`:
```json
{
  "mcpServers": {
    "prom-mcp-server": {
      "env": {
        "PROM_API_URL": "http://127.0.0.1:8003"
      }
    }
  }
}
```
