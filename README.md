# IBM Professional Marketplace — Modernized (ProM+)

A modernized interface and agentic backend for IBM's internal Professional Marketplace (ProM), built for the WatsonX Challenge.

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
├── mcp-server/               # Node.js MCP server (exposes tools to watsonx agents)
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

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in WATSONX_API_KEY etc.
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API docs available at http://127.0.0.1:8000/api/docs

### 2. MCP server

```bash
cd mcp-server
npm install
npm run build
# Register in Bob's mcp.json (see below)
```

### 3. Frontend

Serve the frontend with:
```bash
cd frontend && python -m http.server 3000
```

Then open http://127.0.0.1:3000/login.html in your browser.

**Sign-In Demo**: The app includes 5 demo users showcasing different profiles:
- All accounts use the same password (set via `DEMO_PASSWORD` env var, defaults to "password")
- Click any user card on the login page to auto-sign in
- Each user has unique skills, band, location, and availability date

Demo users: `anguyen`, `jsmith`, `mchen`, `swilliams`, `drodriguez`

See [AUTHENTICATION.md](AUTHENTICATION.md) for complete details.

## Wiring the AI agents

Each agent file has a `# TODO: replace stub with watsonx.ai LLM call` comment.
When you add the watsonx integration:

1. Add `WATSONX_API_KEY`, `WATSONX_URL`, `WATSONX_PROJECT_ID` to `.env`
2. Install `ibm-watsonx-ai` into the backend venv
3. Replace the stub text-generation in each `agents/*.py` file with an actual LLM call

## MCP server registration (mcp.json)

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

## Security notes

- The FastAPI server binds to `127.0.0.1` only (never `0.0.0.0`)
- Secrets are read from environment variables — never hardcoded
- A `.gitignore` excludes `.env` from version control
- All logging uses structured JSON and never includes credential values
