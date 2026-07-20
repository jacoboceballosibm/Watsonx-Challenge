# Automated Dashboards for Listing Owners

## Overview

The Owner Portal now features **two automated dashboards** that run daily at 12:00 AM to help listing owners manage their postings efficiently.

## Features

### 1. Listing Expiration Dashboard

Automatically categorizes all active listings based on days until expiration:

#### Categories

| Category | Days Left | Color | Description |
|----------|-----------|-------|-------------|
| **30 Days Left** | 16-30 days | Green | Listings with plenty of time remaining |
| **15 Days Left** | 8-15 days | Yellow | Listings needing attention soon |
| **Expiring Soon** | 1-7 days | Orange | Urgent: expiring within a week |
| **Expired** | 0 or less | Red | Hidden from candidates, need reactivation |

#### Actions Available

**For Active Listings (30/15/Soon):**
- **Confirm Active** - Resets expiration timer to 30 days
- **View Details** - Navigate to full listing details

**For Expired Listings:**
- **Reactivate** - Reopens listing and resets timer to 30 days
- **View Details** - Review listing before reactivating

### 2. Filled-But-Posted Mismatch Dashboard

Detects listings where enough candidates have been selected but the listing remains open.

#### Detection Logic
- Counts candidates with "Selected" status
- Compares to `positions_available`
- Flags when `selected_count >= positions_available`

#### Actions Available

- **Close Listing** - Marks listing as unavailable (best practice)
- **Mark as Formal** - Changes to formality/compliance posting
- **View Applicants** - Review all candidates for this listing

## Automation

### Daily Schedule

The system runs two automated checks every day at **12:00 AM (midnight)**:

1. **Expiration Check** - Categorizes all listings by expiration status
2. **Mismatch Detection** - Identifies filled-but-posted listings

### Manual Refresh

Owners can manually refresh the dashboard at any time using the **Refresh** button in the top-right corner.

### Auto-Refresh

The dashboard automatically refreshes every **5 minutes** while the page is open.

## Technical Implementation

### Backend (`app/scheduler.py`)

```python
# Daily scheduler runs at 00:00
scheduler.schedule_daily(0, 0, check_all_listings_expiration)
scheduler.schedule_daily(0, 0, check_all_listings_mismatch)
```

### API Endpoint

```
GET /api/owner/dashboard
```

Returns:
```json
{
  "expiration_dashboard": {
    "30_days": [...],
    "15_days": [...],
    "soon": [...],
    "expired": [...]
  },
  "mismatch_dashboard": [...],
  "last_updated": "2026-07-20T00:00:00Z"
}
```

### Frontend

- **UI**: `frontend/owner.html`
- **Dashboard Logic**: `frontend/js/owner-dashboard.js`
- **Styles**: `frontend/css/prom.css` (`.dashboard-*` classes)

## Benefits

✅ **Proactive Management** - No manual checking needed  
✅ **Clear Categorization** - Visual indicators for urgency  
✅ **Quick Actions** - One-click solutions for common tasks  
✅ **Automated Daily Updates** - Always current without intervention  
✅ **Compliance Support** - Easy identification of formal postings  

## Usage

1. **Navigate to Owner Portal** - Sign in as a listing owner
2. **View Dashboards** - Both dashboards load automatically
3. **Review Categories** - Check counts in each category
4. **Take Action** - Click buttons to confirm, close, or mark listings
5. **Auto-Sync** - Dashboards refresh automatically

## Configuration

### Changing Schedule Time

Edit `backend/app/scheduler.py`:

```python
# Change from midnight (0, 0) to another time
scheduler.schedule_daily(9, 0, check_all_listings_expiration)  # 9:00 AM
```

### Expiration Thresholds

Edit category logic in `backend/app/routers/owner.py`:

```python
if days_left < 0:
    expiration_dashboard['expired'].append(seat)
elif days_left <= 7:  # Change this threshold
    expiration_dashboard['soon'].append(seat)
```

## Future Enhancements

- **Email Notifications** - Alert owners before expiration
- **Slack Integration** - Post daily summaries to Slack
- **Custom Schedules** - Let owners choose notification times
- **Bulk Actions** - Confirm or close multiple listings at once
- **Analytics** - Track expiration and mismatch trends over time

## Troubleshooting

**Dashboard shows "Loading..."**
- Check backend is running on correct port
- Verify authentication token is valid
- Check browser console for errors

**No listings showing**
- Ensure user is logged in as owner role
- Verify listings exist in database
- Check `_is_owner()` logic in backend

**Scheduler not running**
- Check backend logs for "Daily scheduler started"
- Verify `setup_daily_tasks()` is called in `main.py`
- Ensure FastAPI startup event is triggered

**Wrong categorization**
- Check `last_confirmed_date` and `last_updated` fields
- Verify timezone handling (UTC vs local)
- Review expiration calculation logic

## Related Files

- Backend Scheduler: `backend/app/scheduler.py`
- Owner Endpoints: `backend/app/routers/owner.py`
- Dashboard UI: `frontend/owner.html`
- Dashboard JS: `frontend/js/owner-dashboard.js`
- Styles: `frontend/css/prom.css`
