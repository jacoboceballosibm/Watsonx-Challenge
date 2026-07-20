"""Unit tests for recommendation ranking helpers and edge cases."""
from __future__ import annotations

import pytest

from app.agents.recommendation_agent import (
    _heuristic_candidate_recs,
    _heuristic_owner_recs,
    _heuristic_seat_score,
    _openai_configured,
    run_recommendations,
)
from app.models.agent import RecommendationMode, RecommendationRequest
from app.models.application import SeatApplicantView
from app.models.profile import Profile
from app.models.seat import CandidateStatus, Seat, SeatType
from datetime import date, datetime, timezone


def test_openai_configured_false_when_missing(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert _openai_configured() is False
    monkeypatch.setenv("OPENAI_API_KEY", "your_openai_api_key_here")
    assert _openai_configured() is False
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert _openai_configured() is True


def test_heuristic_seat_score_prefers_skill_overlap():
    profile = Profile(
        professional_id="X",
        name="Test/US/IBM",
        availability_date=date(2026, 1, 1),
        skills=["React", "TypeScript", "Node.js"],
        band="7",
        location="Remote",
    )
    seat = Seat(
        seat_id="S1",
        title="Frontend Engineer",
        client_name="Acme",
        owner_notes_id="Owner/IBM",
        service="Application Development",
        requested_band_high="7",
        requested_band_low="6",
        contract_owning_country="United States",
        work_location="Remote",
        work_remotely=True,
        sector="Technology",
        industry="Software",
        last_updated=datetime.now(timezone.utc),
        days_since_update=1,
        seat_type=SeatType.REAL,
        is_available=True,
    )
    score_fe, aligned, _ = _heuristic_seat_score(profile.skills, profile, seat)
    assert score_fe >= 0.35
    assert aligned  # frontend/react style skills should contribute

    weak = Seat(
        **{
            **seat.model_dump(),
            "seat_id": "S2",
            "title": "Network Engineer",
            "service": "Networking",
            "sector": "Telecom",
            "industry": "Infrastructure",
        }
    )
    score_net, _, _ = _heuristic_seat_score(profile.skills, profile, weak)
    assert score_fe >= score_net


def test_heuristic_candidate_recs_sorted_and_limited():
    profile = Profile(
        professional_id="JS7BQM3PXWK1",
        name="John Smith/UK/IBM",
        availability_date=date(2026, 1, 1),
        skills=["JavaScript", "TypeScript", "React"],
        band="6",
        location="United Kingdom",
    )
    seats = [
        Seat(
            seat_id=f"S{i}",
            title=title,
            client_name="Client",
            owner_notes_id="Owner/IBM",
            service=service,
            requested_band_high="7",
            requested_band_low="6",
            contract_owning_country="US",
            work_location="Remote",
            work_remotely=True,
            sector="Technology",
            industry="Software",
            last_updated=datetime.now(timezone.utc),
            days_since_update=1,
            seat_type=SeatType.REAL,
            is_available=True,
        )
        for i, (title, service) in enumerate(
            [
                ("Frontend Engineer", "Web"),
                ("Data Science Lead", "Analytics"),
                ("React Developer", "Application Development"),
            ],
            start=1,
        )
    ]
    recs, reasoning = _heuristic_candidate_recs(profile, profile.skills, seats, limit=2)
    assert len(recs) == 2
    assert recs[0].match_score >= recs[1].match_score
    assert "John" in reasoning or "Ranked" in reasoning


def test_heuristic_owner_recs_only_given_applicants():
    seat = Seat(
        seat_id="SEAT-001",
        title="Senior Full-Stack Developer",
        client_name="TechCorp",
        owner_notes_id="Marcus Chen/Innovation Lab/IBM",
        service="Application Development",
        requested_band_high="8",
        requested_band_low="7",
        contract_owning_country="US",
        work_location="Remote",
        work_remotely=True,
        sector="Financial Services",
        industry="Banking",
        last_updated=datetime.now(timezone.utc),
        days_since_update=1,
        seat_type=SeatType.REAL,
        is_available=True,
    )
    applicants = [
        SeatApplicantView(
            application_id="A1",
            seat_id="SEAT-001",
            professional_id="JS7BQM3PXWK1",
            name="John Smith/UK/IBM",
            band="6",
            location="United Kingdom",
            skills=["JavaScript", "TypeScript", "React"],
            status=CandidateStatus.PROPOSED,
            applied_at=datetime.now(timezone.utc),
        ),
        SeatApplicantView(
            application_id="A2",
            seat_id="SEAT-001",
            professional_id="SW8FHK4TQNX7",
            name="Sarah Williams/CA/IBM",
            band="7",
            location="Canada",
            skills=["Data Science", "Machine Learning", "Python"],
            status=CandidateStatus.PROPOSED,
            applied_at=datetime.now(timezone.utc),
        ),
    ]
    recs, _ = _heuristic_owner_recs(seat, applicants, limit=10)
    ids = {r.professional_id for r in recs}
    assert ids == {"JS7BQM3PXWK1", "SW8FHK4TQNX7"}
    assert "A5XCVSPCNN2O" not in ids


@pytest.mark.asyncio
async def test_owner_mode_requires_seat_id(client):
    with pytest.raises(ValueError, match="seat_id is required"):
        await run_recommendations(
            RecommendationRequest(
                professional_id="MC2NVD9RTPW5",
                mode=RecommendationMode.OWNER,
            )
        )


@pytest.mark.asyncio
async def test_missing_profile_raises_lookup(client):
    with pytest.raises(LookupError, match="Professional profile not found"):
        await run_recommendations(
            RecommendationRequest(
                professional_id="DOES-NOT-EXIST",
                mode=RecommendationMode.CANDIDATE,
            )
        )
