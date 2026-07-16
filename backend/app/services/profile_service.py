"""Profile service backed by the local SQLite database."""
from __future__ import annotations

from datetime import date
import json
from typing import Optional

from app.models.profile import Profile, ProfileUpdateRequest
from app.services.database import get_connection

_DEFAULT_CV_SECTIONS = {
    "work_experience": (
        "Senior Developer\n"
        "Northwind Digital - Austin, TX\n"
        "Jan 2023 - Present\n"
        "Builds internal and client-facing applications, improves delivery workflows, and contributes to reusable engineering patterns for delivery teams."
    ),
    "ibm_assignment_history": (
        "Platform Modernization Support\n"
        "Example Federal Agency - Mar 2025 - Sep 2025\n"
        "Supported planning, coordination, and technical delivery activities.\n"
        "Helped document workflows and implementation milestones."
    ),
    "additional_client_history": "",
    "industry_experience": "Financial Services\nProficiency: Intermediate",
    "education": "B.S. in Computer Science\nExample State University, 2022",
    "languages": "English\nSpoken proficiency: Fluent\nWritten proficiency: Fluent",
    "publications": "",
    "memberships": "",
    "additional_information": (
        "Enterprise Portal Refresh\n"
        "Technical contributor - 2026\n"
        "Helped deliver updated user experiences for a large internal platform.\n"
        "Supported implementation planning, testing, and release readiness.\n"
        "Contributed to shared components and engineering documentation."
    ),
}

_SEED_PROFILES: dict[str, Profile] = {
    "A5XCVSPCNN2O": Profile(
        professional_id="A5XCVSPCNN2O",
        name="Alysa Nguyen/US/IBM",
        w3_link="https://w3.ibm.com/people/alysanguyen",
        availability_date=date(2025, 12, 29),
        current_open_seats=[],
        skills=["Python", "AI/ML", "Cloud", "FastAPI", "React"],
        cv_overview="Alysa Nguyen is an IBM professional with experience delivering AI-enabled, cloud-ready applications and API services for enterprise teams.",
        cv_contact={
            "name": "Alysa Nguyen",
            "title": "IBM AI Application Developer",
            "phone": "(555) 010-1001",
            "email": "alysanguyen@example.com",
        },
        cv_sections=_DEFAULT_CV_SECTIONS,
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
        cv_overview="John Smith is a software developer with experience delivering modern web applications, API integrations, and cloud-ready solutions for enterprise teams.",
        cv_contact={
            "name": "John Smith",
            "title": "Senior Developer",
            "phone": "(555) 010-1234",
            "email": "john.smith@example.com",
        },
        cv_sections=_DEFAULT_CV_SECTIONS,
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
        cv_overview="Marcus Chen is an engineering leader focused on scalable Java platforms, microservices, and Kubernetes-based delivery.",
        cv_contact={
            "name": "Marcus Chen",
            "title": "Platform Engineering Lead",
            "phone": "(555) 010-2001",
            "email": "marcus.chen@example.com",
        },
        cv_sections=_DEFAULT_CV_SECTIONS,
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
        cv_overview="Sarah Williams is a data science professional with experience building machine learning solutions and analytical workflows.",
        cv_contact={
            "name": "Sarah Williams",
            "title": "Data Science Consultant",
            "phone": "(555) 010-3001",
            "email": "sarah.williams@example.com",
        },
        cv_sections=_DEFAULT_CV_SECTIONS,
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
        cv_overview="David Rodriguez is a cloud architecture leader with experience designing secure infrastructure across AWS and Azure.",
        cv_contact={
            "name": "David Rodriguez",
            "title": "Cloud Architect",
            "phone": "(555) 010-4001",
            "email": "david.rodriguez@example.com",
        },
        cv_sections=_DEFAULT_CV_SECTIONS,
        band="9",
        location="Mexico",
        cv_repository_url=None,
    ),
}


def _profile_from_row(row) -> Profile:
    return Profile(
        professional_id=row["professional_id"],
        name=row["name"],
        w3_link=row["w3_link"],
        availability_date=date.fromisoformat(row["availability_date"]),
        current_open_seats=json.loads(row["current_open_seats_json"]),
        skills=json.loads(row["skills_json"]),
        cv_overview=row["cv_overview"],
        cv_contact=json.loads(row["cv_contact_json"] or "{}"),
        cv_sections=json.loads(row["cv_sections_json"] or "{}"),
        band=row["band"],
        location=row["location"],
        cv_repository_url=row["cv_repository_url"],
    )


def get_profile(professional_id: str) -> Optional[Profile]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM profiles WHERE professional_id = ?",
            (professional_id,),
        ).fetchone()
    return _profile_from_row(row) if row else None


def update_profile(professional_id: str, updates: ProfileUpdateRequest) -> Optional[Profile]:
    profile = get_profile(professional_id)
    if not profile:
        return None

    data = profile.model_dump()
    for field, value in updates.model_dump(exclude_none=True).items():
        data[field] = value

    updated = Profile(**data)
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE profiles
            SET availability_date = ?,
                current_open_seats_json = ?,
                skills_json = ?,
                cv_overview = ?,
                cv_contact_json = ?,
                cv_sections_json = ?,
                location = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE professional_id = ?
            """,
            (
                updated.availability_date.isoformat(),
                json.dumps(updated.current_open_seats),
                json.dumps(updated.skills),
                updated.cv_overview,
                json.dumps(updated.cv_contact),
                json.dumps(updated.cv_sections),
                updated.location,
                professional_id,
            ),
        )
    return updated


def seed_profiles() -> None:
    with get_connection() as conn:
        for profile in _SEED_PROFILES.values():
            conn.execute(
                """
                INSERT OR IGNORE INTO profiles (
                    professional_id,
                    name,
                    w3_link,
                    availability_date,
                    current_open_seats_json,
                    skills_json,
                    cv_overview,
                    cv_contact_json,
                    cv_sections_json,
                    band,
                    location,
                    cv_repository_url
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile.professional_id,
                    profile.name,
                    profile.w3_link,
                    profile.availability_date.isoformat(),
                    json.dumps(profile.current_open_seats),
                    json.dumps(profile.skills),
                    profile.cv_overview,
                    json.dumps(profile.cv_contact),
                    json.dumps(profile.cv_sections),
                    profile.band,
                    profile.location,
                    profile.cv_repository_url,
                ),
            )
            conn.execute(
                """
                UPDATE profiles
                SET cv_overview = COALESCE(cv_overview, ?)
                WHERE professional_id = ?
                """,
                (profile.cv_overview, profile.professional_id),
            )
            conn.execute(
                """
                UPDATE profiles
                SET cv_contact_json = CASE
                    WHEN cv_contact_json IS NULL OR cv_contact_json = '{}' THEN ?
                    ELSE cv_contact_json
                END
                WHERE professional_id = ?
                """,
                (json.dumps(profile.cv_contact), profile.professional_id),
            )
            conn.execute(
                """
                UPDATE profiles
                SET cv_sections_json = CASE
                    WHEN cv_sections_json IS NULL OR cv_sections_json = '{}' THEN ?
                    ELSE cv_sections_json
                END
                WHERE professional_id = ?
                """,
                (json.dumps(profile.cv_sections), profile.professional_id),
            )
