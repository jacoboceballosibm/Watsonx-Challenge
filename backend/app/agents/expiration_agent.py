"""
Expiration Agent: Checks listings for expiration and drafts reconfirmation reminders

Problem solved: Listings sit for months with no updates
Solution: Reviews listings on a schedule, checks days-since-update, drafts the
          reconfirmation nudge to the owner
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.models.seat import Seat
from app.models.agent import AgentResponse


def check_listing_expiration(seats: List[Seat], threshold_days: int = 7) -> AgentResponse:
    """
    Check which listings are approaching expiration (default: within 7 days)

    Args:
        seats: List of seat listings to check
        threshold_days: Number of days before expiration to flag listings

    Returns:
        AgentResponse with expiring listings and recommendations
    """
    expiring_soon = []
    expired_listings = []

    for seat in seats:
        # Calculate expiration status
        if seat.last_confirmed_date:
            expiration_date = seat.last_confirmed_date + timedelta(days=30)
        else:
            # Use last_updated as fallback
            expiration_date = seat.last_updated + timedelta(days=30)

        days_until_expiration = (expiration_date - datetime.now()).days

        # Categorize listings
        if days_until_expiration < 0:
            expired_listings.append({
                "seat_id": seat.seat_id,
                "title": seat.title,
                "client_name": seat.client_name,
                "days_expired": abs(days_until_expiration),
                "last_updated": seat.last_updated.strftime("%Y-%m-%d"),
                "profs_in_play": seat.profs_in_play,
            })
        elif days_until_expiration <= threshold_days:
            expiring_soon.append({
                "seat_id": seat.seat_id,
                "title": seat.title,
                "client_name": seat.client_name,
                "days_until_expiration": days_until_expiration,
                "last_updated": seat.last_updated.strftime("%Y-%m-%d"),
                "profs_in_play": seat.profs_in_play,
            })

    # Generate summary message
    summary_parts = []

    if expiring_soon:
        summary_parts.append(
            f"⚠️ {len(expiring_soon)} listing(s) expiring within {threshold_days} days"
        )

    if expired_listings:
        summary_parts.append(
            f"🔒 {len(expired_listings)} listing(s) already expired and hidden from candidates"
        )

    if not expiring_soon and not expired_listings:
        summary_parts.append("✅ All listings are up to date. No action needed.")

    summary = " | ".join(summary_parts)

    # Generate recommendations
    recommendations = []

    for listing in expiring_soon:
        recommendations.append({
            "listing": f"{listing['title']} ({listing['client_name']})",
            "action": "Confirm still active",
            "urgency": "high" if listing['days_until_expiration'] <= 3 else "medium",
            "message": f"This listing will expire in {listing['days_until_expiration']} day(s). "
                      f"Click 'Confirm still active' to extend visibility for 30 days."
        })

    for listing in expired_listings:
        recommendations.append({
            "listing": f"{listing['title']} ({listing['client_name']})",
            "action": "Reactivate or delete",
            "urgency": "high",
            "message": f"This listing expired {listing['days_expired']} day(s) ago and is no longer visible. "
                      f"Reactivate if still open, or delete if filled."
        })

    # Prepare detailed data
    data = {
        "expiring_soon": expiring_soon,
        "expired_listings": expired_listings,
        "recommendations": recommendations,
        "total_flagged": len(expiring_soon) + len(expired_listings),
    }

    return AgentResponse(
        agent_name="expiration_agent",
        summary=summary,
        data=data,
        success=True
    )


def draft_reconfirmation_email(listing: Dict[str, Any]) -> str:
    """
    Draft an automated reconfirmation email for the owner

    Args:
        listing: Dictionary containing listing information

    Returns:
        Email draft text
    """
    return f"""
Subject: Action Required: Confirm your ProM listing - {listing['title']}

Hi,

Your ProM listing "{listing['title']}" for {listing['client_name']} is approaching expiration.

📊 Current status:
- Days until expiration: {listing.get('days_until_expiration', 'N/A')}
- Professionals in play: {listing.get('profs_in_play', 0)}
- Last updated: {listing.get('last_updated', 'N/A')}

⚠️ ACTION NEEDED:
To keep this listing visible to candidates, please confirm it's still an active opening.

Options:
1. ✅ Still actively hiring → Click "Confirm still active" to extend visibility for 30 days
2. 🔒 Position filled → Close the listing to hide it from candidates
3. 📝 Compliance posting → Mark as "Formality/compliance" so candidates see accurate expectations

🔗 Manage this listing: [Owner Portal Link]

If you take no action, this listing will automatically expire and be hidden from public view in {listing.get('days_until_expiration', 'N/A')} day(s).

---
This is an automated reminder from IBM Professional Marketplace
""".strip()
