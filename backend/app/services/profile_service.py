"""
Profile service — stub implementation.
Replace the in-memory store with your real database queries.
"""
from __future__ import annotations
from datetime import date
from typing import Optional
from app.models.profile import Profile, ProfileUpdateRequest

# ── In-memory stub data ───────────────────────────────────────────────────────
_PROFILES: dict[str, Profile] = {
    "A5XCVSPCNN2O": Profile(
        professional_id="A5XCVSPCNN2O",
        name="Alysa Nguyen/US/IBM",
        w3_link="https://w3.ibm.com/people/alysanguyen",
        availability_date=date(2025, 12, 29),
        current_open_seats=[],
        skills=["Python", "AI/ML", "Cloud"],
        band="7",
        location="United States",
        cv_repository_url=None,
    )
}


def get_profile(professional_id: str) -> Optional[Profile]:
    return _PROFILES.get(professional_id)


def update_profile(professional_id: str, updates: ProfileUpdateRequest) -> Optional[Profile]:
    profile = _PROFILES.get(professional_id)
    if not profile:
        return None
    data = profile.model_dump()
    for field, value in updates.model_dump(exclude_none=True).items():
        data[field] = value
    _PROFILES[professional_id] = Profile(**data)
    return _PROFILES[professional_id]
