# Professional Marketplace (ProM) — Agent Documentation

## 1. Listing Expiration Tracking Agent

**Purpose:** Automatically track listing expiration and prevent stale postings from sitting inactive.

**How It Works:**
- Scans all active listings owned by current user
- Calculates `days_until_expiration = (last_confirmed_date + 30 days) - today`
- Categorizes into 4 buckets: Expired (<0 days), Soon (≤7 days), 15 Days (8-15 days), 30 Days (16+ days)
- Displays results in color-coded tabs: Red → Orange → Yellow → Green

**Key Actions:**
- **Confirm Active:** Resets `last_confirmed_date` to now, extends visibility 30 days
- **Reactivate:** Re-opens expired listings with fresh 30-day window
- **Archive:** Permanently hides listing from dashboard

**Implementation:**
- **Frontend:** `owner-dashboard.js` → `renderExpirationDashboard()`
- **Backend:** `/api/owner/dashboard` → calculates expiration per listing
- **Trigger:** Runs on page load (not scheduled)

**Data Flow:**
1. Owner opens dashboard
2. Backend queries seats where `owner_professional_id = current_user`
3. Filters to `is_available = true`
4. For each seat: calculate days left, assign to category
5. Frontend renders 4-column grid with counts and listings

---

## 2. Candidate Selection Alert Agent

**Purpose:** Flag listings where enough candidates are already selected to fill all positions.

**How It Works:**
- Cross-references each active listing with its candidate applications
- Counts applications where `status = "Selected"`
- Flags when `selected_count >= positions_still_needed`
- Example: 3 candidates selected, 2 positions needed → Alert

**Key Actions:**
- **Close Listing:** Sets `is_available = false`, hides from candidates
- **Mark as Formality:** Changes `seat_type = "formal"`, keeps visible with accurate labeling
- **Edit Listing:** Opens modal to adjust `positions_still_needed` or other fields

**Implementation:**
- **Frontend:** `owner-dashboard.js` → `renderMismatchDashboard()`
- **Backend:** `/api/owner/dashboard` → queries applications, counts "Selected" status
- **Trigger:** Runs on page load alongside expiration agent

**Data Flow:**
1. For each active listing: fetch all applications via `list_applicants_for_seat(seat_id)`
2. Count where `app.status == CandidateStatus.SELECTED`
3. If `selected_count >= seat.positions_still_needed`, add to mismatch array
4. Frontend displays purple-themed alert with ratio badge (e.g., "3 selected / 2 needed")

---

## 3. AI Recommendation Agent

**Purpose:** Rank and recommend listings for candidates or rank applicants for owners using AI matching.

**How It Works:**

**Candidate Mode:**
- Input: Professional's CV/skills + all open seats
- AI analyzes skills, experience, location preferences
- Scores each seat 0.0-1.0 based on:
  - Aligned skills (matches between CV and job requirements)
  - Skill gaps (missing requirements)
  - Experience level vs. band requirements
- Returns ranked list with match scores, reasons, aligned skills, gaps

**Owner Mode:**
- Input: Specific seat + all applicants already "in play"
- AI ranks applicants by fit for that seat
- Scores based on skills match, experience, availability
- Returns ranked list of candidates with reasons

**Implementation:**
- **Backend:** `recommendation_agent.py` → OpenAI GPT-4.1-mini structured output
- **Frontend (Candidate):** `prom.js` → `loadRecommendations()` displays top matches
- **Frontend (Owner):** `owner.js` → shows ranked applicants for a seat
- **API:** `/api/agents/recommendations` (POST with mode: "candidate" or "owner")

**Key Features:**
- Hybrid scoring: lexical matching (keyword overlap) + LLM semantic analysis
- Frontend ranking bonus: +0.05 for listings with "frontend" + candidate has React/JS
- Max 20 seats sent to LLM (top pre-filtered by lexical score)
- Structured output via Pydantic schema (forced JSON format)

