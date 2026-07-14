from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel


class Profile(BaseModel):
    professional_id: str
    name: str
    w3_link: Optional[str] = None
    availability_date: date
    current_open_seats: list[str] = []
    skills: list[str] = []
    band: Optional[str] = None
    location: Optional[str] = None
    cv_repository_url: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    availability_date: Optional[date] = None
    skills: Optional[list[str]] = None
    location: Optional[str] = None
