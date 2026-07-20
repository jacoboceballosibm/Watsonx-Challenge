# AGENTS.md — IBM Professional Marketplace (ProM+)

Guidance for AI agents working in this WatsonX Challenge repo.

## What this project is

Modernized UI + agentic backend for IBM's internal Professional Marketplace. Stack:

| Layer | Tech | Role |
|-------|------|------|
| `backend/` | Python FastAPI, SQLite, Pydantic | REST API, auth, data, AI agents |
| `frontend/` | Vanilla HTML/CSS/JS (Carbon-inspired) | SPA: profile, seats, groups, owner portal |
| `mcp-server/` | Node.js + TypeScript MCP | Tools that call the FastAPI agents API |

Default API: `http://127.0.0.1:8000` · Frontend often served on port `3000`.

## Layout

```
backend/app/
  main.py           # FastAPI app, CORS, startup seed
  routers/          # auth, profile, seats, agents, owner, cvs
  models/           # Pydantic schemas
  services/         # SQLite access + domain logic
  agents/           # One module per agentic feature
frontend/
  index.html, login.html, owner.html, seat-detail.html
  css/prom.css
  js/prom.js, owner.js
mcp-server/src/index.ts   # MCP tools → POST /api/agents/*
```

## Run locally

**Backend**

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Unix:    source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY, DEMO_PASSWORD, etc.
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Docs: `http://127.0.0.1:8000/api/docs` · Health: `GET /api/health`

**Frontend**

```bash
cd frontend && python -m http.server 3000
```

Open `http://127.0.0.1:3000/login.html`. Demo users: `anguyen`, `jsmith`, `mchen`, `swilliams`, `drodriguez` (password from `DEMO_PASSWORD`, default in `.env.example` is `demo123`).

**MCP server**

```bash
cd mcp-server && npm install && npm run build
```

Point `mcp.json` at `mcp-server/build/index.js` with `PROM_API_URL=http://127.0.0.1:8000`.

## Architecture conventions

- **Routers** stay thin: validate → call service/agent → return Pydantic models.
- **Services** own SQLite (`DATABASE_URL`, default `sqlite:///./prom.db`). Schema + seed run on FastAPI startup.
- **Agents** live in `backend/app/agents/`; expose HTTP via `routers/agents.py`; MCP wraps the same endpoints.
- **Models** are Pydantic v2 in `backend/app/models/`. Prefer extending existing schemas over ad-hoc dicts.
- **Frontend** hardcodes `http://127.0.0.1:8000/api`. Session: `localStorage` keys `prom_token`, `prom_user_id`, `prom_user_name`.
- **Auth**: demo username/password + bearer token. Owner routes use `Depends(get_current_user)`.

## Agentic features

| Feature | Agent module | API | MCP tool | Status |
|---------|--------------|-----|----------|--------|
| Stale listing reconfirmation | `stale_agent.py` | `POST /api/agents/stale-check` | `stale_listing_check` | Stub (template nudge) |
| Internally-filled mismatch | `mismatch_agent.py` | `POST /api/agents/mismatch-check` | `mismatch_detector` | Stub |
| Outreach email drafter | `outreach_agent.py` | `…/outreach-draft`, `…/outreach-send` | `draft_outreach_email` | Stub / Outlook helper |
| Project recommendations | `recommendation_agent.py` | `POST /api/agents/recommendations` | `get_recommendations` | Wired (OpenAI + heuristic fallback; candidate seats + owner applicant ranking) |
| CV tailor | `cv_tailor_agent.py` | `POST /api/agents/cv-tailor` | `tailor_cv` | Wired to OpenAI Agents SDK |
| Listing expiration | `expiration_agent.py` | `POST /api/agents/expiration-check` | — | Rule-based helper |

When wiring a stub agent: keep the request/result models in `models/agent.py`, implement `run_*` in the agent module, keep the router one-liner, and update MCP if the HTTP contract changes. Prefer OpenAI Agents SDK patterns already used in `cv_tailor_agent.py` unless the task explicitly requires watsonx.

## Security & secrets

- Never commit `.env`, tokens, or `prom.db`.
- Bind to `127.0.0.1` in docs/examples; do not advertise `0.0.0.0` for this challenge app.
- Do not hardcode API keys; use env vars (`OPENAI_API_KEY`, etc.).
- Structured JSON logging; never log passwords or bearer tokens.

## Docs map

- `README.md` — overview + quickstart
- `AUTHENTICATION.md` — login/session
- `OWNER_PORTAL.md` — owner listings / expiration / mismatch UX
- `SEAT_DETAIL_PAGE.md`, `CONTACT_FEATURES.md`, `TEST_OWNER_PORTAL.md` — feature notes

## Agent working agreements

1. Match existing style: FastAPI + services + Pydantic; vanilla JS on the frontend (no React/build step unless asked).
2. Prefer small, focused changes; do not rewrite stub agents for cleanliness without a feature goal.
3. After API contract changes, update MCP tool schemas in `mcp-server/src/index.ts` and rebuild.
4. Keep frontend API base URL and auth header patterns consistent with `prom.js` / `owner.js`.
5. Do not commit unless the user asks.