**Data Flow (Candidate Mode):**
1. Fetch user's latest CV + profile
2. Fetch all available seats (`is_available = true`)
3. Lexical pre-filter: token overlap between CV and seat descriptions
4. Send top 20 seats + CV to OpenAI with structured schema
5. LLM returns JSON: `{recommendations: [{seat_id, match_score, reason, aligned_skills, gaps}]}`
6. Frontend displays cards sorted by match_score descending

---

## 4. CV Tailor Agent

**Purpose:** Generate role-specific CV versions that highlight relevant experience for a target listing.

**How It Works:**
- Input: Candidate's base CV + target seat description
- AI rewrites CV sections to emphasize relevant experience:
  - Reorders bullet points (most relevant first)
  - Highlights aligned skills in work history
  - Adjusts professional summary to match role requirements
  - De-emphasizes unrelated experience
- Returns structured CV ready for download

**Key Outputs:**
- `tailored_cv_text`: Full tailored CV as plain text
- `tailored_cv_contact`: Name, title, phone, email
- `tailored_cv_overview`: Role-specific professional summary
- `tailored_skills`: List of key skills (reordered for relevance)
- `tailored_cv_sections`: Work experience, IBM assignments, education, etc.
- `changes_summary`: Bullets explaining what changed and why
- `role_alignment`: Bullets showing how CV now aligns with role

**Implementation:**
- **Backend:** `cv_tailor_agent.py` → OpenAI GPT-4.1-mini structured output
- **Frontend:** CV Builder page (`seat-detail.html`) → "Tailor CV" button
- **API:** `/api/agents/cv-tailor` (POST with seat_id, professional_id, cv_id)

**User Flow:**
1. Candidate views seat detail page
2. Clicks "Tailor CV for this role"
3. Agent generates tailored version (8-15 seconds)
4. Preview displayed in expandable panel
5. Candidate can edit inline or save as new CV version
6. Tagged with `tags: ["tailored"]` in database

**Data Flow:**
1. Fetch seat details (title, client, requirements)
2. Fetch candidate's base CV (latest version or specified cv_id)
3. Send both to OpenAI with detailed prompt:
   - "Rewrite this CV to highlight experience relevant to [seat_title]"
   - "Keep all factual content accurate, only reorder and emphasize"
   - "Return structured sections matching CV Builder format"
4. LLM returns JSON with all sections pre-parsed
5. Frontend loads into editable form

---

## 5. Outreach Email Drafter Agent

**Purpose:** Draft personalized inquiry emails to project contacts for candidates.

**How It Works:**
- Input: Seat details + candidate profile
- Generates email with:
  - Subject: "Interest in [Position] – [Client]"
  - Body: Personalized introduction mentioning candidate's relevant skills
  - CTA: Request to discuss, mention attached CV
- Returned to frontend for user editing (not auto-sent)

**Implementation:**
- **Backend:** `outreach_agent.py` → Template-based stub (TODO: replace with watsonx.ai LLM)
- **Frontend:** Seat detail page → "Draft outreach email" button
- **API:** `/api/agents/outreach/draft` (POST with seat_id, candidate_professional_id)

**Current Stub Logic:**
```
Subject: Interest in {seat_title} – {client}
Body:
Dear Hiring Manager,

I am reaching out regarding the open {seat_title} position at {client}.

My name is {candidate_name} and I bring expertise in {skills}. 
I believe my background aligns closely with the requirements...

Best regards,
{candidate_name}
```

**Send Integration:**
- After editing draft, candidate clicks "Send via Outlook"
- POST to `/api/agents/outreach/send`
- Backend calls `outlook_service.send_outlook_email()` (requires Outlook integration)
- Email tracked in database (to, subject, body, sent_at)

**Data Flow:**
1. Fetch seat (title, client, owner contact)
2. Fetch candidate profile (name, skills)
3. Generate template with personalized values
4. Return draft to frontend (editable textarea)
5. User edits and confirms send
6. Backend sends via Outlook API
7. Record sent email in `outreach_history` table

---

## Quick Reference

