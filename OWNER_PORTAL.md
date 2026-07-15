# Owner Portal Implementation

## Overview
This implementation tackles the three key problems with stale and inaccurate job listings on the IBM Professional Marketplace:

### Problems Solved

#### 1. **Listings sit for months with no updates**
- **Solution**: Default-expiring listings with recurring confirmation
- Listings expire from public view in 30 days unless the owner confirms they're still active
- Expiration is the default, not extension — silence closes the listing instead of keeping it open
- AI Agent checks listings on schedule and drafts reconfirmation nudges to owners

#### 2. **Filled internally but still posted**
- **Solution**: Mismatch detection with smart recommendations
- Cross-checks listing status against internal signals (e.g., candidates already Selected/Confirmed)
- AI Agent flags mismatches and recommends: (1) Close the listing, or (2) Mark as "Formality/compliance posting"
- Prevents confusion for external candidates

#### 3. **Listings posted for formality, not real openings**
- **Solution**: Owner self-labeling at time of posting
- Forced choice with no default/skip option: "Actively hiring" vs. "Formality/compliance posting"
- Formality listings aren't hidden — they stay visible in a separate tab
- Candidates can still try, with accurate expectations

---

## Architecture

### Frontend Components

1. **[owner.html](frontend/owner.html)** — Owner portal interface
   - **My Listings tab**: Dashboard showing all listings with expiration status
   - **Create Listing tab**: Form with required listing type selection
   - **Analytics tab**: Overview stats and listing health metrics
   - Two integrated AI agents:
     - Expiration check agent
     - Mismatch detection agent

2. **[owner.js](frontend/js/owner.js)** — Owner portal JavaScript
   - Role-based authentication (redirects candidates)
   - Listing management functions (confirm, close, reactivate, change type)
   - Agent execution (expiration check, mismatch detection)
   - Dynamic UI rendering based on listing state

3. **[login.html](frontend/login.html)** — Updated with role-based routing
   - Redirects to `owner.html` for owner role
   - Redirects to `index.html` for candidate role

### Backend Components

1. **[owner.py](backend/app/routers/owner.py)** — Owner API routes
   - `GET /api/owner/my-listings` — Get all listings for current owner
   - `POST /api/owner/confirm-listing` — Confirm listing is still active (resets 30-day timer)
   - `POST /api/owner/update-listing-type` — Change between "real" and "formal"
   - `POST /api/owner/close-listing` — Mark listing as unavailable
   - `POST /api/owner/reactivate-listing` — Reactivate expired listing

2. **[expiration_agent.py](backend/app/agents/expiration_agent.py)** — Expiration check agent
   - Scans listings for expiration status
   - Flags listings expiring within threshold (default 7 days)
   - Generates reconfirmation email drafts
   - Returns prioritized recommendations

3. **[mismatch_agent.py](backend/app/agents/mismatch_agent.py)** — Enhanced mismatch detector
   - Checks if candidate status is "Selected"
   - Checks if selected count ≥ positions needed
   - Flags filled-but-posted listings
   - Recommends: close or mark as formality

4. **[seat.py](backend/app/models/seat.py)** — Extended Seat model
   - Added fields:
     - `last_confirmed_date` — When owner last confirmed listing
     - `expiration_date` — Calculated 30 days from confirmation
     - `days_until_expiration` — Days remaining before expiration
     - `is_expired` — Boolean flag for expired listings

5. **[auth.py](backend/app/models/auth.py)** — Updated authentication
   - Added `UserRole` enum (candidate, owner, admin)
   - User model includes role assignment
   - Login response includes role for frontend routing

---

## User Flow

### For Listing Owners

1. **Login** → Automatically routed to Owner Portal based on role
2. **Dashboard** shows:
   - All owned listings with expiration countdown
   - Status badges (Active, Expiring Soon, Expired, Formality)
   - Action buttons contextual to listing state
3. **Agent Tools**:
   - Click "Check for expiration" → See which listings need action
   - Click "Check for mismatches" → See filled-but-posted listings
4. **Actions**:
   - "Confirm still active" → Resets 30-day timer
   - "Mark as formality" → Moves to formality tab (visible to candidates)
   - "Close listing" → Hides from public view
   - "Reactivate" → Brings expired listing back

### For Candidates

1. **Listings auto-expire** after 30 days of no confirmation
   - Prevents seeing months-old stale listings
2. **Separate "Formality postings" tab**
   - Candidates can still apply but know it's compliance-only
3. **Accurate status** via mismatch detection
   - Owners prompted to close filled positions

---

## Demo Users

