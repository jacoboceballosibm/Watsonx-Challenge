"""Seat applications — professionals already in play for a listing."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from app.models.application import SeatApplicantView, SeatApplication
from app.models.seat import CandidateStatus
from app.services.database import get_connection
from app.services.profile_service import get_profile

# Seed: applicants already applied / in play (never invents people at runtime).
# Owners are excluded from their own seats.
_SEED_APPLICATIONS: list[tuple[str, str, CandidateStatus]] = [
    # SEAT-001 Senior Full-Stack (Marcus) — JS/React fit should rank John high
    ("SEAT-001", "JS7BQM3PXWK1", CandidateStatus.PROPOSED),  # John — strong FE/JS
    ("SEAT-001", "A5XCVSPCNN2O", CandidateStatus.PROPOSED),  # Alysa — Python/AI
    ("SEAT-001", "SW8FHK4TQNX7", CandidateStatus.PROPOSED),  # Sarah — data
    ("SEAT-001", "DR3KGP6LMZY8", CandidateStatus.SELECTED),  # David — cloud/arch
    # SEAT-002 Cloud Infrastructure (Sarah)
    ("SEAT-002", "DR3KGP6LMZY8", CandidateStatus.PROPOSED),
    ("SEAT-002", "MC2NVD9RTPW5", CandidateStatus.PROPOSED),
    ("SEAT-002", "A5XCVSPCNN2O", CandidateStatus.PROPOSED),
    # SEAT-003 Data Science Lead (David)
    ("SEAT-003", "SW8FHK4TQNX7", CandidateStatus.PROPOSED),
    ("SEAT-003", "A5XCVSPCNN2O", CandidateStatus.PROPOSED),
    ("SEAT-003", "JS7BQM3PXWK1", CandidateStatus.NOT_SELECTED),
    # SEAT-005 Solutions Architect (Marcus)
    ("SEAT-005", "DR3KGP6LMZY8", CandidateStatus.PROPOSED),
    ("SEAT-005", "JS7BQM3PXWK1", CandidateStatus.PROPOSED),
    ("SEAT-005", "A5XCVSPCNN2O", CandidateStatus.WITHDRAWN),
    # SEAT-020 Full-Stack Developer (David) - 3 selected, 2 needed
    ("SEAT-020", "JS7BQM3PXWK1", CandidateStatus.SELECTED),
    ("SEAT-020", "A5XCVSPCNN2O", CandidateStatus.SELECTED),
    ("SEAT-020", "SW8FHK4TQNX7", CandidateStatus.SELECTED),
    ("SEAT-020", "MC2NVD9RTPW5", CandidateStatus.PROPOSED),
    # SEAT-021 Data Engineer (David) - 2 selected, 1 needed
    ("SEAT-021", "SW8FHK4TQNX7", CandidateStatus.SELECTED),
    ("SEAT-021", "A5XCVSPCNN2O", CandidateStatus.SELECTED),
    ("SEAT-021", "JS7BQM3PXWK1", CandidateStatus.PROPOSED),
    # SEAT-022 Cloud Solutions Architect (David) - 4 selected, 3 needed
    ("SEAT-022", "DR3KGP6LMZY8", CandidateStatus.SELECTED),
    ("SEAT-022", "MC2NVD9RTPW5", CandidateStatus.SELECTED),
    ("SEAT-022", "JS7BQM3PXWK1", CandidateStatus.SELECTED),
    ("SEAT-022", "SW8FHK4TQNX7", CandidateStatus.SELECTED),
    ("SEAT-022", "A5XCVSPCNN2O", CandidateStatus.PROPOSED),
]


def _application_from_row(row) -> SeatApplication:
    return SeatApplication(
        application_id=row["application_id"],
        seat_id=row["seat_id"],
        professional_id=row["professional_id"],
        status=CandidateStatus(row["status"]),
        applied_at=datetime.fromisoformat(row["applied_at"]),
        notes=row["notes"],
    )


def list_applications_for_seat(seat_id: str) -> list[SeatApplication]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *
            FROM seat_applications
            WHERE seat_id = ?
            ORDER BY applied_at ASC
            """,
            (seat_id,),
        ).fetchall()
    return [_application_from_row(row) for row in rows]


def list_applicants_for_seat(seat_id: str) -> list[SeatApplicantView]:
    applications = list_applications_for_seat(seat_id)
    applicants: list[SeatApplicantView] = []
    for application in applications:
        profile = get_profile(application.professional_id)
        if not profile:
            continue
        applicants.append(
            SeatApplicantView(
                application_id=application.application_id,
                seat_id=application.seat_id,
                professional_id=application.professional_id,
                name=profile.name,
                band=profile.band,
                location=profile.location,
                skills=list(profile.skills),
                status=application.status,
                applied_at=application.applied_at,
                cv_overview=profile.cv_overview,
            )
        )
    return applicants


def get_application(seat_id: str, professional_id: str) -> Optional[SeatApplication]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT *
            FROM seat_applications
            WHERE seat_id = ? AND professional_id = ?
            """,
            (seat_id, professional_id),
        ).fetchone()
    return _application_from_row(row) if row else None


def seed_applications() -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        for seat_id, professional_id, status in _SEED_APPLICATIONS:
            existing = conn.execute(
                """
                SELECT 1 FROM seat_applications
                WHERE seat_id = ? AND professional_id = ?
                """,
                (seat_id, professional_id),
            ).fetchone()
            if existing:
                continue
            conn.execute(
                """
                INSERT INTO seat_applications (
                    application_id,
                    seat_id,
                    professional_id,
                    status,
                    applied_at,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    f"APP-{uuid4().hex[:10].upper()}",
                    seat_id,
                    professional_id,
                    status.value,
                    now,
                    None,
                ),
            )
