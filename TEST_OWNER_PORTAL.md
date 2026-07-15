# Testing the Owner Portal

## Quick Start

### 1. Start the Backend Server
```bash
cd backend
uvicorn app.main:app --reload
```

### 2. Open the Frontend
```bash
cd frontend
# Use any local server, e.g.:
python -m http.server 8080
# Or use Live Server extension in VS Code
```

### 3. Access the Application
- Frontend: http://localhost:8080
- Backend API: http://127.0.0.1:8000
- API Docs: http://127.0.0.1:8000/api/docs

---

## Test Scenarios

### Scenario 1: Owner Login and Dashboard

1. **Navigate to login page**: http://localhost:8080/login.html
2. **Select owner user**: Click on "Marcus Chen" (mchen) or "Sarah Williams" (swilliams)
3. **Expected**: Automatically routed to `owner.html`
4. **Verify**:
   - Header shows "IBM Professional Marketplace · Owner Portal"
   - Three tabs visible: "My listings", "Create listing", "Analytics"
   - "My listings" tab is active by default

### Scenario 2: View Owner Listings

1. **On owner dashboard**: You should see listing cards for seats owned by the logged-in user
2. **Each card shows**:
   - Title and client name
   - Status badge (Active, Expiring Soon, Expired, Formality)
   - Stats: Last updated, Expires in, Profs in play, Listing type
   - Action buttons
   - Alert box if action needed

### Scenario 3: Confirm Listing (Reset Expiration Timer)

1. **Find a listing** with "Expiring soon" badge
2. **Click** "Confirm still active" button
3. **Expected**:
   - Toast notification: "Listing confirmed. It will remain visible for 30 more days."
   - Listing refreshes with updated "Expires in: 30 days"
   - Status badge changes to "Active" (blue)
   - Alert box disappears

### Scenario 4: Change Listing Type

**Mark as Formality**:
1. **Find an "Active" listing** (real opening)
2. **Click** "Mark as formality" button
3. **Confirm** the dialog
4. **Expected**:
   - Badge changes to "Formality" (purple)
   - Listing type shows "Formality/compliance"
   - Info box appears explaining visibility in formality tab

**Mark as Actively Hiring**:
1. **Find a "Formality" listing**
2. **Click** "Mark as actively hiring" button
3. **Confirm** the dialog
4. **Expected**:
   - Badge changes to "Active" (blue)
   - Listing type shows "Actively hiring"

### Scenario 5: Close Listing

1. **Click** "Close listing" on any active listing
2. **Confirm** the dialog
3. **Expected**:
   - Toast notification: "Listing closed successfully"
   - Listing is no longer visible to candidates (check by switching to candidate portal)

### Scenario 6: Reactivate Expired Listing

1. **Find an expired listing** (red badge)
2. **Click** "Reactivate listing" button
3. **Expected**:
   - Badge changes to "Active"
   - "Expires in: 30 days"
   - Available to candidates again

### Scenario 7: Run Expiration Check Agent

1. **Click** "Check all my listings for expiration" button
2. **Wait** for agent to complete
3. **Expected output**:
   - Summary: "X listing(s) expiring within 7 days | Y listing(s) already expired"
   - List of recommendations with:
     - Listing name
     - Action needed
     - Urgency level (high/medium)
     - Detailed message

### Scenario 8: Run Mismatch Detection Agent

1. **Click** "Check for filled-but-posted listings" button
2. **Wait** for agent to complete
3. **Expected output**:
   - If no mismatches: "✅ No mismatches detected"
   - If mismatches found:
     - Count of mismatches
     - List showing:
       - Listing title
       - Reason for mismatch
       - AI recommendation

### Scenario 9: Role-Based Access Control

