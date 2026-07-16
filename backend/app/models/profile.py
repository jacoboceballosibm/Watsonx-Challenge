from __future__ import annotations
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class Profile(BaseModel):
    professional_id: str
    name: str
    w3_link: Optional[str] = None
    availability_date: date
    current_open_seats: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    cv_overview: Optional[str] = None
    cv_contact: dict[str, str] = Field(default_factory=dict)
    cv_sections: dict[str, str] = Field(default_factory=dict)
    band: Optional[str] = None
    location: Optional[str] = None
    cv_repository_url: Optional[str] = None


class ProfileUpdateRequest(BaseModel):
    availability_date: Optional[date] = None
    skills: Optional[list[str]] = None
    cv_overview: Optional[str] = None
    cv_contact: Optional[dict[str, str]] = None
    cv_sections: Optional[dict[str, str]] = None
    location: Optional[str] = None
