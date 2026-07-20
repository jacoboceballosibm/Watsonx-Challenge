# Port Configuration Changes Summary

## What Changed

The repository now supports **flexible port configuration** for both backend and frontend, allowing you to use any available port (e.g., 8003 and 3003 instead of 8000 and 3000).

## Files Modified

### New Files
1. **`frontend/js/config.js`** - Dynamic backend URL configuration
   - Reads backend port from query parameter or localStorage
   - Falls back to port 8000 by default
   - Logs configuration on page load

2. **`start-backend.sh`** - Backend startup script
   - Reads PORT from `backend/.env`
   - Defaults to 8000 if not set

3. **`start-frontend.sh`** - Frontend startup script
   - Reads FRONTEND_PORT from environment
   - Defaults to 3000 if not set
   - Shows instructions for connecting to custom backend port

4. **`test-ports.sh`** - Verification script
   - Tests that all configuration is correct
   - Checks for hardcoded ports
   - Validates config.js is included

5. **`PORT-CONFIGURATION.md`** - Comprehensive port configuration guide

6. **`CHANGES-PORT-CONFIG.md`** - This file

### Modified Files

#### Frontend
- **`frontend/index.html`** - Added `<script src="js/config.js"></script>`
- **`frontend/login.html`** - Added `<script src="js/config.js"></script>`
- **`frontend/owner.html`** - Added `<script src="js/config.js"></script>`
- **`frontend/seat-detail.html`** - Added `<script src="js/config.js"></script>` and replaced hardcoded URLs
- **`frontend/js/prom.js`** - Removed hardcoded `const API = "http://127.0.0.1:8000/api"`
- **`frontend/js/owner.js`** - Changed to use `API` from config.js

#### Backend
- **`backend/.env.example`** - Added comment about PORT configuration
- **`backend/.env`** - Already has PORT=8003 configured

#### Documentation
- **`README.md`** - Added Quick Start section with custom port instructions
- **`README.md`** - Updated Quickstart sections with flexible port examples
- **`README.md`** - Updated MCP server registration with port notes

## How It Works

### Backend Port
1. Set `PORT=8003` in `backend/.env`
2. Start backend: `uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload`

### Frontend Port
1. Serve on any port: `python3 -m http.server 3003`
2. Connect to backend using query parameter on first visit:
   ```
   http://127.0.0.1:3003/login.html?backend_port=8003
   ```
3. The frontend saves this to localStorage automatically

### Configuration Flow
```
User visits login.html?backend_port=8003
  ↓
config.js reads query parameter
  ↓
Saves to localStorage.setItem('BACKEND_PORT', '8003')
  ↓
Sets API = 'http://127.0.0.1:8003/api'
  ↓
All subsequent API calls use this URL
```

## Benefits

1. **No port conflicts** - Use any available port on your Mac
2. **Easy switching** - Change ports without editing code
3. **Persistent** - Frontend remembers backend port across sessions
4. **Flexible** - Each developer can use different ports
5. **Clear errors** - Console logs show which backend URL is being used

## Testing

Run the test script to verify everything is configured correctly:
```bash
./test-ports.sh
```

## Migration Notes

- **Old approach**: Hardcoded `http://127.0.0.1:8000/api` in every file
- **New approach**: Single `config.js` with dynamic port detection
- **Breaking changes**: None - defaults to port 8000 if not configured
- **MCP server**: Requires manual update to `PROM_API_URL` in mcp.json

## Usage Examples

### Scenario 1: Using ports 8003 and 3003
```bash
# Terminal 1
cd backend
# Edit .env: PORT=8003
uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload

# Terminal 2
cd frontend
python3 -m http.server 3003

# Browser
# First time: http://127.0.0.1:3003/login.html?backend_port=8003
# After that: http://127.0.0.1:3003/login.html
```

### Scenario 2: Using startup scripts
```bash
# Terminal 1
./start-backend.sh  # Reads PORT from backend/.env

# Terminal 2
FRONTEND_PORT=3003 ./start-frontend.sh

# Browser
http://127.0.0.1:3003/login.html?backend_port=8003
```

### Scenario 3: Switching ports
```bash
# In browser console
localStorage.setItem('BACKEND_PORT', '8004');
location.reload();
```

## Troubleshooting

See [PORT-CONFIGURATION.md](PORT-CONFIGURATION.md) for detailed troubleshooting steps.

Common issues:
- Frontend can't reach backend → Check `API` variable in browser console
- Wrong backend port → Add `?backend_port=XXXX` to URL
- Port conflicts → Use `lsof -i :8000` to check what's using a port
