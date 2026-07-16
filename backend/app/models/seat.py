from __future__ import annotations
from datetime import date, datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CandidateStatus(str, Enum):
    PROPOSED = "P"
    SELECTED = "S"
    NOT_SELECTED = "N"
    WITHDRAWN = "W"


class SeatType(str, Enum):
    FORMAL = "formal"
    REAL = "real"


class StatusBreakdown(BaseModel):
    proposed: int = 0
    selected: int = 0
    not_selected: int = 0
    withdrawn: int = 0


class Seat(BaseModel):
    seat_id: str
    title: str
    client_name: str
    owner_notes_id: str
    owner_professional_id: Optional[str] = None
    service: str
    requested_band_high: str
    requested_band_low: str
    contract_owning_country: str
    work_location: str
    work_remotely: bool
    sector: str
    industry: str
    last_updated: datetime
    days_since_update: int
    candidate_status: Optional[CandidateStatus] = None
    profs_in_play: int = 0
    status_breakdown: Optional[StatusBreakdown] = None
    positions_still_needed: int = 1
    start_date: Optional[date] = None
    clearance_needed: Optional[str] = None
    seat_type: SeatType = SeatType.REAL
    is_stale: bool = False
    has_applied: bool = False
    is_available: bool = True
    mismatch_flag: bool = False
    ai_recommendation_note: Optional[str] = None
    last_confirmed_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    days_until_expiration: Optional[int] = None
    is_expired: bool = False


class SeatSearchParams(BaseModel):
    query: Optional[str] = None
    work_location: Optional[str] = None
    work_remotely: Optional[bool] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    band: Optional[str] = None
    owner_notes_id: Optional[str] = None
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=30, ge=10, le=50)


class SeatListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    seats: list[Seat]
