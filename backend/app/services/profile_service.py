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
        skills=["Python", "AI/ML", "Cloud", "FastAPI", "React"],
        band="7",
        location="United States",
        cv_repository_url=None,
    ),
    "JS7BQM3PXWK1": Profile(
        professional_id="JS7BQM3PXWK1",
        name="John Smith/UK/IBM",
        w3_link="https://w3.ibm.com/people/jsmith",
        availability_date=date(2026, 3, 15),
        current_open_seats=[],
        skills=["JavaScript", "TypeScript", "Node.js", "React", "Docker"],
        band="6",
        location="United Kingdom",
        cv_repository_url=None,
    ),
    "MC2NVD9RTPW5": Profile(
        professional_id="MC2NVD9RTPW5",
        name="Marcus Chen/SG/IBM",
        w3_link="https://w3.ibm.com/people/mchen",
        availability_date=date(2026, 1, 20),
        current_open_seats=[],
        skills=["Java", "Spring Boot", "Kubernetes", "Microservices", "DevOps"],
        band="8",
        location="Singapore",
        cv_repository_url=None,
    ),
    "SW8FHK4TQNX7": Profile(
        professional_id="SW8FHK4TQNX7",
        name="Sarah Williams/CA/IBM",
        w3_link="https://w3.ibm.com/people/swilliams",
        availability_date=date(2026, 2, 10),
        current_open_seats=[],
        skills=["Data Science", "Machine Learning", "Python", "TensorFlow", "SQL"],
        band="7",
        location="Canada",
        cv_repository_url=None,
    ),
    "DR3KGP6LMZY8": Profile(
        professional_id="DR3KGP6LMZY8",
        name="David Rodriguez/MX/IBM",
        w3_link="https://w3.ibm.com/people/drodriguez",
        availability_date=date(2026, 4, 1),
        current_open_seats=[],
        skills=["Cloud Architecture", "AWS", "Azure", "Infrastructure", "Security"],
        band="9",
        location="Mexico",
        cv_repository_url=None,
    ),
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