The system includes demo users with different roles:

**Candidates** (view listings):
- `anguyen` / `password`
- `jsmith` / `password`

**Owners** (manage listings):
- `mchen` / `password`
- `swilliams` / `password`
- `drodriguez` / `password`

---

## Key Features

### 1. Default Expiration
- **Incentive flipped**: Silence closes the listing, not keeps it open
- Listing remains visible for 30 days after last confirmation
- Owner must actively confirm to keep it live

### 2. Listing Type Transparency
- Owner chooses at creation: "Actively hiring" vs. "Formality/compliance"
- No default or skip option — forced choice
- Formality listings visible in separate tab with clear labeling

### 3. Smart Expiration Warnings
- Visual countdown: "Expires in X days"
- Color-coded badges: Active (blue), Expiring Soon (orange), Expired (red)
- Alert boxes with specific action prompts

### 4. Mismatch Detection
- Checks candidate selection status
- Compares selected count vs. positions needed
- AI recommendation for each mismatch

### 5. One-Click Actions
- Confirm listing → Extends 30 days
- Mark as formality → Changes category, stays visible
- Close listing → Hides immediately
- Reactivate → Brings expired listing back with fresh 30-day timer

---

## API Endpoints

### Owner Routes (`/api/owner`)
```
GET    /my-listings              Get all listings for current owner
POST   /confirm-listing          Confirm listing is still active
POST   /update-listing-type      Change listing type (real/formal)
POST   /close-listing/:id        Close a listing
POST   /reactivate-listing/:id   Reactivate expired listing
```

### Agent Routes (`/api/agents`)
```
POST   /expiration-check         Check listings for expiration
POST   /mismatch-check           Detect filled-but-posted listings
```

---

## Technical Implementation

### Expiration Logic
1. When owner confirms listing: `last_confirmed_date = now()`
2. Calculate: `expiration_date = last_confirmed_date + 30 days`
3. Calculate: `days_until_expiration = expiration_date - now()`
4. If `days_until_expiration < 0`: listing is expired and hidden

### Mismatch Detection Logic
1. Check if any candidate has status = "SELECTED"
2. Check if `selected_count >= positions_still_needed`
3. If either true → flag as mismatch
4. Generate recommendation based on listing state

### Role-Based Routing
1. User logs in → backend returns role in JWT/session
2. Frontend stores role in localStorage
3. On page load:
   - Owners → `owner.html`
   - Candidates → `index.html`
4. Each portal checks role on load, redirects if mismatch

---

## Future Enhancements

1. **Automated Email Reminders**
   - Integrate with Outlook service (already added in codebase)
   - Send expiration warnings at 7, 3, and 1 day(s) remaining

2. **Scheduled Agent Runs**
   - Cron job to run expiration check daily
   - Batch email notifications to owners

3. **Listing Edit Functionality**
   - Full CRUD for listing details
   - Version history

4. **Analytics Dashboard**
   - Owner engagement metrics
   - Listing performance tracking
   - Candidate response rates

5. **WatsonX Integration**
   - Enhanced AI recommendations for listing optimization
   - Natural language listing creation
   - Automated candidate-listing matching

---

## Testing Checklist

- [ ] Owner can log in and see only their listings
- [ ] Candidate users are redirected away from owner portal
- [ ] Expiration countdown displays correctly
- [ ] "Confirm still active" resets timer to 30 days
- [ ] Expired listings show as hidden/expired
- [ ] Mismatch detection flags filled positions
- [ ] Listing type can be changed (real ↔ formality)
- [ ] Closed listings can be reactivated
- [ ] Agents return proper results
- [ ] UI updates after actions without refresh

---

## Deployment Notes

1. **Environment Variables** (already configured):
   - `DEMO_PASSWORD` — Password for demo accounts

2. **Database** (currently in-memory):
   - Production needs persistent storage for:
     - Listing confirmation dates
     - Expiration tracking
     - User roles

3. **Authentication** (currently JWT-style tokens):
   - Production needs proper session management
   - OAuth/SAML for IBM SSO

4. **Email Service**:
   - Configure Outlook service for notifications
   - Set up templates for expiration reminders

---

## Summary

This implementation provides a complete owner portal that solves the three core problems:

1. ✅ **No more stale listings** — Default expiration forces accountability
2. ✅ **Accurate status** — Mismatch detection flags filled positions
3. ✅ **Transparent formality postings** — Candidates know what's real vs. compliance

The dual-portal architecture (candidate + owner) ensures each user type has the right tools for their needs, while AI agents proactively surface issues before they become problems.
