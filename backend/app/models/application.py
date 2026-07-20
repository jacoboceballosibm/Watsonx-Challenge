from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.seat import CandidateStatus


class SeatApplication(BaseModel):
    application_id: str
    seat_id: str
    professional_id: str
    status: CandidateStatus = CandidateStatus.PROPOSED
    applied_at: datetime
    notes: Optional[str] = None


class SeatApplicantView(BaseModel):
    application_id: str
    seat_id: str
    professional_id: str
    name: str
    band: Optional[str] = None
    location: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    status: CandidateStatus
    applied_at: datetime
    cv_overview: Optional[str] = None


class SeatApplicantsResponse(BaseModel):
    seat_id: str
    total: int
    applicants: list[SeatApplicantView]
