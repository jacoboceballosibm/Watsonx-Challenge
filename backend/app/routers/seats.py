from fastapi import APIRouter, Query
from typing import Optional
from app.models.seat import SeatListResponse, Seat, SeatSearchParams
from app.services.seat_service import search_seats, get_seat_by_id

router = APIRouter()


@router.get("/", response_model=SeatListResponse)
def list_seats(
    query: Optional[str] = Query(default=None),
    work_location: Optional[str] = Query(default=None),
    work_remotely: Optional[bool] = Query(default=None),
    sector: Optional[str] = Query(default=None),
    band: Optional[str] = Query(default=None),
    owner_notes_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=30, ge=10, le=50),
):
    params = SeatSearchParams(
        query=query,
        work_location=work_location,
        work_remotely=work_remotely,
        sector=sector,
        band=band,
        owner_notes_id=owner_notes_id,
        page=page,
        per_page=per_page,
    )
    return search_seats(params)


@router.get("/{seat_id}", response_model=Seat)
def get_seat(seat_id: str):
    from fastapi import HTTPException
    seat = get_seat_by_id(seat_id)
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")
    return seat
