from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, List
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel

from app.models.seat import Seat, SeatType
from app.services.seat_service import get_all_seats, get_seat_by_id, update_seat
from app.models.auth import User
from app.services.auth_service import get_current_user

router = APIRouter()


class ConfirmListingRequest(BaseModel):
    seat_id: str


class UpdateListingTypeRequest(BaseModel):
    seat_id: str
    seat_type: SeatType


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
