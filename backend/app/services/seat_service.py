"""
Seat service — stub implementation with representative sample data.
Replace with real database queries when integrating with ProM's backend.
"""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from app.models.seat import Seat, SeatListResponse, SeatSearchParams, CandidateStatus, SeatType

_now = datetime.now(timezone.utc)

# ── Stub seat data ─────────────────────────────────────────────────────────────
_SEATS: list[Seat] = [
    Seat(
        seat_id="SEAT-001",
        title="Help Desk Analyst",
        client_name="US Citizenship & Immigration Services (USCIS)",
        owner_notes_id="Alyssa B Porter/Rocket Center/IBM",
        service="Application Operations",
        requested_band_high="7",
        requested_band_low="6",
        contract_owning_country="United States",
        work_location="Washington",
        work_remotely=True,
        sector="Public",
        industry="Government",
        last_updated=datetime(2025, 3, 10, tzinfo=timezone.utc),
        days_since_update=75,
        candidate_status=CandidateStatus.PROPOSED,
        profs_in_play=43,
        seat_type=SeatType.REAL,
        is_stale=True,
        mismatch_flag=False,
        ai_recommendation_note=None,
    ),
    Seat(
        seat_id="SEAT-002",
        title="Platform Engineer",
        client_name="US Citizenship & Immigration Services (USCIS)",
        owner_notes_id="Alyssa B Porter/Rocket Center/IBM",
        service="Application Operations",
        requested_band_high="7",
        requested_band_low="6G",
        contract_owning_country="United States",
        work_location="Remote",
        work_remotely=True,
        sector="Public",
        industry="Government",
        last_updated=datetime(2025, 4, 20, tzinfo=timezone.utc),
        days_since_update=34,
        candidate_status=CandidateStatus.SELECTED,
        profs_in_play=8,
        seat_type=SeatType.REAL,
        is_stale=False,
        mismatch_flag=True,
        ai_recommendation_note="Candidate already Selected — verify if this seat should be closed.",
    ),
    Seat(
        seat_id="SEAT-003",
        title="Cloud Solutions Architect",
        client_name="US Dept of Homeland Security",
        owner_notes_id="Karen Bean/Rocket Center/IBM",
        service="Cloud Services",
        requested_band_high="8",
        requested_band_low="7",
        contract_owning_country="United States",
        work_location="Herndon",
        work_remotely=False,
        sector="Public",
        industry="Defense",
        last_updated=datetime(2025, 5, 15, tzinfo=timezone.utc),
        days_since_update=10,
        candidate_status=None,
        profs_in_play=12,
        seat_type=SeatType.REAL,
        is_stale=False,
        mismatch_flag=False,
        ai_recommendation_note=None,
    ),
    Seat(
        seat_id="SEAT-004",
        title="Cybersecurity Analyst",
        client_name="US Dept of Defense Health Affairs",
        owner_notes_id="Alicia D Joiner/Rocket Center/IBM",
        service="Security Services",
        requested_band_high="7",
        requested_band_low="6",
        contract_owning_country="United States",
        work_location="Washington",
        work_remotely=True,
        sector="Public",
        industry="Defense",
        last_updated=datetime(2025, 2, 1, tzinfo=timezone.utc),
        days_since_update=110,
        candidate_status=CandidateStatus.NOT_SELECTED,
        profs_in_play=6,
        seat_type=SeatType.FORMAL,
        is_stale=True,
        mismatch_flag=False,
        ai_recommendation_note=None,
    ),
    Seat(
        seat_id="SEAT-005",
        title="Data Engineer",
        client_name="US Dept of the Army",
        owner_notes_id="Bridget Davidson/Sterling Forest/IBM",
        service="Data & Analytics",
        requested_band_high="7",
        requested_band_low="6",
        contract_owning_country="United States",
        work_location="Wallops Island",
        work_remotely=False,
        sector="Public",
        industry="Defense",
        last_updated=datetime(2025, 5, 28, tzinfo=timezone.utc),
        days_since_update=3,
        candidate_status=CandidateStatus.PROPOSED,
        profs_in_play=22,
        seat_type=SeatType.REAL,
        is_stale=False,
        mismatch_flag=False,
        ai_recommendation_note=None,
    ),
]


def search_seats(params: SeatSearchParams) -> SeatListResponse:
    results = list(_SEATS)

    if params.query:
        q = params.query.lower()
        results = [
            s for s in results
            if q in s.title.lower()
            or q in s.client_name.lower()
            or q in s.service.lower()
        ]
    if params.work_location:
        results = [s for s in results if params.work_location.lower() in s.work_location.lower()]
    if params.work_remotely is not None:
        results = [s for s in results if s.work_remotely == params.work_remotely]
    if params.sector:
        results = [s for s in results if params.sector.lower() in s.sector.lower()]
    if params.band:
        results = [s for s in results if s.requested_band_high == params.band or s.requested_band_low == params.band]
    if params.owner_notes_id:
        results = [s for s in results if params.owner_notes_id.lower() in s.owner_notes_id.lower()]

    total = len(results)
    start = (params.page - 1) * params.per_page
    end = start + params.per_page

    return SeatListResponse(
        total=total,
        page=params.page,
        per_page=params.per_page,
        seats=results[start:end],
    )


def get_seat_by_id(seat_id: str) -> Optional[Seat]:
    return next((s for s in _SEATS if s.seat_id == seat_id), None)
