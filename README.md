# IBM Professional Marketplace — Modernized (ProM+)

A modernized interface and agentic backend for IBM's internal Professional Marketplace (ProM), built for the WatsonX Challenge.

## 🚀 Quick Start (Custom Ports)

The app works on **any port**. If 8000/3000 don't work, use 8003/3003 or any available ports:

```bash
# 1. Backend (set PORT=8003 in backend/.env first)
cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload

# 2. Frontend (in another terminal)
cd frontend && python3 -m http.server 3003

# 3. Open browser
# Visit: http://127.0.0.1:3003/login.html?backend_port=8003
```

The `?backend_port=8003` tells the frontend which port the backend is using. This is saved automatically, so you only need to set it once.

**Test your configuration:** Visit [test-config.html](http://127.0.0.1:3003/test-config.html) to verify ports and test backend connectivity.

See [PORT-CONFIGURATION.md](PORT-CONFIGURATION.md) for detailed port configuration guide.

## Project layout

```
prom-modernized/
├── backend/                  # Python FastAPI backend
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── routers/          # profile, seats, agents endpoints
│   │   ├── models/           # Pydantic schemas
│   │   ├── services/         # data access layer (stub → swap for real DB)
│   │   └── agents/           # one file per agentic feature
│   ├── requirements.txt
│   └── .env.example
├── mcp-server/               # Node.js MCP server (exposes tools to agent clients)
│   ├── src/index.ts          # All 5 MCP tools defined here
│   ├── package.json
│   └── tsconfig.json
└── frontend/                 # Standalone HTML/CSS/JS UI
    ├── index.html            # 3-tab SPA (My Profile, Find a Seat, My Groups)
    ├── css/prom.css          # IBM Carbon-inspired design system
    └── js/prom.js            # Tab nav + all agent panel interactions
```

## Agentic features

| # | Feature | Agent file | MCP tool |
|---|---------|-----------|---------|
| 1 | Stale listing reconfirmation | `stale_agent.py` | `stale_listing_check` |
| 2 | Internally-filled mismatch detector | `mismatch_agent.py` | `mismatch_detector` |
| 5 | AI outreach email drafter | `outreach_agent.py` | `draft_outreach_email` |
| 7 | AI project recommendations | `recommendation_agent.py` | `get_recommendations` |
| 8 | AI CV tailor | `cv_tailor_agent.py` | `tailor_cv` |

Features #3 (formal vs real label) and #4 (status visibility) are handled purely in the frontend/data layer.

## Quickstart

### 1. Backend

The backend port is configurable via the `.env` file. By default it uses port 8000, but you can change it to any available port (e.g., 8003).

**Quick start with default port (8000):**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in OPENAI_API_KEY and PORT if needed
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**OR use a custom port by editing `.env`:**
```bash
# In backend/.env, set:
PORT=8003
# Then run:
uvicorn app.main:app --host 127.0.0.1 --port 8003 --reload
```

**OR use the startup script (reads PORT from .env):**
```bash
./start-backend.sh
```

API docs available at `http://127.0.0.1:<PORT>/api/docs` (replace `<PORT>` with your configured port)

The backend uses a local SQLite database at `backend/prom.db` by default
(`DATABASE_URL=sqlite:///./prom.db`). On startup it creates the schema and seeds
demo users, profiles, and seats from the bundled sample data. Auth uses demo
username/password login plus persisted bearer sessions.

### 2. MCP server

```bash
cd mcp-server
npm install
npm run build
# Register in your mcp.json (see MCP server registration section below)
# IMPORTANT: Update PROM_API_URL in mcp.json to match your backend port
```

### 3. Frontend

The frontend automatically detects the backend port. You can serve it on any port you prefer.

**Quick start with default port (3000):**
```bash
cd frontend && python3 -m http.server 3000
```

**OR use a custom port:**
```bash
cd frontend && python3 -m http.server 3003
# or any other port
```

**OR use the startup script:**
```bash
FRONTEND_PORT=3000 ./start-frontend.sh
```

Then open `http://127.0.0.1:<FRONTEND_PORT>/login.html` in your browser.

**Connecting to a non-default backend:**
If your backend runs on a different port (e.g., 8003), you have two options:

1. **Use query parameter** (one-time):
   ```
   http://127.0.0.1:3000/login.html?backend_port=8003
   ```
   This saves the backend port to localStorage for future visits.

2. **Set in browser console** (persistent):
   ```javascript
   localStorage.setItem('BACKEND_PORT', '8003')
   ```
   Then refresh the page.

**Sign-In Demo**: The app includes 5 demo users showcasing different profiles:
- All accounts use the same password (set via `DEMO_PASSWORD` env var, defaults to "password")
- Click any user card on the login page to auto-sign in
- Each user has unique skills, band, location, and availability date

Demo users: `anguyen`, `jsmith`, `mchen`, `swilliams`, `drodriguez`

See [AUTHENTICATION.md](AUTHENTICATION.md) for complete details.

## Wiring the AI agents

Agent #8, the CV tailor, is wired to the OpenAI Agents SDK. Set these values in
`backend/.env`:

```bash
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CV_TAILOR_MODEL=gpt-4.1-mini
```

The remaining agent files are still draft stubs and can be migrated one by one.

## MCP server registration (mcp.json)

Update the `PROM_API_URL` to match your backend port:

```json
{
  "mcpServers": {
    "prom-mcp-server": {
      "command": "node",
      "args": ["/absolute/path/to/prom-modernized/mcp-server/build/index.js"],
      "env": {
        "PROM_API_URL": "http://127.0.0.1:8000"
      }
    }
  }
}
```

If you're using a different backend port (e.g., 8003), change the URL accordingly:
```json
"PROM_API_URL": "http://127.0.0.1:8003"
```

## Security notes

- The FastAPI server binds to `127.0.0.1` only (never `0.0.0.0`)
- Secrets are read from environment variables — never hardcoded
- A `.gitignore` excludes `.env` from version control
- All logging uses structured JSON and never includes credential values