| Agent | Trigger | Input | Output | AI Model |
|-------|---------|-------|--------|----------|
| **Expiration Tracking** | Page load | Owner's seats | 4 categories + counts | None (date math) |
| **Candidate Alert** | Page load | Seats + applications | Mismatch list | None (count logic) |
| **Recommendations** | User click | CV + seats (or seat + applicants) | Ranked list with scores | OpenAI GPT-4.1-mini |
| **CV Tailor** | User click | Base CV + target seat | Tailored CV sections | OpenAI GPT-4.1-mini |
| **Outreach Draft** | User click | Seat + candidate profile | Email subject + body | Template (stub) |

---

## Technical Architecture

**Backend Structure:**
- `backend/app/agents/` — Agent implementations
- `backend/app/routers/agents.py` — API endpoints
- `backend/app/routers/owner.py` — Dashboard endpoint
- `backend/app/models/agent.py` — Request/response schemas

**Frontend Integration:**
- `frontend/js/owner-dashboard.js` — Expiration + Candidate Alert rendering
- `frontend/js/prom.js` — Recommendations + CV Tailor + Outreach
- `frontend/owner.html` — Owner dashboard UI
- `frontend/seat-detail.html` — Candidate view with agent buttons

**Authentication:**
- All agent endpoints require JWT bearer token
- Token validated via `get_current_user()` dependency
- Cross-user access prevented at query level

**Rate Limiting:**
- OpenAI calls: 20 seats max per recommendation request
- CV truncation: 16k chars max for tailor, 8k for recommendations
- No explicit rate limits currently (TODO: add Redis-based throttling)

---

## Configuration

**Environment Variables:**
- `OPENAI_API_KEY` — Required for Recommendations + CV Tailor
- `OPENAI_RECOMMENDATIONS_MODEL` — Default: `gpt-4.1-mini`
- `OPENAI_CV_TAILOR_MODEL` — Default: `gpt-4.1-mini`
- `WATSONX_API_KEY` — TODO: For Outreach agent watsonx.ai integration
- `WATSONX_URL` — TODO: watsonx.ai endpoint

**Feature Flags:**
- Recommendations: Disabled if `OPENAI_API_KEY` not set
- CV Tailor: Disabled if `OPENAI_API_KEY` not set
- Outreach Send: Disabled if Outlook integration not configured

---

## Problem Mapping

| ProM Problem | Agent Solution |
|--------------|----------------|
| **#1: Listings sit for months with no updates** | Expiration Tracking Agent → 30-day auto-expire + color-coded urgency |
| **#2: Listings posted after seat already filled** | Candidate Alert Agent → flags when selected_count ≥ positions_needed |
| **#3: Listings posted for formality, not real** | Candidate Alert → "Mark as Formality" action |
| **#6: Candidates can't tell which listings are real** | Expiration status + formality labeling driven by agents |
| **#7: Tool rarely leads to interviews** | Outreach Drafter → personalized emails to project contacts |

---

## Performance Notes

**Expiration + Candidate Alert:**
- Single DB query per dashboard load
- Sub-100ms response time (no external API calls)
- Auto-refresh every 5 minutes (optional background sync)

**Recommendations:**
- Lexical pre-filter: ~50ms for 100 seats
- OpenAI API call: 3-8 seconds for 20 seats
- Total latency: ~5-10 seconds

**CV Tailor:**
- OpenAI API call: 8-15 seconds (longer prompt, larger output)
- Cached results: instant (if re-tailoring same CV+seat)

**Outreach Draft:**
- Template generation: <10ms (no API call in stub)
- TODO: watsonx.ai call will add 2-5 seconds

---

## Future Enhancements

**Expiration Agent:**
- Email reminders 3 days before expiration
- Bulk "confirm all" action
- Historical expiration rate analytics

**Candidate Alert:**
- Track owner response time to alerts
- Auto-suggest closing after 7 days of inaction

**Recommendations:**
- Fine-tune model on historical hire data
- Incorporate candidate application history (avoid re-recommending rejected seats)
- Real-time skill gap training suggestions

**CV Tailor:**
- Multi-version management (save up to 5 tailored CVs per base CV)
- A/B test different tailoring styles
- Export to .docx with formatting

**Outreach Draft:**
- Replace stub with watsonx.ai LLM call
- Learn from successful outreach (track response rates)
- Suggest follow-up email if no response after 7 days
