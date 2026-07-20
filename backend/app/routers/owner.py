from fastapi import APIRouter, HTTPException, Depends, Response
from typing import Optional, List, Dict
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from fastapi.responses import JSONResponse

from app.models.application import SeatApplicantsResponse
from app.models.seat import Seat, SeatType, CandidateStatus
from app.services.application_service import list_applicants_for_seat
from app.services.seat_service import get_all_seats, get_seat_by_id, update_seat
from app.models.auth import User
from app.services.auth_service import get_current_user

router = APIRouter()


class DashboardData(BaseModel):
    expiration_dashboard: Dict[str, List[Seat]]
    mismatch_dashboard: List[Dict]
    last_updated: datetime


class ConfirmListingRequest(BaseModel):
    seat_id: str


class UpdateListingTypeRequest(BaseModel):
    seat_id: str
    seat_type: SeatType


class UpdateListingRequest(BaseModel):
    title: Optional[str] = None
    client_name: Optional[str] = None
    work_location: Optional[str] = None
    positions_still_needed: Optional[int] = None
    requested_band_low: Optional[str] = None
    requested_band_high: Optional[str] = None


class ListingActionResponse(BaseModel):
    success: bool
    message: str
    seat: Optional[Seat] = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _is_owner(seat: Seat, user: User) -> bool:
    return seat.owner_professional_id == user.professional_id


@router.get("/my-listings", response_model=List[Seat])
def get_owner_listings(current_user: User = Depends(get_current_user)):
    """
    Get all listings owned by the current user
    """
    all_seats = get_all_seats()
    owner_seats = [
        seat for seat in all_seats
        if _is_owner(seat, current_user)
    ]

    # Calculate expiration data for each seat
    for seat in owner_seats:
        if seat.last_confirmed_date:
            seat.expiration_date = seat.last_confirmed_date + timedelta(days=30)
            days_left = (seat.expiration_date - _now()).days
            seat.days_until_expiration = max(0, days_left)
            seat.is_expired = days_left < 0
        else:
            # Default: assume confirmation is last_updated date
            seat.expiration_date = seat.last_updated + timedelta(days=30)
            days_left = (seat.expiration_date - _now()).days
            seat.days_until_expiration = max(0, days_left)
            seat.is_expired = days_left < 0

    return owner_seats