**Test Owner → Candidate Redirect**:
1. **As owner user**, manually navigate to http://localhost:8080/index.html
2. **Expected**: Redirected to `owner.html` (owners can't access candidate portal)

**Test Candidate → Owner Redirect**:
1. **Log out** and log in as candidate (anguyen or jsmith)
2. **Expected**: Routed to `index.html` (candidate portal)
3. **Manually navigate** to http://localhost:8080/owner.html
4. **Expected**: Redirected to `index.html` (candidates can't access owner portal)

### Scenario 10: Create Listing Form

1. **Click** "Create listing" tab
2. **Fill out the form**:
   - Position title: "Test Senior Developer"
   - Client name: "Test Client Corp"
   - Work location: "Remote"
   - Work remotely: "Yes"
   - Band low: "6"
   - Band high: "7"
   - **Required**: Select listing type (Actively hiring OR Formality/compliance)
3. **Click** "Create listing"
4. **Expected**: Toast message "Create listing functionality coming soon"
   - (Note: Full CRUD not yet implemented, but form validates listing type selection)

### Scenario 11: Analytics Dashboard

1. **Click** "Analytics" tab
2. **View**:
   - Summary cards with counts:
     - Active listings
     - Expiring soon (7 days)
     - Formality postings
     - Total candidates in play
   - Listing health table with actionable items

---

## API Testing (via Swagger UI)

### Access API Docs
Navigate to: http://127.0.0.1:8000/api/docs

### Test Owner Endpoints

**Note**: You need a valid token from login. Get it by:
1. POST `/api/auth/login` with `{"username": "mchen", "password": "password"}`
2. Copy the `token` from response
3. Click "Authorize" button in Swagger UI
4. Enter: `Bearer <your-token>`

**Test These Endpoints**:

1. **GET /api/owner/my-listings**
   - Returns all listings for current owner
   - Check that `days_until_expiration` and `is_expired` are calculated

2. **POST /api/owner/confirm-listing**
   - Body: `{"seat_id": "SEAT-001"}`
   - Should return updated listing with `days_until_expiration: 30`

3. **POST /api/owner/update-listing-type**
   - Body: `{"seat_id": "SEAT-001", "seat_type": "formal"}`
   - Should change listing to formality type

4. **POST /api/owner/close-listing/{seat_id}**
   - Path param: `SEAT-001`
   - Should mark `is_available: false`

5. **POST /api/owner/reactivate-listing/{seat_id}**
   - Reactivates closed listing with fresh 30-day timer

6. **POST /api/agents/expiration-check**
   - Body: Array of Seat objects
   - Returns expiration analysis

7. **POST /api/agents/mismatch-check**
   - Body: `{"seat_id": "SEAT-001"}`
   - Returns mismatch detection result

---

## Expected Data Flow

### Listing Lifecycle

```
[Created] 
    ↓
[Active - 30 days remaining]
    ↓ (no action)
[Expiring Soon - ≤7 days] ← Agent sends warning
    ↓ (no action)
[Expired - hidden from candidates]
    ↓ (owner confirms)
[Active - 30 days remaining] ← Timer reset
```

### Listing States

- **Active (real)**: Open position, actively hiring
- **Active (formal)**: Compliance posting, candidates see separate tab
- **Expiring Soon**: Within 7 days of expiration
- **Expired**: Past expiration date, hidden from public
- **Closed**: Manually closed by owner

---

## Troubleshooting

### Backend won't start
```bash
# Check Python dependencies
pip install -r requirements.txt

# Verify FastAPI is installed
python -c "import fastapi; print(fastapi.__version__)"
```

### Frontend won't load data
```bash
# Check CORS settings in backend/app/main.py
# Verify API_BASE URL in frontend/js/owner.js matches backend
```

### Authentication issues
```bash
# Check localStorage in browser dev tools
# Should contain:
# - prom_token
# - prom_user_id
# - prom_user_name
# - prom_user_role
```

### Role routing not working
```bash
# Clear localStorage
localStorage.clear()

# Re-login and check prom_user_role value
```

---

## Success Criteria

✅ Owner can log in and see their listings only  
✅ Expiration countdown displays correctly  
✅ "Confirm still active" resets timer to 30 days  
✅ Listing type can be changed (real ↔ formality)  
✅ Expired listings show as hidden  
✅ Agents return actionable recommendations  
✅ Candidates redirected away from owner portal  
✅ Owners redirected away from candidate portal  

---

## Next Steps After Testing

1. **Integrate with real database** (replace in-memory _SEATS)
2. **Implement full CRUD** for listings
3. **Set up automated email reminders** using Outlook service
4. **Add scheduled cron jobs** for daily expiration checks
5. **Connect to WatsonX AI** for enhanced recommendations
6. **Add audit logging** for compliance tracking
