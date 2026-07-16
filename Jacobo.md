# Jacobo Implementation Rundown

Last updated: July 16, 2026

This project has moved from a static rough draft into a working local prototype with persistent profiles, saved CVs, and a first version of an OpenAI-powered CV tailoring flow.

## Current Architecture

The app is still intentionally lightweight:

- Frontend: static HTML, CSS, and vanilla JavaScript in `frontend/`.
- Backend: FastAPI in `backend/app/`.
- Database: local SQLite through a small custom DB layer.
- Auth: demo username/password auth backed by the SQLite `users` and `sessions` tables.
- AI: OpenAI API via the Python SDK, using a mini model by default.

The default local database is:

```env
DATABASE_URL=sqlite:///./prom.db
```

Because this resolves relative to the backend process working directory, running the backend from `backend/` creates `backend/prom.db`.

## Backend Implemented

### SQLite Persistence

Added `backend/app/services/database.py`.

It creates and migrates these tables:

- `schema_migrations`
- `users`
- `sessions`
- `profiles`
- `seats`
- `cvs`
- `cv_agent_runs`

The DB layer currently supports SQLite only. This is deliberate for the prototype so we can persist edits locally without adding Postgres, Docker, or cloud infra yet.

Profile migration now includes:

- `cv_overview`
- `cv_contact_json`
- `cv_sections_json`

These fields make the CV Builder save real data instead of only updating the page in memory.

### Auth

Implemented demo auth persistence through:

- `backend/app/services/auth_service.py`
- `backend/app/routers/auth.py`

Current auth model:

- Demo users are seeded into the SQLite DB.
- Login returns a session token.
- Sessions are stored in the `sessions` table.
- This is fine for local/demo usage, but it is not production auth yet.

Production later should use hashed passwords, expiry/refresh behavior, proper authorization checks on every user-owned resource, and likely SSO/OIDC if this remains IBM-oriented.

### Profiles

Updated profile service/model/routers so user CV edits can persist.

Profile data now stores:

- base professional details
- skills
- CV overview
- contact block
- structured CV sections
- repository URL field

The frontend saves profile-level CV data through the profile PATCH flow.

### CV Repository

Added a first CV repository backend:

- `backend/app/models/cv.py`
- `backend/app/services/cv_service.py`
- `backend/app/routers/cvs.py`

Available API shape:

```http
GET    /api/cvs?professional_id=...
POST   /api/cvs
GET    /api/cvs/{cv_id}
PATCH  /api/cvs/{cv_id}
DELETE /api/cvs/{cv_id}
POST   /api/cvs/{cv_id}/duplicate
```

Each CV document stores:

- `cv_id`
- `professional_id`
- `name`
- `target_role`
- `source_type`
- `tags`
- `cv_contact`
- `cv_overview`
- `skills`
- `cv_sections`
- `is_default`
- timestamps

On startup, existing profile CV data is seeded into a default `Base CV` when a user does not already have saved CVs.

### CV Tailor Agent

The CV tailor agent lives in:

- `backend/app/agents/cv_tailor_agent.py`
- `backend/app/models/agent.py`
- `backend/app/routers/agents.py`

The agent currently:

- accepts a target role description
- accepts either an active repository CV or pasted source CV text
- falls back to profile data when no source CV is provided
- calls OpenAI using `AsyncOpenAI`
- uses structured output parsing
- returns a tailored CV draft plus review metadata
- records runs in `cv_agent_runs`

Default model:

```env
OPENAI_CV_TAILOR_MODEL=gpt-4.1-mini
```

The structured output includes:

- tailored full CV text
- tailored contact information
- tailored overview
- tailored skills
- tailored structured CV sections
- changes summary
- role alignment notes
- missing experience/gaps
- suggested keywords
- warnings

Important fix made: the OpenAI structured output schema was updated so all response fields are compatible with OpenAI's strict JSON schema requirements.

## Frontend Implemented

### CV Builder Persistence

The CV Builder page now saves updates instead of losing them after logout/refresh.

Updatable areas include:

- contact information
- overview
- key skills
- work experience
- IBM assignment history
- additional client history
- industry experience
- education
- languages
- publications
- memberships
- additional information

The frontend collects the current CV payload and persists it through profile and CV repository endpoints.

### CV Repository UI

Added a repository panel in the CV Builder sidebar.

Current repository behavior:

- loads saved CVs for the active user
- shows active/default CV
- lets the user switch between CVs
- lets the user duplicate the active CV
- updates the builder when a CV is selected
- saves edits back to the active CV

### CV Agent Workspace

Added a CV Agent Workspace above the editor.

Current flow:

1. Paste a target role description.
2. Choose the source CV:
   - active repository CV
   - pasted raw CV text
3. Click `Tailor CV`.
4. Review the agent output:
   - changes
   - role alignment
   - gaps
   - suggested keywords
   - warnings
   - generated CV text
5. Apply the draft to the current CV editor or save it as a new repository CV.

### Resume Preview

Added a resume-style preview card to the CV Builder.

Current preview behavior:

- renders from the active CV/profile data
- updates after selecting a CV
- updates after applying an agent draft
- updates after saving CV edits
- includes `Refresh preview`
- includes `Print`
- includes `Minimize` / `Expand`

The preview is generated from structured CV data, not from a parsed PDF layout yet.

## Environment Variables

Current `.env.example` includes:

```env
PORT=8000
HOST=127.0.0.1
DATABASE_URL=sqlite:///./prom.db
DEMO_PASSWORD=demo123
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CV_TAILOR_MODEL=gpt-4.1-mini
STALE_DAYS_THRESHOLD=30
```

The real `.env` should stay local and should not be committed.

## What Is Not Done Yet

The main missing pieces for a more complete CV agent product are:

- PDF upload and parsing
- DOCX upload and parsing
- export tailored CV to PDF/DOCX
- richer section editing instead of plain text blocks
- better authorization checks on CV endpoints
- production-grade auth
- tests around DB migrations and CV repository endpoints
- UI polish around agent loading/error states
- version history for CVs
- choosing a CV when putting yourself in play for a role

## Recommended Next Phases

### Phase 1: Stabilize Current Prototype

- Add API tests for profile save, CV CRUD, duplicate, and CV tailor request validation.
- Add simple frontend smoke test notes or Playwright later.
- Fix any remaining encoding artifacts from old dash characters in UI strings.

### Phase 2: File Import

- Add backend upload endpoint for PDF/DOCX.
- Parse uploaded CV into text.
- Ask the agent to convert raw CV text into the structured CV schema.
- Save imported CVs into the repository.

Likely Python packages:

- `pypdf` for PDF text extraction
- `python-docx` for DOCX extraction

### Phase 3: Better CV Editing

- Convert section textareas into structured repeatable entries.
- Support adding/removing experience items.
- Support per-section agent suggestions.
- Add "save as new version" behavior.

### Phase 4: Export

- Generate a polished PDF/DOCX from the structured CV.
- Keep the browser preview and exported document visually aligned.
- Let users download a tailored CV from the repository.

### Phase 5: Role Application Flow

- When putting yourself in play for a role, let the user choose one CV from the repository.
- Store the selected CV against that role/application workflow.
- Optionally recommend the best CV based on role fit.

## Current Developer Notes

Run backend from `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open frontend through the local static server or the existing frontend route used in this project. After frontend JS/CSS changes, hard refresh the browser to clear cached files.

Useful checks:

```powershell
node --check frontend/js/prom.js
```

```powershell
cd backend
.\.venv\Scripts\python.exe -m compileall app
```

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/health
```