@router.get("/listings/{seat_id}/applicants", response_model=SeatApplicantsResponse)
def get_listing_applicants(seat_id: str, current_user: User = Depends(get_current_user)):
    """Return professionals already applied / in play for an owned listing."""
    seat = get_seat_by_id(seat_id)
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")
    if not _is_owner(seat, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to view applicants for this listing")

    applicants = list_applicants_for_seat(seat_id)
    return SeatApplicantsResponse(
        seat_id=seat_id,
        total=len(applicants),
        applicants=applicants,
    )


@router.post("/confirm-listing", response_model=ListingActionResponse)
def confirm_listing(
    request: ConfirmListingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Confirm that a listing is still active.
    This resets the expiration timer to 30 days from now.
    """
    seat = get_seat_by_id(request.seat_id)

    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    if not _is_owner(seat, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to modify this listing")

    # Update confirmation date and expiration
    seat.last_confirmed_date = _now()
    seat.expiration_date = seat.last_confirmed_date + timedelta(days=30)
    seat.days_until_expiration = 30
    seat.is_expired = False
    seat.last_updated = _now()
    seat.days_since_update = 0
    update_seat(seat)

    return ListingActionResponse(
        success=True,
        message=f"Listing confirmed. It will remain visible for 30 more days.",
        seat=seat
    )


@router.post("/update-listing-type", response_model=ListingActionResponse)
def update_listing_type(
    request: UpdateListingTypeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update the listing type (real vs formal)
    """
    seat = get_seat_by_id(request.seat_id)

    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    if not _is_owner(seat, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to modify this listing")

    seat.seat_type = request.seat_type
    seat.last_updated = _now()
    update_seat(seat)

    type_name = "actively hiring" if request.seat_type == SeatType.REAL else "formality/compliance posting"

    return ListingActionResponse(
        success=True,
        message=f"Listing type updated to: {type_name}",
        seat=seat
    )


@router.post("/close-listing/{seat_id}", response_model=ListingActionResponse)
def close_listing(seat_id: str, current_user: User = Depends(get_current_user)):
    """
    Close a listing (mark as unavailable)
    """
    seat = get_seat_by_id(seat_id)

    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    if not _is_owner(seat, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to modify this listing")

    seat.is_available = False
    seat.last_updated = _now()
    update_seat(seat)

    return ListingActionResponse(
        success=True,
        message="Listing closed successfully",
        seat=seat
    )


@router.post("/reactivate-listing/{seat_id}", response_model=ListingActionResponse)
def reactivate_listing(seat_id: str, current_user: User = Depends(get_current_user)):
    """
    Reactivate an expired or closed listing
    """
    seat = get_seat_by_id(seat_id)

    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    if not _is_owner(seat, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to modify this listing")

    seat.is_available = True
    seat.last_confirmed_date = _now()
    seat.expiration_date = seat.last_confirmed_date + timedelta(days=30)
    seat.days_until_expiration = 30
    seat.is_expired = False
    seat.last_updated = _now()
    seat.days_since_update = 0
    update_seat(seat)

    return ListingActionResponse(
        success=True,
        message="Listing reactivated and will remain visible for 30 days",
        seat=seat
    )


@router.put("/update-listing/{seat_id}", response_model=ListingActionResponse)
def update_listing(
    seat_id: str,
    request: UpdateListingRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Update listing details
    """
    seat = get_seat_by_id(seat_id)

    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")

    if not _is_owner(seat, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to modify this listing")

    # Update only provided fields
    if request.title is not None:
        seat.title = request.title
    if request.client_name is not None:
        seat.client_name = request.client_name
    if request.work_location is not None:
        seat.work_location = request.work_location
    if request.positions_still_needed is not None:
        seat.positions_still_needed = request.positions_still_needed
    if request.requested_band_low is not None:
        seat.requested_band_low = request.requested_band_low
    if request.requested_band_high is not None:
        seat.requested_band_high = request.requested_band_high

    seat.last_updated = _now()
    update_seat(seat)

    return ListingActionResponse(
        success=True,
        message="Listing updated successfully",
        seat=seat
    )


@router.get("/dashboard")
def get_owner_dashboard(current_user: User = Depends(get_current_user)):
    """
    Get automated dashboard data for owner
    Returns categorized listings for expiration and mismatch checks
    """
    all_seats = get_all_seats()
    owner_seats = [seat for seat in all_seats if _is_owner(seat, current_user)]

    now = _now()

    # Expiration Dashboard - 4 categories
    expiration_dashboard = {
        '30_days': [],  # 30+ days left
        '15_days': [],  # 15-29 days left
        'soon': [],     # 1-14 days left (7 days warning)
        'expired': []   # 0 or negative days
    }

    for seat in owner_seats:
        if not seat.is_available:
            continue

        # Calculate days until expiration
        last_update = seat.last_confirmed_date or seat.last_updated
        expiration_date = last_update + timedelta(days=30)
        days_left = (expiration_date - now).days

        seat.days_until_expiration = days_left
        seat.expiration_date = expiration_date
        seat.is_expired = days_left < 0

        if days_left < 0:
            expiration_dashboard['expired'].append(seat)
        elif days_left <= 7:
            expiration_dashboard['soon'].append(seat)
        elif days_left <= 15:
            expiration_dashboard['15_days'].append(seat)
        else:
            expiration_dashboard['30_days'].append(seat)

    # Mismatch Dashboard
    mismatch_dashboard = []
    for seat in owner_seats:
        if not seat.is_available:
            continue

        applicants = list_applicants_for_seat(seat.seat_id)
        selected_count = sum(1 for app in applicants if app.status == CandidateStatus.SELECTED)

        if selected_count >= seat.positions_still_needed:
            mismatch_dashboard.append({
                'seat': seat,
                'selected_count': selected_count,
                'positions_available': seat.positions_still_needed,
                'message': f"Seat '{seat.title}' has {selected_count} candidates already Selected, but only {seat.positions_still_needed} position(s) needed. The listing should be closed or marked as formality/compliance posting if keeping it open for compliance."
            })

    # Convert Seat objects to dicts (handle both Pydantic v1 and v2)
    def seat_to_dict(seat):
        if hasattr(seat, 'model_dump'):
            return seat.model_dump(mode='json')
        else:
            return seat.dict()

    expiration_dict = {
        key: [seat_to_dict(seat) for seat in seats]
        for key, seats in expiration_dashboard.items()
    }

    mismatch_dict = [
        {
            "seat": seat_to_dict(m["seat"]),
            "selected_count": m["selected_count"],
            "positions_available": m["positions_available"],
            "message": m["message"]
        }
        for m in mismatch_dashboard
    ]

    result = {
        "expiration_dashboard": expiration_dict,
        "mismatch_dashboard": mismatch_dict,
        "last_updated": now.isoformat()
    }

    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )
